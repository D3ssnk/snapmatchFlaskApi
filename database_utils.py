import pymysql.cursors
import time
import os

# MySQL database configuration
DB_HOST = 'snapmatchdb.c3mmisa2asbw.eu-west-2.rds.amazonaws.com'
DB_USER = 'snapmatchAdmin'
DB_PASSWORD = 'kUkCCZDSyQE4THxrlBm8'
DB_NAME = 'snapmatchDatabase'


# Function to establish a connection to the MySQL database
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


# Function to insert a new challenge into the 'Challenges' table in the MySQL database
def insert_data_into_db(table_name, user_id, img_path, tags, caption):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Use string formatting for the table name
        query = f"INSERT INTO {table_name} (UserID, ImgPath, Tags, CreationDate, Caption) VALUES (%s, %s, %s, NOW(),%s)"
        cur.execute(query, (user_id, img_path, tags, caption))

        conn.commit()
    except Exception as e:
        print(f"Error inserting data into database: {str(e)}")
    finally:
        conn.close()

# Function to get a list of all challenges from a specific user in the MySQL database
def get_challenges_by_user_id(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT ChallengeID, UserID, Tags, CreationDate, Caption FROM Challenges WHERE UserID = %s', (user_id,))
    challenges = [dict(challenge) for challenge in cur.fetchall()]
    conn.close()
    challenges.sort(key=lambda challenge: challenge['CreationDate'], reverse=True)
    return challenges

def get_challenge_URL_by_challenge_id(challenge_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT ImgPath FROM Challenges WHERE ChallengeID = %s', (challenge_id,))
        imgPath = cur.fetchall()

        if imgPath:  # Check if there's any result
            img_path_parts = os.path.splitext(imgPath[0]['ImgPath'])
            cache_busting_url = f"{img_path_parts[0]}_v={int(time.time())}{img_path_parts[1]}"
            imgPath = cache_busting_url
            return imgPath
        else:
            return None

    except Exception as e:
        print('Error:', str(e))
        return None
    finally:
        conn.close()

