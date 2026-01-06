import socket
import json
import base64
from pathlib import Path
import shutil

def edit(path, filedata):
    file_bytes = base64.b64decode(filedata)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_bytes)

def create_and_delete(file_path, action, subaction):
    if action == "create":
        if subaction == "file_created":
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).touch()
        elif subaction == "folder_created":
            Path(file_path).mkdir(parents=True, exist_ok=True)

    elif action == "delete":
        if subaction == "file_deleted":
            Path(file_path).unlink(missing_ok=True)
        elif subaction == "folder_deleted":
            shutil.rmtree(file_path, ignore_errors=True)

def recv_json(sock):
    try:
        header = sock.recv(4)
        if not header:
            return None

        msg_len = int.from_bytes(header, "big")

        data = b""
        while len(data) < msg_len:
            chunk = sock.recv(4096)
            if not chunk:
                return None
            data += chunk

        return json.loads(data.decode())

    except Exception as e:
        print("Receive error:", e)
        return None

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print("Server running forever (Ctrl+C to stop)")

while True:  # ← SERVER NEVER STOPS
    conn, addr = server.accept()
    print("Client connected:", addr)

    while True:  # ← CONNECTION NEVER STOPS
        msg = recv_json(conn)
        if msg is None:
            print("Client disconnected:", addr)
            conn.close()
            break

        print("Received:", msg)

        action = msg.get("action")
        subaction = msg.get("subaction")
        path = msg.get("path")

        if action in ["create", "delete"]:
            create_and_delete(path, action, subaction)
        elif action == "edit":
            edit(path, msg.get("filedata"))

        conn.sendall(b"OK")