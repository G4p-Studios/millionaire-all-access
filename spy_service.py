# spy_service.py

from flask import Flask, request, jsonify
from waitress import serve # Import the production server
import time

app = Flask(__name__)

# Store lobbies in memory: { "unique_id": { lobby_data } }
lobbies = {}

# Time in seconds before a lobby is considered dead
TIMEOUT_SECONDS = 40 

@app.route('/')
def home():
    return "Lobby Spy Service is Running on Port 1945."

@app.route('/lobbies', methods=['POST'])
def register_lobby():
    """
    Game servers call this every ~30 seconds to say "I'm here".
    Expected JSON: {"name": "...", "host": "...", "port": 50550, ...}
    """
    try:
        data = request.json
        if not data or 'port' not in data:
            return "Invalid Data", 400

        # We determine the IP from the request itself
        client_ip = request.remote_addr
        
        # Create a unique key for this lobby
        lobby_key = f"{client_ip}:{data['port']}"

        # Add the IP and a timestamp to the data
        data['ip'] = client_ip
        data['last_seen'] = time.time()

        # Update the store
        lobbies[lobby_key] = data
        
        print(f"Heartbeat from {data['name']} ({lobby_key})")
        return "Registered", 200
    except Exception as e:
        print(f"Error: {e}")
        return "Error", 500

@app.route('/lobbies', methods=['GET'])
def get_lobbies():
    """
    Game clients call this to get the list of playable lobbies.
    This also cleans up dead lobbies.
    """
    current_time = time.time()
    active_lobbies = []
    dead_lobbies = []

    # Filter lobbies
    for key, lobby in lobbies.items():
        if current_time - lobby['last_seen'] < TIMEOUT_SECONDS:
            # This lobby is active
            clean_lobby = lobby.copy()
            del clean_lobby['last_seen']
            active_lobbies.append(clean_lobby)
        else:
            # This lobby has timed out
            dead_lobbies.append(key)

    # Remove dead lobbies from memory
    for key in dead_lobbies:
        print(f"Pruning inactive lobby: {key}")
        del lobbies[key]

    return jsonify(active_lobbies)

if __name__ == '__main__':
    print("Starting Production Lobby Spy Service on port 1945...")
    # 'threads=4' allows multiple game clients to connect simultaneously
    # without blocking each other.
    serve(app, host='0.0.0.0', port=1945, threads=4)