import collections.abc
import collections
collections.Iterable = collections.abc.Iterable  # патч для Python 3.13

from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, time

# ====== Инициализация ======
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
DATA_FILE = os.path.join(APP_DIR, "data.json")

app = Flask(
    __name__,
    static_folder="static",
    static_url_path=""
)
CORS(app)

# ====== Главная страница ======
@app.route("/")
def index():
    return app.send_static_file("index.html")

# ====== Data ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"users": [], "msgs": []}
    save_data()

# ====== API ======
@app.route("/api/data", methods=["GET"])
def get_data():
    return jsonify(data)

@app.route("/api/data", methods=["POST"])
def set_data():
    global data
    data = request.json
    save_data()
    return jsonify({"ok": True})

# ====== Пользователи ======
@app.route("/register", methods=["POST"])
def register():
    d = request.get_json()
    name = d.get("name")
    password = d.get("password")
    role = d.get("role", "")

    if not name or not password:
        return jsonify({"ok": False, "error": "empty"}), 400

    if any(u["name"].lower() == name.lower() for u in data["users"]):
        return jsonify({"ok": False, "error": "exists"}), 400

    user = {
        "id": len(data["users"]) + 1,
        "name": name,
        "password": password,
        "role": role,
        "fav": []
    }
    data["users"].append(user)
    save_data()

    return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

@app.route("/login", methods=["POST"])
def login():
    d = request.get_json()
    user = next(
        (u for u in data["users"]
         if u["name"].lower() == d.get("name","").lower()
         and u["password"] == d.get("password")),
        None
    )
    if not user:
        return jsonify({"ok": False}), 401

    return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

# ====== Избранное ======
@app.route("/fav", methods=["POST"])
def toggle_fav():
    d = request.get_json()
    uid = d.get("user")
    fav = d.get("fav")

    user = next((u for u in data["users"] if u["id"] == uid), None)
    if not user:
        return jsonify({"ok": False}), 404

    if fav in user["fav"]:
        user["fav"].remove(fav)
        action = "removed"
    else:
        user["fav"].append(fav)
        action = "added"

    save_data()
    return jsonify({"ok": True, "action": action})

# ====== Сообщения ======
@app.route("/msg", methods=["POST"])
def post_msg():
    d = request.get_json()
    data["msgs"].append({
        "from": d.get("from"),
        "to": d.get("to"),
        "text": d.get("text"),
        "time": int(time.time())
    })
    save_data()
    return jsonify({"ok": True})

@app.route("/msg", methods=["GET"])
def get_msgs():
    u1 = request.args.get("u1")
    u2 = request.args.get("u2")

    msgs = [
        m for m in data["msgs"]
        if (u2 == "GLOBAL" and m["to"] == "GLOBAL")
        or (str(m["from"]) == u1 and str(m["to"]) == u2)
        or (str(m["from"]) == u2 and str(m["to"]) == u1)
    ]
    return jsonify(msgs)

# ====== Запуск ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
