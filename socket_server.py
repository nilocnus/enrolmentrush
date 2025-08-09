# socket_server.py  (full, updated version)

import socket
import threading
import json
import shutil
import os
import random
import atexit
import utils   # course list & points
import time

HOST, PORT         = '0.0.0.0', 11888
MAX_CLIENTS        = 4
COURSES_PER_ROUND  = 5
POINTS_TO_WIN      = 15
MAX_ROUNDS         = 6

game_courses = {}                   # local copy of cmpt_courses from utils, that can be modified

clients       = []                   # list of (conn, username)
clients_lock  = threading.Lock()

# ─── mutable game state (protected by game_lock) ────────────────────────────
game_lock      = threading.Lock()
round_no       = 0
round_courses  = []                   # list of 5 dicts for current round
seat_map       = {}                   # course_code -> seats left
scores         = {}                   # username -> accumulated points
player_picks   = set()                # usernames who have picked this round
winner         = None                 # first person to hit threshold
leading_player = None                 # if round cap is reached, winner is leading_player
# ───────────────────────────────────────────────────────────────────────────


def cleanup_pycache():
    """Remove __pycache__ directories on exit."""
    for root, dirs, _ in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                try:
                    shutil.rmtree(os.path.join(root, d))
                except:
                    pass


atexit.register(cleanup_pycache)


def broadcast(message):
    """Send a JSON message to all clients without holding the lock during send."""
    global clients

    data = (json.dumps(message) + '\n').encode()
    with clients_lock:
        targets = [conn for conn, _ in clients]

    dead_connections = []  # used to remove dead connections from clients list
    for sock in targets:
        try:
            sock.sendall(data)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
            print(f"[SERVER] Connection lost during broadcast: {e}")
            dead_connections.append(sock)
        except Exception as e:
            print(f"[SERVER] Unexpected error during broadcast: {e}")
            dead_connections.append(sock)

    if dead_connections:
        with clients_lock:
            clients = [(conn, username) for conn, username in clients if conn not in dead_connections]
        # If we pruned everyone and the game had started, shut down.
        maybe_shutdown_if_empty()

# ─── Clean shutdown support ─────────────────────────────────────────────────
server_socket = None
shutdown_event = threading.Event()

def shutdown_server():
    """Gracefully stop accepting and disconnect all clients."""
    global server_socket
    if shutdown_event.is_set():
        return
    shutdown_event.set()

    print("[SERVER] Shutting down…")

    # close all client sockets
    with clients_lock:
        targets = [conn for conn, _ in clients]
    for sock in targets:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
    with clients_lock:
        clients.clear()

    # close the listening socket (break accept loop)
    if server_socket:
        try:
            server_socket.close()
        except Exception:
            pass
        server_socket = None


def maybe_shutdown_if_empty():
    """If the game has started and all clients are gone, shut the server down."""
    with clients_lock:
        no_clients = (len(clients) == 0)
    with game_lock:
        started = (round_no > 0)

    if no_clients and started and not shutdown_event.is_set():
        print("[SERVER] All players disconnected. Shutting down server.")
        shutdown_server()
# ────────────────────────────────────────────────────────────────────────────


def update_lobby():
    """Notify all clients of current lobby membership and start game if full."""
    is_full = False
    with clients_lock:
        users = [u for _, u in clients]
        count = len(users)
        if count == MAX_CLIENTS and round_no == 0:
            is_full = True
    broadcast({
        "type": "lobby",
        "player_count": count,
        "users": users
    })

    # when lobby is now full, start the game after a delay (let clients render lobby)
    if is_full:
        threading.Timer(1.5, start_round).start()  # 1.5 seconds


def choose_round_courses():
    """Randomly pick COURSES_PER_ROUND courses and reset seat_map."""
    global round_courses, seat_map, game_courses

    # pool of courses only with nonzero seats
    pool = [(code, info) for code, info in game_courses.items() if info["available_seats"] > 0]

    picks = random.sample(pool, COURSES_PER_ROUND)
    round_courses = [
        {
            "code": code,
            "name": info["name"],
            "points": info["points"],
            "available_seats": info["available_seats"]
        }
        for code, info in picks
    ]
    seat_map = {c["code"]: c["available_seats"] for c in round_courses}


def start_round():
    """Increment round number, choose courses, broadcast round_start."""
    global round_no, game_courses
    with game_lock:
        # initialize the game's course list on round 1
        if round_no == 0:
            # deep copy to avoid modifying utils.cmpt_courses
            game_courses = {code: info.copy() for code, info in utils.cmpt_courses.items()}

        round_no += 1
        choose_round_courses()
        payload = {
            "type":    "round_start",
            "round":   round_no,
            "courses": round_courses
        }
    broadcast(payload)


