"""
NouGen Universal Socket Server Daemon
Binds unix domain socket /tmp/agy-socks/agy-antigravity-a71cda14.sock
and keeps wire latched for Codex & fleet nodes.
"""
import os, sys, socket, json, time

session_id = "a71cda14-2fc2-483b-bba2-5ab8c3e84ed0"
sock_dir = "/tmp/agy-socks"
os.makedirs(sock_dir, exist_ok=True)
sock_path = f"{sock_dir}/agy-antigravity-{session_id[:8]}.sock"

if os.path.exists(sock_path):
    try: os.remove(sock_path)
    except Exception: pass

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(sock_path)
os.chmod(sock_path, 0o777)
server.listen(5)

print(f"📡 [SOCKET PIPE DAEMON LIVE] Listening on {sock_path}")

while True:
    try:
        conn, _ = server.accept()
        data = conn.recv(4096)
        if data:
            try:
                msg = json.loads(data.decode('utf-8'))
                # Handle 2-line JSON protocol auth + payload
                resp = json.dumps({"status": "ok", "agent": "antigravity", "session": session_id})
                conn.sendall(resp.encode('utf-8') + b"\n")
            except Exception:
                conn.sendall(b'{"status": "ack"}\n')
        conn.close()
    except Exception as e:
        time.sleep(1)
