from database_utils import *
from flask import session
import hashlib
import base64

# Function to verify if the username and password are safe
def safe_username_password(username, password):
    # Verify if the username and password are not empty
    if not username or not password:
        return False

    # Preventing SQL injection
    malicious_code = ["<", ">", "{", "}", "[", "]", ";", ":", ",", ".", "?", "/", "\\", "|", "+", "-", "=", "~", "`", " ", "'", "#"]
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

# function to emcrypt an integer
def SymmetricEncryption(num):
    num_str = "CongratulationsondiscoveringtheeastereggIleftbehind" + str(num)
    num_bytes = num_str.encode('utf-8')
    encoded_bytes = base64.b64encode(num_bytes)
    encoded_str = encoded_bytes.decode('utf-8')
    replaced_str = encoded_str.replace('W', '-')
    return replaced_str

# function to decrypt a integer
def SymmetricDecryption(encoded_str):
    restored_str = encoded_str.replace('-', 'W')
    restored_bytes = restored_str.encode('utf-8')
    decoded_bytes = base64.b64decode(restored_bytes)
    decoded_str = decoded_bytes.decode('utf-8')
    return decoded_str.split('Ileftbehind')[1]

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

# for google login, save user's data to the database
def saveGoogleUserData(user_info):
    conn = None
    try: 
        # extract username from the email (the section before '@')
        user_email = user_info['email']
        print("user email: ", user_email)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT UserID FROM Users WHERE UserName = '{user_email}'")
        existing_user_id = cur.fetchone()

        # if the user has login before, return the userID
        if existing_user_id:
            # cur.execute('UPDATE Users SET UserName = %s, Email = %s, Avatar = %s WHERE UserID = %s',
            #         (username, user_email, user_info['picture'], user_info['id']))
            return existing_user_id['UserID']
        # else, new user, insert user's information to the database
        else:
            current_datetime = datetime.datetime.now() 

            query = f"INSERT INTO Users (UserName, Email, Avatar, RegistrationDate) VALUES ('{user_email}', '{user_email}', '{user_info['picture']}', '{current_datetime}')"
            cur.execute(query)
            conn.commit()
            
            cur.execute(f"SELECT UserID FROM Users WHERE UserName = '{user_email}'")
            user_id = cur.fetchone()
            print("After insertion user id: ", user_id['UserID'])
            if user_id:
                return user_id['UserID']
            else:
                return -1
    except Exception as e:
        print(f"Error inserting user into database: {str(e)}")
    finally:
        if conn is not None:
            conn.close()