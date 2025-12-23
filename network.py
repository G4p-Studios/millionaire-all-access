# network.py

import socket
import pickle

class Network:
    def __init__(self, server_ip, server_port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = server_port
        self.addr = (self.server, self.port)

    def connect(self, player_name):
        """
        Connects to the server, sends the player name, 
        and receives the assigned Player object (with ID).
        """
        try:
            self.client.settimeout(5.0)
            self.client.connect(self.addr)
            
            # --- HANDSHAKE ---
            # Send the player name immediately
            self.client.send(pickle.dumps(player_name))
            
            # Receive the assigned Player object
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(f"Send/Receive Error: {e}")
            return None