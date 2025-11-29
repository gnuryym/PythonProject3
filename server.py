import collections.abc
import collections
collections.Iterable = collections.abc.Iterable  # патч для совместимости с Python 3.13

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
DATA_FILE = os.path.join(APP_DIR, "data.json")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)


# Инициализация данных
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"users": [], "msgs": []}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====== Статика ======
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(STATIC_DIR, path)

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
    uid = len(data["users"]) + 1
    user = {"id": uid, "name": name, "password": password, "role": role, "fav": []}
    data["users"].append(user)
    save_data()
    return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

@app.route("/login", methods=["POST"])
def login():
    d = request.get_json()
    name, password = d.get("name"), d.get("password")
    user = next((u for u in data["users"] if u["name"].lower() == name.lower() and u["password"] == password), None)
    if not user:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

@app.route("/users", methods=["GET"])
def get_users():
    role = request.args.get("role", "").lower()
    users = data["users"]
    if role:
        users = [u for u in users if u["role"].lower() == role]
    return jsonify([{k: u[k] for k in u if k != "password"} for u in users])

@app.route("/profile/<int:uid>", methods=["GET","POST"])
def profile(uid):
    user = next((u for u in data["users"] if u["id"] == uid), None)
    if not user:
        return jsonify({"ok": False, "error": "not found"}), 404
    if request.method == "GET":
        return jsonify({k: user[k] for k in user if k != "password"})
    else:
        d = request.get_json()
        user["name"] = d.get("name", user["name"])
        user["password"] = d.get("password", user["password"])
        user["role"] = d.get("role", user["role"])
        user["fav"] = d.get("fav", user.get("fav", []))
        save_data()
        return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

# ====== Избранное ======
@app.route("/fav", methods=["POST"])
def toggle_fav():
    d = request.get_json()
    uid = d.get("user")
    fav_id = d.get("fav")
    user = next((u for u in data["users"] if u["id"] == uid), None)
    if not user:
        return jsonify({"ok": False, "error": "user not found"}), 404
    if fav_id in user.get("fav", []):
        user["fav"].remove(fav_id)
        action = "removed"
    else:
        user.setdefault("fav", []).append(fav_id)
        action = "added"
    save_data()
    return jsonify({"ok": True, "action": action})

@app.route("/fav/<int:uid>", methods=["GET"])
def get_favs(uid):
    user = next((u for u in data["users"] if u["id"] == uid), None)
    if not user:
        return jsonify({"ok": False, "error": "user not found"}), 404
    return jsonify(user.get("fav", []))

# ====== Сообщения ======
@app.route("/msg", methods=["POST"])
def post_msg():
    d = request.get_json()
    msg = {
        "from": d.get("from"),
        "to": d.get("to"),
        "text": d.get("text"),
        "time": int(time.time())
    }
    data["msgs"].append(msg)
    save_data()
    return jsonify({"ok": True})

@app.route("/msg", methods=["GET"])
def get_msgs():
    u1 = request.args.get("u1")
    u2 = request.args.get("u2")
    msgs = []
    for m in data["msgs"]:
        if u2 == "GLOBAL" and m["to"] == "GLOBAL":
            msgs.append(m)
        elif u2 != "GLOBAL":
            if (str(m["from"]) == u1 and str(m["to"]) == u2) or (str(m["from"]) == u2 and str(m["to"]) == u1):
                msgs.append(m)
    return jsonify(msgs)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

