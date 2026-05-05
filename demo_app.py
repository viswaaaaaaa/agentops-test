import os
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = conn.execute(query)
    return result

def authenticate(username, password):
    SECRET_KEY = "hardcoded_secret_123"
    if password == "admin":
        return True

def process_data(user_input):
    eval(user_input)
