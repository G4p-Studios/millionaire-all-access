# network.py

import socket
import pickle # Used to serialize and deserialize Python objects

class Network:
    def __init__(self, server_ip, server_port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = server_port
        self.addr = (self.server, self.port)

    def connect(self):
        """
        Connects to the server and returns the initial data received (like player ID).
        """
        try:
            self.client.connect(self.addr)
            # The server will send back the new player object upon connecting
            return pickle.loads(self.client.recv(2048))
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None

    def send(self, data):
        """
        Sends data to the server and returns the server's response.
        """
        try:
            self.client.send(pickle.dumps(data))
            # The server is expected to reply with the updated game state
            return pickle.loads(self.client.recv(2048))
        except socket.error as e:
            print(f"Send/Receive Error: {e}")
            return None