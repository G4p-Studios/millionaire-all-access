# server.py

import socket
from _thread import *
import pickle
import struct
import hashlib
from player import Player
import sys
import threading
import urllib.request
import json
import time
import uuid
from settings import (
    LOBBY_SPY_URL as DEFAULT_SPY_URL,
    SESSION_SYNC_CHUNK_SIZE,
    SESSION_SYNC_MAX_FILE_SIZE,
    DISCONNECT_GRACE_SECONDS,
)

# Default Configuration
server_port = 50550
lobby_name = "My Lobby"
host_name = "Host" 
is_public = False
spy_url = DEFAULT_SPY_URL

# Parse Command Line Arguments
# Expected: script.py [port] [lobby_name] [host_name] [public] [spy_url]
if len(sys.argv) > 1:
    try: server_port = int(sys.argv[1])
    except ValueError: pass
if len(sys.argv) > 2: lobby_name = sys.argv[2]
if len(sys.argv) > 3: host_name = sys.argv[3]
if len(sys.argv) > 4: is_public = (sys.argv[4] == "1" or sys.argv[4].lower() == "true")
if len(sys.argv) > 5: spy_url = sys.argv[5]

print(f"Server Config: Port={server_port}, Name='{lobby_name}', Host='{host_name}', Public={is_public}, SpyURL='{spy_url}'")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("", server_port))
except socket.error as e:
    print(f"Bind Error: {e}")
    exit()

s.listen(4)
print("Waiting for connections...")

# Game State
game_state_lock = threading.Lock()
game_state = {
    "players": [],
    "game_started": False,
    "lobby_name": lobby_name,
    "host_name": host_name,
    "host_player_id": 0,
    "host_handoff_notice": "",
    "asset_manifest": [],
    "asset_revision": 0,
    "start_block_reason": ""
}

session_assets = {}
session_manifest = []
session_uploads = {}
session_tokens = {}
id_to_token = {}

id_counter = 1
id_lock = threading.Lock()


def _connected_players_locked():
    return [p for p in game_state["players"] if getattr(p, "connected", True)]


def _find_player_by_id_locked(player_id):
    for p in game_state["players"]:
        if p.id == player_id:
            return p
    return None


def _elect_host_locked(notice=""):
    connected = _connected_players_locked()
    if not connected:
        game_state["host_player_id"] = -1
        game_state["host_handoff_notice"] = notice or "No active host connected."
        return -1

    preferred = [p for p in connected if p.id == 0]
    host_player = preferred[0] if preferred else min(connected, key=lambda p: p.id)

    game_state["host_player_id"] = host_player.id
    game_state["host_name"] = host_player.name
    if notice:
        game_state["host_handoff_notice"] = notice
    return host_player.id


def _prune_disconnected_locked():
    now = time.time()
    keep = []
    removed_ids = []
    for p in game_state["players"]:
        if getattr(p, "connected", True):
            keep.append(p)
            continue

        disconnected_at = float(getattr(p, "disconnected_at", now))
        if now - disconnected_at <= DISCONNECT_GRACE_SECONDS:
            keep.append(p)
        else:
            removed_ids.append(p.id)

    if removed_ids:
        game_state["players"] = keep
        for pid in removed_ids:
            token = id_to_token.pop(pid, None)
            if token:
                session_tokens.pop(token, None)

        if game_state.get("host_player_id") in removed_ids:
            _elect_host_locked("Host timed out. Control handed off.")

        if not _connected_players_locked():
            game_state["game_started"] = False
            game_state["start_block_reason"] = ""

def register_lobby():
    while True:
        if is_public:
            try:
                with game_state_lock:
                    connected_count = len(_connected_players_locked())
                    current_host_name = game_state.get("host_name", host_name)
                data = {
                    "name": lobby_name,
                    "host": current_host_name,
                    "port": server_port,
                    "players": connected_count,
                    "max_players": 4
                }
                json_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(spy_url, data=json_data, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response: pass 
            except Exception as e: print(f"Lobby Spy Error: {e}")
        time.sleep(30)

if is_public: start_new_thread(register_lobby, ())

def send_packet(conn, obj):
    payload = pickle.dumps(obj)
    header = struct.pack("!I", len(payload))
    conn.sendall(header + payload)

def recv_exact(conn, size):
    chunks = []
    received = 0
    while received < size:
        chunk = conn.recv(size - received)
        if not chunk:
            return None
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)

def recv_packet(conn):
    header = recv_exact(conn, 4)
    if not header:
        return None
    payload_len = struct.unpack("!I", header)[0]
    payload = recv_exact(conn, payload_len)
    if payload is None:
        return None
    return pickle.loads(payload)


def cleanup_loop():
    while True:
        with game_state_lock:
            _prune_disconnected_locked()
        time.sleep(2)


start_new_thread(cleanup_loop, ())


