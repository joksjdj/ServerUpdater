import difflib
import socket
import json
import base64
from pathlib import Path
import shutil

def edit(path, filedata):
    file_bytes = base64.b64decode(filedata)
    with open(path, "wb") as f:
        f.write(file_bytes)

def create_and_delete(file_path, action, subaction):
    if action == "create":
        if subaction == "file_created":
            Path(file_path).touch()
        elif subaction == "folder_created":
            Path(file_path).mkdir(parents=True, exist_ok=True)
    elif action == "delete":
        if subaction == "file_deleted":
            Path(file_path).unlink(missing_ok=True)
        elif subaction == "folder_deleted":
            shutil.rmtree(file_path, ignore_errors=True)

def recv_json(sock):
    header = sock.recv(4)
    if not header:
        return None

    msg_len = int.from_bytes(header, "big")

    data = b""
    while len(data) < msg_len:
        packet = sock.recv(4096)
        if not packet:
            return None
        data += packet

    return json.loads(data.decode())

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Waiting for connection...")
conn, addr = server.accept()
print("Connected by", addr)

while True:
    received_array = recv_json(conn)
    if received_array is None:
        break

    print("Received:", received_array)

    action = received_array.get("action")
    subaction = received_array.get("subaction")
    path = received_array.get("path")

    if action in ["create", "delete"]:
        create_and_delete(path, action, subaction)
    elif action == "edit":
        edit(path, received_array.get("filedata"))

    conn.sendall(b"OK")
