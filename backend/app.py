from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import re
import bcrypt  

app = Flask(__name__)
CORS(app)

# Load JSON data
def load_data(filename):
    with open(filename, "r") as f:
        return json.load(f)

flavors = load_data("flavors.json")
reviews = load_data("reviews.json")

# In-memory users
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
    return jsonify(flavors)

@app.route("/reviews")
def get_reviews():
    return jsonify(reviews)
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    #Check missing fields
    if not username or not email or not password:
        return {"success": False, "message": "All fields are required."}, 400

    # Username validation
    if not re.match(r'^[A-Za-z][A-Za-z0-9_-]{2,19}$', username):
        return {"success": False, "message": "Invalid username."}, 400

    # Email validation
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return {"success": False, "message": "Invalid email."}, 400

    # Password validation
    if not (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'[0-9]', password) and
        re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    ):
        return {"success": False, "message": "Weak password."}, 400

    # Duplicate check
    for user in users:
        if user["username"] == username:
            return {"success": False, "message": "Username is already taken."}, 400
        if user["email"] == email:
            return {"success": False, "message": "Email is already registered."}, 400

    # Hash password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Create user
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

# Run app
if __name__ == "__main__":
    app.run(debug=True)