def threaded_client(conn):
    global id_counter, game_state, session_assets, session_manifest, session_uploads, session_tokens, id_to_token

    # --- HANDSHAKE: Receive identity payload ---
    try:
        hello = recv_packet(conn)
        if not hello:
            conn.close()
            return
    except Exception as e:
        print(f"Handshake error: {e}")
        conn.close()
        return

    if isinstance(hello, dict):
        player_name = str(hello.get("name", "")).strip()
        reconnect_token = str(hello.get("session_token", "")).strip()
    else:
        player_name = str(hello).strip()
        reconnect_token = ""

    if not player_name:
        conn.close()
        return

    player_id = -1
    player_object = None
    reconnected = False

    with game_state_lock:
        _prune_disconnected_locked()

        if reconnect_token and reconnect_token in session_tokens:
            session = session_tokens[reconnect_token]
            player_object = session["player"]
            player_id = int(session["id"])
            reconnected = True
            if player_name:
                player_object.name = player_name
        else:
            reconnect_token = str(uuid.uuid4())

            if player_name == host_name and 0 not in id_to_token:
                player_id = 0
                print(f"Host '{player_name}' connected as primary host ID 0.")
            else:
                with id_lock:
                    while id_counter in id_to_token:
                        id_counter += 1
                    player_id = id_counter
                    id_counter += 1
                print(f"Player '{player_name}' connected. Assigned ID {player_id}.")

            player_object = Player(player_id)
            player_object.name = player_name
            session_tokens[reconnect_token] = {"id": player_id, "player": player_object}
            id_to_token[player_id] = reconnect_token
            game_state["players"].append(player_object)

        if player_object not in game_state["players"]:
            game_state["players"].append(player_object)

        player_object.connected = True
        player_object.disconnected_at = 0.0
        if not hasattr(player_object, "zone"):
            player_object.zone = "Contestant Area"
        if not hasattr(player_object, "seated"):
            player_object.seated = False
        if not hasattr(player_object, "asset_ready"):
            player_object.asset_ready = (player_id == 0 or len(session_manifest) == 0)

        game_state["asset_manifest"] = session_manifest
        _elect_host_locked("Host reconnected." if reconnected and player_id == 0 else "")

        # Attach reconnect metadata so older clients still receive a Player object.
        player_object.session_token = reconnect_token
        player_object.reconnected = reconnected
        player_object.host_player_id = game_state.get("host_player_id", 0)

    send_packet(conn, player_object)

    # Main Loop
    while True:
        try:
            command = recv_packet(conn)
            if command is None:
                break

            with game_state_lock:
                _prune_disconnected_locked()
                reply = game_state
                current_host_id = int(game_state.get("host_player_id", -1))
                is_host_actor = (player_id == current_host_id)

                if command == "start" and is_host_actor:
                    non_hosts = [
                        p for p in game_state["players"]
                        if p.id != current_host_id and getattr(p, "connected", True)
                    ]
                    waiting = [p.name for p in non_hosts if not getattr(p, "asset_ready", False)]
                    if waiting:
                        game_state["start_block_reason"] = f"Waiting for asset sync: {', '.join(waiting)}"
                    else:
                        game_state["start_block_reason"] = ""
                        game_state["game_started"] = True
                elif isinstance(command, dict) and command.get("action") == "move_zone":
                    zone_name = command.get("zone")
                    player = _find_player_by_id_locked(player_id)
                    if player:
                        player.zone = zone_name
                elif isinstance(command, dict) and command.get("action") == "set_seated":
                    seated = bool(command.get("seated", False))
                    player = _find_player_by_id_locked(player_id)
                    if player:
                        player.seated = seated
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "move_target_hot_seat"
                    and is_host_actor
                ):
                    target_name = command.get("target_name", "")
                    for player in game_state["players"]:
                        if (
                            player.id != current_host_id
                            and getattr(player, "connected", True)
                            and player.name == target_name
                        ):
                            player.zone = "Hot Seat"
                            player.seated = True
                            break
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "asset_upload_manifest"
                    and is_host_actor
                ):
                    session_manifest = command.get("manifest", [])
                    session_assets = {}
                    session_uploads = {}
                    game_state["asset_manifest"] = session_manifest
                    game_state["asset_revision"] += 1
                    game_state["start_block_reason"] = ""
                    for player in game_state["players"]:
                        player.asset_ready = (player.id == 0 or len(session_manifest) == 0)
                    reply = {
                        "ok": True,
                        "manifest_count": len(session_manifest),
                        "asset_revision": game_state["asset_revision"],
                    }
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "asset_upload_begin"
                    and is_host_actor
                ):
                    name = command.get("name", "")
                    size = command.get("size", -1)
                    sha256 = command.get("sha256", "")
                    if isinstance(name, str) and isinstance(size, int) and size >= 0 and isinstance(sha256, str):
                        if size > SESSION_SYNC_MAX_FILE_SIZE:
                            reply = {"ok": False, "error": "file_too_large", "name": name}
                            continue
                        existing = session_uploads.get(name)
                        if (
                            existing
                            and existing.get("size") == size
                            and existing.get("sha256") == sha256
                        ):
                            offset = len(existing.get("data", bytearray()))
                        else:
                            session_uploads[name] = {
                                "size": size,
                                "sha256": sha256,
                                "data": bytearray(),
                            }
                            offset = 0
                        reply = {"ok": True, "name": name, "offset": offset}
                    else:
                        reply = {"ok": False, "error": "invalid_upload_begin"}
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "asset_upload_chunk"
                    and is_host_actor
                ):
                    name = command.get("name", "")
                    offset = command.get("offset", -1)
                    data = command.get("data", b"")
                    upload = session_uploads.get(name)
                    if not upload:
                        reply = {"ok": False, "error": "no_upload_session", "name": name}
                    elif not isinstance(offset, int):
                        reply = {"ok": False, "error": "invalid_offset", "name": name}
                    elif not isinstance(data, (bytes, bytearray)):
                        reply = {"ok": False, "error": "invalid_chunk_payload", "name": name}
                    else:
                        expected = len(upload["data"])
                        if offset != expected:
                            reply = {
                                "ok": False,
                                "error": "offset_mismatch",
                                "name": name,
                                "expected_offset": expected,
                            }
                        else:
                            upload["data"].extend(bytes(data))
                            if len(upload["data"]) > upload["size"]:
                                session_uploads.pop(name, None)
                                reply = {"ok": False, "error": "upload_too_large", "name": name}
                            elif len(upload["data"]) == upload["size"]:
                                digest = hashlib.sha256(upload["data"]).hexdigest()
                                if upload["sha256"] and digest != upload["sha256"]:
                                    session_uploads.pop(name, None)
                                    reply = {"ok": False, "error": "hash_mismatch", "name": name}
                                else:
                                    session_assets[name] = bytes(upload["data"])
                                    session_uploads.pop(name, None)
                                    reply = {
                                        "ok": True,
                                        "name": name,
                                        "next_offset": len(session_assets[name]),
                                        "complete": True,
                                    }
                            else:
                                reply = {
                                    "ok": True,
                                    "name": name,
                                    "next_offset": len(upload["data"]),
                                    "complete": False,
                                }
                elif isinstance(command, dict) and command.get("action") == "asset_get_manifest":
                    reply = {
                        "type": "asset_manifest",
                        "manifest": session_manifest,
                        "revision": game_state.get("asset_revision", 0),
                        "chunk_size": SESSION_SYNC_CHUNK_SIZE,
                    }
                elif isinstance(command, dict) and command.get("action") == "asset_get_file_chunk":
                    name = command.get("name", "")
                    offset = command.get("offset", -1)
                    length = command.get("length", 65536)
                    data = session_assets.get(name)
                    if data is None:
                        reply = {"type": "asset_file_chunk", "ok": False, "name": name, "error": "not_found"}
                    elif not isinstance(offset, int) or offset < 0 or offset > len(data):
                        reply = {
                            "type": "asset_file_chunk",
                            "ok": False,
                            "name": name,
                            "error": "offset_mismatch",
                            "expected_offset": len(data) if isinstance(offset, int) and offset > len(data) else 0,
                        }
                    else:
                        if not isinstance(length, int) or length <= 0:
                            length = SESSION_SYNC_CHUNK_SIZE
                        length = min(length, SESSION_SYNC_CHUNK_SIZE)
                        chunk = data[offset:offset + length]
                        next_offset = offset + len(chunk)
                        reply = {
                            "type": "asset_file_chunk",
                            "ok": True,
                            "name": name,
                            "offset": offset,
                            "next_offset": next_offset,
                            "eof": next_offset >= len(data),
                            "data": chunk,
                        }
                elif isinstance(command, dict) and command.get("action") == "asset_client_ready":
                    is_ready = bool(command.get("ready", False))
                    revision = int(command.get("revision", -1))
                    player = _find_player_by_id_locked(player_id)
                    if player:
                        player.asset_ready = is_ready and revision == game_state.get("asset_revision", 0)
                    reply = {
                        "ok": True,
                        "ready": is_ready,
                        "accepted": revision == game_state.get("asset_revision", 0),
                        "asset_revision": game_state.get("asset_revision", 0),
                    }
                elif command == "get":
                    game_state["server_time"] = time.time()
                    reply = game_state
            
            send_packet(conn, reply)
        except (pickle.UnpicklingError, ConnectionResetError, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"Player {player_id} ({player_name}) disconnected.")
    with game_state_lock:
        player = _find_player_by_id_locked(player_id)
        if player:
            player.connected = False
            player.disconnected_at = time.time()

        if game_state.get("host_player_id", -1) == player_id:
            _elect_host_locked("Host disconnected. Control handed off.")

        _prune_disconnected_locked()
    conn.close()

while True:
    conn, addr = s.accept()
    start_new_thread(threaded_client, (conn, ))