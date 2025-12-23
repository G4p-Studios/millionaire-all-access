# server.py

import socket
from _thread import *
import pickle
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
    "host_name": host_name
}

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

def threaded_client(conn):
    global id_counter, game_state
    
    # --- HANDSHAKE: Receive Name ---
    try:
        name_data = conn.recv(4096)
        if not name_data:
            conn.close()
            return
        player_name = pickle.loads(name_data)
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
    
    with game_state_lock:
        game_state["players"].append(player_object)

    conn.send(pickle.dumps(player_object))

    # Main Loop
    while True:
        try:
            data = conn.recv(2048)
            if not data: break
            command = pickle.loads(data)

            with game_state_lock:
                if command == "start" and player_id == 0:
                    game_state["game_started"] = True
                reply = game_state
            
            conn.sendall(pickle.dumps(reply))
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
    conn.close()

while True:
    conn, addr = s.accept()
    start_new_thread(threaded_client, (conn, ))