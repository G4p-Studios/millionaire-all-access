# network.py

import socket
import pickle
import struct


class Network:
    def __init__(self, server_ip, server_port):
        self.server = server_ip
        self.port = server_port
        self.addr = (self.server, self.port)
        self.client = None
        self.player_name = ""
        self.player_id = -1
        self.session_token = None

    def _new_socket(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        return client

    def connect(self, player_name):
        """
        Connects to the server, sends the player name, 
        and receives the assigned Player object (with ID).
        """
        self.player_name = player_name
        try:
            self.client = self._new_socket()
            self.client.connect(self.addr)

            hello = {
                "name": self.player_name,
                "session_token": self.session_token,
                "requested_id": self.player_id,
            }
            self._send_packet(hello)
            player_data = self._recv_packet()
            self._apply_handshake(player_data)
            return player_data
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None

    def send(self, data):
        try:
            self._send_packet(data)
            return self._recv_packet()
        except (socket.error, OSError) as e:
            print(f"Send/Receive Error: {e}")

        if not self._reconnect():
            return None

        try:
            self._send_packet(data)
            return self._recv_packet()
        except (socket.error, OSError) as e:
            print(f"Send failed after reconnect: {e}")
            return None

    def _apply_handshake(self, player_data):
        if player_data is None:
            return

        if isinstance(player_data, dict):
            self.player_id = int(player_data.get("id", self.player_id))
            token = player_data.get("session_token")
            if isinstance(token, str) and token:
                self.session_token = token
            return

        if hasattr(player_data, "id"):
            self.player_id = int(getattr(player_data, "id", self.player_id))

        token = getattr(player_data, "session_token", None)
        if isinstance(token, str) and token:
            self.session_token = token

    def _reconnect(self):
        if not self.player_name:
            return False

        try:
            if self.client:
                try:
                    self.client.close()
                except Exception:
                    pass

            self.client = self._new_socket()
            self.client.connect(self.addr)

            hello = {
                "name": self.player_name,
                "session_token": self.session_token,
                "requested_id": self.player_id,
            }
            self._send_packet(hello)
            player_data = self._recv_packet()
            if player_data is None:
                return False

            self._apply_handshake(player_data)
            return True
        except (socket.error, OSError) as e:
            print(f"Reconnect failed: {e}")
            return False

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
            try:
                chunk = self.client.recv(size - received)
            except socket.timeout:
                return None
            if not chunk:
                return None
            chunks.append(chunk)
            received += len(chunk)
        return b"".join(chunks)