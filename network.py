# network.py

import socket
import pickle
import struct

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
            
            self._send_packet(player_name)
            return self._recv_packet()
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None

    def send(self, data):
        try:
            self._send_packet(data)
            return self._recv_packet()
        except socket.error as e:
            print(f"Send/Receive Error: {e}")
            return None

    def _send_packet(self, obj):
        payload = pickle.dumps(obj)
        header = struct.pack("!I", len(payload))
        self.client.sendall(header + payload)

    def _recv_packet(self):
        header = self._recv_exact(4)
        if not header:
            return None
        payload_len = struct.unpack("!I", header)[0]
        payload = self._recv_exact(payload_len)
        if payload is None:
            return None
        return pickle.loads(payload)

    def _recv_exact(self, size):
        chunks = []
        received = 0
        while received < size:
            chunk = self.client.recv(size - received)
            if not chunk:
                return None
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)