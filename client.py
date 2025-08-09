# client.py

import socket
import threading
import json
import queue

MAX_CLIENTS = 4


class ClientConnection:
    def __init__(
        self,
        username,
        username_fail_callback=None,
        lobby_update_callback=None,
        lobby_fail_callback=None,
        lobby_success_callback=None,
        round_update_callback=None,
        seat_update_callback=None,
        game_over_callback=None,
        server_host='127.0.0.1',        # testing
        #server_host='165.227.45.38',  # final demo
        server_port=11888
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.username_fail_callback = username_fail_callback
        self.lobby_update_callback = lobby_update_callback
        self.lobby_fail_callback = lobby_fail_callback
        self.lobby_success_callback = lobby_success_callback

        self.round_update_callback = round_update_callback
        self.seat_update_callback = seat_update_callback
        self.game_over_callback = game_over_callback

        self.sock = None
        self.out_q = queue.Queue()
        self.running = True

        # start networking thread
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    # public helper to send any JSON message to the server
    def send(self, data):
        try:
            if self.sock:
                self.sock.sendall((json.dumps(data) + '\n').encode())
        except Exception as e:
            print(f"[Client] send() failed: {e}")

    def connect_to_server(self):
        try:
            # create and connect socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_host, self.server_port))

            # send username with newline
            self.sock.sendall((self.username + '\n').encode())

            buffer = ""
            while self.running:
                payload = self.sock.recv(1024).decode()
                if not payload:
                    break  # connection closed by server
                buffer += payload

                # process newline-delimited JSON messages
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)

                    if not line:
                        continue

                    message = json.loads(line)
                    msg_type = message.get("type")

                    # route by message type
                    if msg_type == "username_taken":
                        if self.username_fail_callback:
                            self.username_fail_callback()
                            return

                    elif msg_type == "game_in_progress":
                        # server refuses late joiners / full room
                        reason = message.get(
                            "reason", "Game already in progress or room is full."
                        )
                        if self.lobby_fail_callback:
                            self.lobby_fail_callback(reason)
                        self.running = False
                        try:
                            if self.sock:
                                self.sock.shutdown(socket.SHUT_RDWR)
                                self.sock.close()
                        except Exception:
                            pass
                        return

                    elif msg_type == "lobby":
                        if self.lobby_update_callback:
                            self.lobby_update_callback(
                                message["player_count"],
                                message["users"]
                            )
                            if self.lobby_success_callback:
                                self.lobby_success_callback(True)
                                self.lobby_success_callback = None

                    elif msg_type == "round_start":
                        if self.round_update_callback:
                            self.round_update_callback(message)

                    elif msg_type == "seat_update":
                        if self.seat_update_callback:
                            seat_denied = message.get("denied")
                            if seat_denied is True:
                                self.seat_update_callback({
                                    **message,
                                    "denied": True
                                })
                            else:
                                self.seat_update_callback({
                                    **message,
                                    "denied": False
                                })

                    elif msg_type == "round_wait":
                        if self.round_update_callback:
                            self.round_update_callback(message)

                    elif msg_type == "round_over":
                        if self.round_update_callback:
                            self.round_update_callback(message)

                    elif msg_type == "game_over":
                        if self.game_over_callback:
                            print("[Client] got game_over:", message)
                            self.game_over_callback(message)
                        # stop listening so no late messages can overwrite the Game Over screen
                        self.running = False
                        try:
                            if self.sock:
                                self.sock.shutdown(socket.SHUT_RDWR)
                                self.sock.close()
                        except Exception:
                            pass
                        return

        except Exception as e:
            print(f"Error connecting to server: {e}")
            if self.lobby_fail_callback:
                self.lobby_fail_callback(str(e))
        finally:
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass

    def disconnect(self):
        try:
            self.running = False  # stops recursive loops from happening
            if self.sock:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
        except Exception as e:
            print(f"[Client] Error during disconnect: {e}")