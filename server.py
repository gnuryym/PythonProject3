import collections.abc
import collections
collections.Iterable = collections.abc.Iterable  # патч для Python 3.13

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, json, time

# ====== Пути ======
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
DATA_FILE = os.path.join(APP_DIR, "data.json")

# ====== Инициализация Flask ======
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
CORS(app)

# ====== Главная страница ======
@app.route("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")

# ====== Работа с данными ======
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"users": [], "msgs": []}
    save_data()

# ====== API для данных ======
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
    name = (d.get("name") or "").strip()
    password = (d.get("password") or "").strip()
    role = d.get("role", "")
    portfolio = d.get("portfolio", "")

    if not name or not password:
        return jsonify({"ok": False, "error": "empty"}), 400

    if any(u["name"].lower() == name.lower() for u in data["users"]):
        return jsonify({"ok": False, "error": "exists"}), 400

    user = {
        "id": len(data["users"]) + 1,
        "name": name,
        "password": password,
        "role": role,
        "portfolio": portfolio,
        "fav": []
    }
    data["users"].append(user)
    save_data()
    return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

@app.route("/login", methods=["POST"])
def login():
    d = request.get_json()
    name_input = (d.get("name") or "").strip().lower()
    password_input = (d.get("password") or "").strip()

    user = next(
        (u for u in data["users"]
         if u["name"].lower() == name_input
         and u["password"] == password_input),
        None
    )
    if not user:
        return jsonify({"ok": False}), 401
    return jsonify({"ok": True, "user": {k: user[k] for k in user if k != "password"}})

# ====== Список пользователей ======
@app.route("/users", methods=["GET"])
def get_users():
    return jsonify([{k: u[k] for k in u if k != "password"} for u in data["users"]])

# ====== Профиль пользователя ======
@app.route("/profile/<int:uid>", methods=["GET"])
def get_profile(uid):
    u = next((u for u in data["users"] if u["id"] == uid), None)
    if not u:
        return jsonify({"ok": False}), 404
    return jsonify(u)

@app.route("/profile/<int:uid>", methods=["POST"])
def update_profile(uid):
    u = next((u for u in data["users"] if u["id"] == uid), None)
    if not u:
        return jsonify({"ok": False}), 404
    d = request.get_json()
    u["name"] = d.get("name", u["name"])
    u["password"] = d.get("password", u["password"])
    u["role"] = d.get("role", u["role"])
    u["portfolio"] = d.get("portfolio", u.get("portfolio",""))
    save_data()
    return jsonify({"ok": True, "user": {k: u[k] for k in u if k != "password"}})

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

@app.route("/fav/<int:uid>", methods=["GET"])
def get_fav(uid):
    u = next((u for u in data["users"] if u["id"] == uid), None)
    if not u:
        return jsonify([])
    return jsonify(u.get("fav", []))

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

# ====== Страница пользователя ======
@app.route("/user/<int:uid>")
def user_page(uid):
    return send_from_directory(STATIC_DIR, "user.html")

# ====== Запуск ======
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
