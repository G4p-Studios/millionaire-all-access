# server.py

import socket
from _thread import *
import pickle
import struct
from player import Player
import sys
import threading
import urllib.request
import json
import time
from settings import LOBBY_SPY_URL as DEFAULT_SPY_URL

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
    "asset_manifest": [],
    "start_block_reason": ""
}

session_assets = {}
session_manifest = []

id_counter = 1
id_lock = threading.Lock()

def register_lobby():
    while True:
        if is_public:
            try:
                data = {
                    "name": lobby_name,
                    "host": host_name,
                    "port": server_port,
                    "players": len(game_state["players"]),
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

def threaded_client(conn):
    global id_counter, game_state, session_assets, session_manifest
    
    # --- HANDSHAKE: Receive Name ---
    try:
        player_name = recv_packet(conn)
        if not player_name:
            conn.close()
            return
    except Exception as e:
        print(f"Handshake error: {e}")
        conn.close()
        return

    # --- HANDSHAKE: Assign ID ---
    player_id = -1
    
    if player_name == host_name:
        print(f"Host '{player_name}' identified. Assigning ID 0.")
        player_id = 0
        with game_state_lock:
            # Remove any ghost hosts
            game_state["players"] = [p for p in game_state["players"] if p.id != 0]
    else:
        with id_lock:
            player_id = id_counter
            id_counter += 1
        print(f"Player '{player_name}' connected. Assigned ID {player_id}.")

    player_object = Player(player_id)
    player_object.name = player_name
    player_object.asset_ready = (player_id == 0 or len(session_manifest) == 0)
    
    with game_state_lock:
        game_state["players"].append(player_object)
        game_state["asset_manifest"] = session_manifest

    send_packet(conn, player_object)

    # Main Loop
    while True:
        try:
            command = recv_packet(conn)
            if command is None:
                break

            with game_state_lock:
                reply = game_state
                if command == "start" and player_id == 0:
                    non_hosts = [p for p in game_state["players"] if p.id != 0]
                    waiting = [p.name for p in non_hosts if not getattr(p, "asset_ready", False)]
                    if waiting:
                        game_state["start_block_reason"] = f"Waiting for asset sync: {', '.join(waiting)}"
                    else:
                        game_state["start_block_reason"] = ""
                        game_state["game_started"] = True
                elif isinstance(command, dict) and command.get("action") == "move_zone":
                    zone_name = command.get("zone")
                    for player in game_state["players"]:
                        if player.id == player_id:
                            player.zone = zone_name
                            break
                elif isinstance(command, dict) and command.get("action") == "set_seated":
                    seated = bool(command.get("seated", False))
                    for player in game_state["players"]:
                        if player.id == player_id:
                            player.seated = seated
                            break
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "move_target_hot_seat"
                    and player_id == 0
                ):
                    target_name = command.get("target_name", "")
                    for player in game_state["players"]:
                        if player.id != 0 and player.name == target_name:
                            player.zone = "Hot Seat"
                            player.seated = True
                            break
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "asset_upload_manifest"
                    and player_id == 0
                ):
                    session_manifest = command.get("manifest", [])
                    session_assets = {}
                    game_state["asset_manifest"] = session_manifest
                    game_state["start_block_reason"] = ""
                    for player in game_state["players"]:
                        player.asset_ready = (player.id == 0 or len(session_manifest) == 0)
                    reply = {"ok": True, "manifest_count": len(session_manifest)}
                elif (
                    isinstance(command, dict)
                    and command.get("action") == "asset_upload_file"
                    and player_id == 0
                ):
                    name = command.get("name", "")
                    data = command.get("data", b"")
                    if isinstance(name, str) and isinstance(data, (bytes, bytearray)):
                        session_assets[name] = bytes(data)
                        reply = {"ok": True, "name": name}
                    else:
                        reply = {"ok": False, "error": "invalid_file_payload"}
                elif isinstance(command, dict) and command.get("action") == "asset_get_manifest":
                    reply = {"type": "asset_manifest", "manifest": session_manifest}
                elif isinstance(command, dict) and command.get("action") == "asset_get_file":
                    name = command.get("name", "")
                    data = session_assets.get(name)
                    if data is None:
                        reply = {"type": "asset_file", "ok": False, "name": name}
                    else:
                        reply = {"type": "asset_file", "ok": True, "name": name, "data": data}
                elif isinstance(command, dict) and command.get("action") == "asset_client_ready":
                    is_ready = bool(command.get("ready", False))
                    for player in game_state["players"]:
                        if player.id == player_id:
                            player.asset_ready = is_ready
                            break
                    reply = {"ok": True, "ready": is_ready}
                elif command == "get":
                    reply = game_state
            
            send_packet(conn, reply)
        except (pickle.UnpicklingError, ConnectionResetError, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"Player {player_id} ({player_name}) disconnected.")
    with game_state_lock:
        game_state["players"] = [p for p in game_state["players"] if p.id != player_id]
        if player_id == 0:
            print("Host disconnected. Resetting state.")
            game_state["game_started"] = False
            game_state["asset_manifest"] = []
            game_state["start_block_reason"] = ""
            session_manifest = []
            session_assets = {}
    conn.close()

while True:
    conn, addr = s.accept()
    start_new_thread(threaded_client, (conn, ))