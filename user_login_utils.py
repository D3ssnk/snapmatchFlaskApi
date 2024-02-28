from database_utils import *
from flask import session
import hashlib

# Function to verify if the username and password are safe
def safe_username_password(username, password):
    # Verify if the username and password are not empty
    if not username or not password:
        return False

    # Preventing SQL injection
    malicious_code = ["<", ">", "{", "}", "[", "]", ";", ":", ",", ".", "?", "/", "\\", "|", "+", "=", "~", "`", " "]
    for code in malicious_code:
        if code in username or code in password:
            return False
    return True

# Function to encrypt the password
def password_encryption(password):
    SALTED_INFO = "wersnapmatch" + password + "team17"
    hl = hashlib.md5()
    hl.update(SALTED_INFO.encode(encoding='utf-8'))
    return hl.hexdigest()

# Function to register a new user in the MySQL database
# If registration is successful, return True, otherwise return False
def user_register(username, password):
    if not safe_username_password(username, password):
        return -1
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        #  Verify if the user already exists
        query = f"SELECT * FROM Users WHERE Username = '{username}'"
        cur.execute(query)
        user = cur.fetchone()

        if user:
            print("User already exists")
            return -1
        else:
            # Encrypt the password
            password = password_encryption(password)
            query = f"INSERT INTO Users (UserName, PasswordHash) VALUES ('{username}', '{password}')"
            cur.execute(query)
            conn.commit()
            print("User registered successfully")
            return 1
    except Exception as e:
        print(f"Error processing user info with database: {str(e)}")
    finally:
        conn.close()

# Function to login a user in the MySQL database
# If login is successful, return the user ID, otherwise return -1
def user_login(username, password):
    if not safe_username_password(username, password):
        print("Malicious code detected")
        return -1
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Encrypt the password
        password = password_encryption(password)
        query = f"SELECT UserID FROM Users WHERE UserName = '{username}' AND PasswordHash = '{password}'"
        cur.execute(query)
        user_id = cur.fetchone()
        if user_id:
            print("User logged in successfully")
            return user_id['UserID']
        else:
            print("User does not exist or password is incorrect")
            return -1
    except Exception as e:
        print(f"Error processing user info with database: {str(e)}")
    finally:
        conn.close()

def store_user_id_in_session(user_id):
    session['user_id'] = user_id

def get_user_id_from_session():
    return session.get('user_id', None)

def logout_user():
    session.pop('user_id', None)