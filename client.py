# ===== Third-party libraries (need pip install) =====
# pip install watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ===== Python standard library (NO pip install needed) =====
from fileinput import filename
from xmlrpc import client
import time
import socket
import json
import os
import threading
from pathlib import Path
import base64

def connect_to_server():
    host = "AlexanderPI.local"
    port = 5000
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    return client


edited_files = []
def get_user_input():
    while True:
        user_input = input("Enter something: ")
        print(f"You typed: {user_input}")
        if user_input.lower() == "save":
            print("Edited files to save:", edited_files)

            client = connect_to_server()
            for file_path in edited_files:

                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                file_b64 = base64.b64encode(file_bytes).decode()
                data_to_send = {"action": "edit", "subaction": None, "path": file_path, "filedata": file_b64}

                client.sendall(json.dumps(data_to_send).encode())

            client.close()
                
            edited_files.clear()

input_thread = threading.Thread(target=get_user_input, daemon=True)
input_thread.start()

class Handler(FileSystemEventHandler):
    action = None
    subaction = None
    path = None
    def on_created(self, event):
        global action, subaction, path
        if event.is_directory:
            print(f"Folder created: {Path(event.src_path).as_posix()}")
            subaction = "folder_created"
        else:
            print(f"New file created: {Path(event.src_path).as_posix()}")
            subaction = "file_created"

        path = Path(event.src_path).as_posix()
        action = "create"
        self.send_update()

    def on_deleted(self, event):
        global action, subaction, path
        if event.is_directory:
            print(f"Folder deleted: {Path(event.src_path).as_posix()}")
            subaction = "folder_deleted"
        else:
            print(f"File deleted: {Path(event.src_path).as_posix()}")
            subaction = "file_deleted"

        path = Path(event.src_path).as_posix()
        action = "delete"
        self.send_update()

    def send_update(self):
        global action, subaction, path
        client = connect_to_server()
        data_to_send = {"action": action,"subaction": subaction, "path": path}
        client.sendall(json.dumps(data_to_send).encode())
        client.close()

    def on_modified(self, event):
        global edited_files
        path = Path(event.src_path).as_posix()
        if not event.is_directory:
            print(f"{path} was modified!")
            if path not in edited_files:
                edited_files.append(path)
                print("Edited files:", edited_files)

path_to_watch = "projects"

observer = Observer()
observer.schedule(Handler(), path_to_watch, recursive=True)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()
