import random
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import re
import bcrypt

app = Flask(__name__)
CORS(app)

def load_data(filename):
    with open(filename, "r") as f:
        return json.load(f)

flavors = load_data("flavors.json")
reviews = load_data("reviews.json")

users = [
    {
        "id": 1,
        "username": "sweet_alice",
        "email": "alice@example.com",
        "password_hash": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8"),
        "cart": [],
        "orders": []
    }
]

# Routes
@app.route("/")
def home():
    return jsonify({"message": "Backend is running!"})

@app.route("/flavors")
def get_flavors():
    return jsonify({
        "success": True,
        "message": "Flavors loaded.",
        "flavors": flavors
    })


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return {"success": False, "message": "All fields are required."}, 400

    if not re.match(r'^[A-Za-z][A-Za-z0-9_-]{2,19}$', username):
        return {"success": False, "message": "Invalid username."}, 400

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return {"success": False, "message": "Invalid email."}, 400
    if not (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'[0-9]', password) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    ):
        return {"success": False, "message": "Weak password."}, 400

    for user in users:
        if user["username"] == username:
            return {"success": False, "message": "Username is already taken."}, 400
        if user["email"] == email:
            return {"success": False, "message": "Email is already registered."}, 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    new_user = {
        "id": len(users) + 1,
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "cart": [],
        "orders": []
    }

    users.append(new_user)

    return {
        "success": True,
        "message": "Registration successful."
    }, 201 
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"success": False, "message": "Email and password are required."}, 400

    user = next((u for u in users if u["email"] == email), None)
    if not user:
        return {"success": False, "message": "Invalid email or password."}, 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return {"success": False, "message": "Invalid email or password."}, 401

    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    }, 200

@app.route("/reviews")
def manage_reviews():
    random_reviews = random.sample(reviews, min(2, len(reviews)))

    return jsonify({
        "success": True,
        "message": "Reviews loaded.",
        "reviews": random_reviews
    })
@app.route("/cart", methods=["GET"])
def get_cart():
    user_id = request.args.get("userId")

    if not user_id:
        return {"success": False, "message": "userId required."}, 400

    user = next((u for u in users if str(u["id"]) == user_id), None)

    if not user:
        return {"success": False, "message": "User not found."}, 404

    return {
        "success": True,
        "message": "Cart loaded.",
        "cart": user["cart"]
    }, 200
@app.route("/cart", methods=["POST"])
def add_to_cart():
    data = request.json
    user_id = data.get("userId")
    flavor_id = data.get("flavorId")

    if not user_id or not flavor_id:
        return {"success": False, "message": "userId and flavorId required."}, 400

    user = next((u for u in users if u["id"] == int(data.get("userId"))), None)
    if not user:
        return {"success": False, "message": "User not found."}, 404

    flavor = next((f for f in flavors if f["id"] == flavor_id), None)
    if not flavor:
        return {"success": False, "message": "Flavor not found."}, 404

    existing_item = next((item for item in user["cart"] if item["flavorId"] == flavor_id), None)
    if existing_item:
        return {"success": False, "message": "Flavor already in cart. Use PUT to update quantity."}, 400

    user["cart"].append({
        "flavorId": flavor["id"],
        "name": flavor["name"],
        "price": flavor["price"],
        "quantity": 1
    })

    return {
        "success": True,
        "message": "Flavor added to cart.",
        "cart": user["cart"]
    }, 200
@app.route("/cart", methods=["PUT"])
def update_cart():
    data = request.json
    user_id = data.get("userId")
    flavor_id = data.get("flavorId")
    quantity = data.get("quantity")

    if not user_id or not flavor_id or quantity is None:
        return {"success": False, "message": "Missing fields."}, 400

    if quantity < 1:
        return {"success": False, "message": "Quantity must be at least 1."}, 400

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return {"success": False, "message": "User not found."}, 404

    item = next((i for i in user["cart"] if i["flavorId"] == flavor_id), None)
    if not item:
        return {"success": False, "message": "Flavor not in cart."}, 404

    item["quantity"] = quantity

    return {
        "success": True,
        "message": "Cart updated successfully.",
        "cart": user["cart"]
    }, 200
@app.route("/cart", methods=["DELETE"])
def delete_cart_item():
    data = request.json
    user_id = data.get("userId")
    flavor_id = data.get("flavorId")

    if not user_id or not flavor_id:
        return {"success": False, "message": "Missing fields."}, 400

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return {"success": False, "message": "User not found."}, 404

    user["cart"] = [item for item in user["cart"] if item["flavorId"] != flavor_id]

    return {
        "success": True,
        "message": "Flavor removed from cart.",
        "cart": user["cart"]
    }, 200
@app.route("/orders", methods=["POST"])
def place_order():
    data = request.json
    user_id = data.get("userId")

    if not user_id:
        return {"success": False, "message": "userId required."}, 400

    try:
        user_id = int(user_id)
    except:
        return {"success": False, "message": "Invalid userId."}, 400

    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return {"success": False, "message": "User not found."}, 404

    if not user["cart"]:
        return {"success": False, "message": "Cart is empty."}, 400

    total = sum(item["price"] * item["quantity"] for item in user["cart"])

    order = {
        "orderId": len(user["orders"]) + 1,
        "items": user["cart"].copy(),
        "total": total,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    user["orders"].append(order)
    user["cart"] = []

    return {
        "success": True,
        "message": "Order placed successfully.",
        "orderId": order["orderId"]
    }, 201

if __name__ == "__main__":
    app.run(debug=True)