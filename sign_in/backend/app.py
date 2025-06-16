from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder="../frontend")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 初始化資料庫
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            time TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route('/admin')
def serve_admin():
    return send_from_directory(app.static_folder, "admin.html")

@app.route('/checkin', methods=["POST"])
def checkin():
    name = request.json.get("name")
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not name:
        return jsonify({"status": "error", "message": "姓名不可為空"}), 400

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO checkin (name, time) VALUES (?, ?)", (name, time_now))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "已簽到過"}), 400

    # 通知所有管理頁
    socketio.emit("new_checkin", {"name": name, "time": time_now})
    return jsonify({"status": "success", "message": "簽到成功"})

@app.route("/list")
def get_list():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, time FROM checkin ORDER BY time DESC")
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)

if __name__ == "__main__":
    init_db()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