def finish_round():
    """Broadcast round_over (with round number), clear picks, then start next round."""
    global round_no, winner, leading_player
    # snapshot which round is ending
    with game_lock:
        finished_round = round_no
        # take a snapshot of players and scores before clearing them
        final_round_players = list(player_picks)
        final_scores = scores.copy()

    # if there is a winner
    if winner:
        broadcast({
            "type":         "game_over",
            "winner":       winner,
            "final_scores": scores.copy()
        })
        # give clients a moment to render Game Over, then disconnect server
        threading.Timer(1.0, shutdown_server).start()
        return

    # if round cap reached, leading player wins
    elif finished_round >= MAX_ROUNDS:
        broadcast({
            "type":         "game_over",
            "winner":       leading_player,
            "final_scores": scores.copy()
        })
        threading.Timer(1.0, shutdown_server).start()
        return

    # tell everyone the round is over
    broadcast({
        "type":   "round_over",
        "round":  finished_round,
        "scores": final_scores,
        "users":  final_round_players
    })

    # print player scores on the server console
    print(f"\n[SERVER] Round {finished_round} completed. Current scores:")
    for username, pts in scores.items():
        print(f"- {username}: {pts} points")

    # clear per-round picks
    with game_lock:
        player_picks.clear()

    # brief delay to let clients process UI updates
    time.sleep(5)
    start_round()


def handle_selection(username, course_code):
    """Process a client's course pick."""
    global winner, leading_player
    with game_lock:
        seats = seat_map.get(course_code, 0)
        denied = seats <= 0

        # notify everyone of this pick attempt
        if denied:
            # broadcast denial immediately
            broadcast({
                "type":        "seat_update",
                "course_code": course_code,
                "seats_left":  0,
                "username":    username,
                "denied":      True
            })
            return

        # successfully allocate seat:
        # decrease count in temporary seat_map and persistent game_courses
        seat_map[course_code] -= 1
        game_courses[course_code]["available_seats"] -= 1

        # award points
        pts = next(c["points"] for c in round_courses if c["code"] == course_code)
        scores[username] = scores.get(username, 0) + pts
        player_picks.add(username)

        # broadcast with the updated seat count
        broadcast({
            "type": "seat_update",
            "course_code": course_code,
            "seats_left": seat_map[course_code],
            "username": username,
            "denied": False
        })

        everyone_done = (len(player_picks) == min(len(clients), MAX_CLIENTS))

        # broadcast waiting-lobby update
        broadcast({
            "type":         "round_wait",
            "round":        round_no,
            "player_count": len(player_picks),
            "current_players": len(clients),
            "users":        list(player_picks),
            "scores":       scores.copy()
        })

        # if someone reached the win threshold, they are the winner (highest score wins ties)
        if scores[username] >= POINTS_TO_WIN and ((winner is None) or scores[username] > scores[winner]):
            winner = username
        elif all(other_points < scores[username] for other_user, other_points in scores.items() if other_user != username):
            leading_player = username

    # finish the round and start next if all have picked
    if everyone_done:
        finish_round()


def handle_connection(conn, addr):
    """Main loop for each client connection."""
    try:
        # Step 1: Receive and sanitize username
        username = conn.recv(1024).decode().strip()
        username = ''.join(username.split())

        # Step 2: Check if username is already taken
        with clients_lock:
            existing_usernames = {u for _, u in clients}
            if username in existing_usernames:
                payload = { "type": "username_taken" }
                data = (json.dumps(payload) + '\n').encode()
                conn.sendall(data)
                conn.close()
                return

        # Step 3: Reject if game already started or lobby full
        with game_lock, clients_lock:
            lobby_full = (len(clients) >= MAX_CLIENTS)
            game_in_progress = (round_no > 0)

        if lobby_full or game_in_progress:
            try:
                notice = (json.dumps({
                    "type": "game_in_progress",
                    "reason": "No new connections accepted once the game has started."
                }) + '\n').encode()
                conn.sendall(notice)
            except Exception:
                pass
            conn.close()
            return

        print(f"{username} connected from {addr}")

    except Exception:
        conn.close()
        return

    # Step 4: Initialize score for new player
    with game_lock:
        scores.setdefault(username, 0)

    # Step 5: Add player to lobby
    with clients_lock:
        clients.append((conn, username))
    update_lobby()

    buffer = ""
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                raise ConnectionResetError
            buffer += data

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                    if not isinstance(msg, dict) or not msg.get("type"):
                        print(f"[SERVER] Invalid message from {username}: {line}")
                        continue

                    if msg.get("type") == "select_course":
                        course_code = msg.get("course_code")
                        if course_code:
                            handle_selection(username, msg["course_code"])
                        else:
                            print(f"[SERVER] Missing course_code from {username}")

                except json.JSONDecodeError as e:
                    print(f"[SERVER] Invalid JSON from {username}: {line} - {e}")
                    continue
    except Exception as e:
        print(f"[SERVER] {username} disconnected. {e}")
    finally:
        with clients_lock:
            clients[:] = [(c, u) for c, u in clients if c != conn]
        update_lobby()
        maybe_shutdown_if_empty()   # if everyone is gone mid-game, shut down
        try:
            conn.close()
        except Exception:
            pass


def main():
    global server_socket
    print(f"Server listening on port {PORT}…")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # helpful for quick restarts during development
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    try:
        while not shutdown_event.is_set():
            try:
                conn, addr = server_socket.accept()
            except OSError:
                # listener was closed during shutdown
                break
            threading.Thread(
                target=handle_connection,
                args=(conn, addr),
                daemon=True
            ).start()
    finally:
        # idempotent; safe even if already shut down
        shutdown_server()


if __name__ == "__main__":
    main()
