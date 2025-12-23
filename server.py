# server.py

import socket
from _thread import *
import pickle
from player import Player
import sys
import threading

try:
    server_port = int(sys.argv[1])
except (IndexError, ValueError):
    server_port = 50505

# Server Configuration
server_ip = "" 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server_ip, server_port))
except socket.error as e:
    print(str(e))
    exit()

s.listen(4)
print(f"Server Started on port {server_port}. Waiting for a connection...")

# --- NEW: Shared Game State and Lock ---
# We use a lock to prevent race conditions when multiple threads access the game state.
game_state_lock = threading.Lock()
game_state = {
    "players": [],
    "game_started": False
}

def threaded_client(conn, player_id):
    """
    This function runs in a separate thread for each connected client.
    """
    global game_state
    
    # Create player and add to shared state safely
    with game_state_lock:
        player_object = Player(player_id)
        game_state["players"].append(player_object)
    
    # Send the brand new player object to the client so they know their ID
    conn.send(pickle.dumps(player_object))
    
    print(f"Player {player_id} connected.")

    while True:
        try:
            # Receive a command from the client
            command = pickle.loads(conn.recv(2048))
            if not command:
                break

            with game_state_lock:
                if command == "start" and player_id == 0: # Only host can start
                    game_state["game_started"] = True
                
                # Always reply with the current game state
                reply = game_state
            
            conn.sendall(pickle.dumps(reply))

        except (pickle.UnpicklingError, ConnectionResetError, EOFError) as e:
            # These errors indicate a client disconnected abruptly
            break

    # --- Client Disconnected ---
    print(f"Player {player_id} disconnected.")
    with game_state_lock:
        # Find and remove the disconnected player
        game_state["players"] = [p for p in game_state["players"] if p.id != player_id]
        
        # If the host disconnects, reset the game state for everyone
        if player_id == 0:
            print("Host disconnected. Resetting server state.")
            game_state["game_started"] = False
            # In a real game, you might disconnect all other clients here.
    
    conn.close()


# Main Server Loop
currentPlayerId = 0
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)
    start_new_thread(threaded_client, (conn, currentPlayerId))
    currentPlayerId += 1