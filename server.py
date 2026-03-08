from flask import Flask, jsonify, request
from flask_cors import CORS
import os, json, time, uuid, subprocess

app = Flask(__name__)
CORS(app)  # تمكين CORS كامل

SESSIONS_DIR = "sessions"
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# صفحة البداية
@app.route("/")
def index():
    return "<h1>✅ Server is running on cloud</h1>"

# عرض جميع الجلسات
@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    sessions = []
    for f in os.listdir(SESSIONS_DIR):
        if f.endswith(".json"):
            with open(os.path.join(SESSIONS_DIR, f), "r", encoding="utf-8") as fp:
                try:
                    data = json.load(fp)
                    sessions.append(data)
                except:
                    pass
    return jsonify(sessions)

# إنشاء جلسة جديدة
@app.route("/api/create_session", methods=["POST"])
def create_session():
    data = request.json or {}
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

    return jsonify({
        "success": True,
        "session_id": session_id,
        "ip": ip,
        "file": filename,
        "message": "تم إنشاء الجلسة"
    })

# تنفيذ أوامر على السيرفر
@app.route("/api/execute", methods=["POST"])
def execute_command():
    data = request.json or {}
    session_id = data.get("session_id")
    command = data.get("command", "")
    if not session_id or not command:
        return jsonify({"success": False, "message": "يجب توفير session_id و command"}), 400

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if not output:
            output = "[OK]"
    except Exception as e:
        output = str(e)

    return jsonify({
        "success": True,
        "session_id": session_id,
        "command": command,
        "output": output
    })

# تشغيل السيرفر على Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
