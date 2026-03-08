#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# خادم التحكم عن بعد - نسخة متوافقة مع المنصات السحابية (Replit, Railway, Render)

import http.server
import socketserver
import json
import os
import time
import uuid
import subprocess
from urllib.parse import urlparse

# تحديد المنفذ: اقرأه من متغير البيئة PORT الذي تحدده المنصة، أو استخدم 5000 كاحتياطي
PORT = int(os.environ.get("PORT", 5000))
# الاستماع على كل العناوين (ضروري للمنصات السحابية)
HOST = "0.0.0.0"
SESSIONS_DIR = "sessions"

# إنشاء مجلد الجلسات
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # تعطيل السجل

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>✅ Server is running on cloud</h1>")
            return

        elif path == "/api/sessions":
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            sessions = []
            for f in os.listdir(SESSIONS_DIR):
                if f.endswith(".json"):
                    with open(os.path.join(SESSIONS_DIR, f), "r", encoding="utf-8") as fp:
                        try:
                            data = json.load(fp)
                            sessions.append(data)
                        except:
                            pass
            self.wfile.write(json.dumps(sessions, ensure_ascii=False).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(post_data)
        except:
            data = {}

        if path == "/api/create_session":
            ip = data.get("ip", "unknown")
            name = data.get("name", f"session_{ip}")
            session_id = f"{ip}_{uuid.uuid4().hex[:8]}"
            filename = os.path.join(SESSIONS_DIR, f"{ip}.json")
            session_data = {
                "ip": ip,
                "session_id": session_id,
                "name": name,
                "status": "active",
                "created_at": time.time()
            }
            if os.path.exists(filename):
                with open(filename, "r", encoding="utf-8") as f:
                    try:
                        existing = json.load(f)
                        if isinstance(existing, list):
                            existing.append(session_data)
                        else:
                            existing = [existing, session_data]
                    except:
                        existing = [session_data]
            else:
                existing = [session_data]

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=4)

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            response = {
                "success": True,
                "session_id": session_id,
                "ip": ip,
                "file": filename,
                "message": "تم إنشاء الجلسة"
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            print(f"✅ New session: {session_id}")
            return

        elif path == "/api/execute":
            session_id = data.get("session_id")
            command = data.get("command", "")
            if not session_id or not command:
                self.send_response(400)
                self.end_headers()
                return

            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
                if not output:
                    output = "[OK]"
            except Exception as e:
                output = str(e)

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            response = {
                "success": True,
                "session_id": session_id,
                "command": command,
                "output": output
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            print(f"⚡ Command from {session_id}: {command}")
            return

        self.send_response(404)
        self.end_headers()

def run():
    server = socketserver.ThreadingTCPServer((HOST, PORT), Handler)
    print("="*50)
    print("🚀 Cloud Server running on port", PORT)
    print("📁 Sessions dir:", os.path.abspath(SESSIONS_DIR))
    print("⚠️  Real commands execution")
    print("="*50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server")
        server.shutdown()

if __name__ == "__main__":
    run()
