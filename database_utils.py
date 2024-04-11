import pymysql.cursors
import time
import datetime
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
def insert_into_challenge_db(user_id, img_path, tags, caption):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Use string formatting for the table name
        query = """
        INSERT INTO Challenges (UserID, ImgPath, Tags, CreationDate, Caption) 
        VALUES (%s, %s, %s, NOW(), %s);
        """
        query2 = "UPDATE Users SET UserScore = UserScore + 10 WHERE UserID = %s;"

        # Execute the query with the appropriate parameters
        cur.execute(query, (user_id, img_path, tags, caption))
        cur.execute(query2, (user_id,))

        conn.commit()
    except Exception as e:
        print(f"Error inserting data into database: {str(e)}")
    finally:
        conn.close()


# Function to insert a new challenge into the 'Responses' table in the MySQL database
def insert_into_response_db(challengeID, user_id, img_path, tags, caption):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Use string formatting for the table name
        query = f"INSERT INTO Responses (ChallengeID ,UserID, ImagePath, Tags, CommentText, PostDate) VALUES (%s,%s, %s, %s, %s,NOW())"
        cur.execute(query, (challengeID, user_id, img_path, tags, caption))

        conn.commit()
    except Exception as e:
        print(f"Error inserting data into database: {str(e)}")
    finally:
        conn.close()

#hi
# Function check how many responses have currently been made for a challenge and then gives the user points accordingly
def insert_points_into_db(challengeID,userID):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Use string formatting for the table name
        query = "SELECT * FROM Responses WHERE ChallengeID = %s;"
        query2 = "UPDATE Users SET UserScore = UserScore + %s WHERE UserID = %s;"

        # Execute the query with the appropriate parameters
        cur.execute(query, (challengeID,))
        responses = [dict(response) for response in cur.fetchall()]
        num_responses = len(responses)
        if num_responses == 0:
            cur.execute(query2, ("50",userID))
        elif num_responses == 1:
            cur.execute(query2, ("40",userID))
        elif num_responses == 2:
            cur.execute(query2, ("30",userID))
        elif num_responses == 3:
            cur.execute(query2, ("20",userID))
        else:
            cur.execute(query2, ("10",userID))
        conn.commit()
    except Exception as e:
        print(f"Error inserting data into database: {str(e)}")
    finally:
        conn.close()

# Function to get a list of all challenges from a specific user in the MySQL database
def get_challenges_by_user_id(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        query = f"""
                        SELECT Challenges.*, Users.UserName 
                        FROM Challenges JOIN Users 
                        ON Challenges.UserID = Users.UserID
                        WHERE Challenges.UserID = {user_id}
                        """
        cur.execute(query)
        challenges = [dict(challenge) for challenge in cur.fetchall()]
        challenges.sort(key=lambda challenge: challenge['CreationDate'], reverse=True)
        return challenges
    except Exception as e:
        print(f"Error get challenges by user ID: {str(e)}")
    finally:
        conn.close()

# Function to get a list of all responses from a specific challenge in the MySQL database
def get_responses_by_challenge_id(challenge_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = f"""
        SELECT Responses.*, Users.UserName
        FROM Responses
        JOIN Users ON Responses.UserID = Users.UserID
        WHERE Responses.ChallengeID = {challenge_id};
        """
        print("did 1")
        cur.execute(query)
        print("did 2")
        responses = [dict(response) for response in cur.fetchall()]
        print("did 3")
        responses.sort(key=lambda response: response['PostDate'], reverse=True)
        print("did 4")
        return responses
    except Exception as e:
        print(f"Error get responses by challenge ID: {str(e)}")
    finally:
        conn.close()

def get_leaderboard_from_database():
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
                SELECT UserName, UserScore, UserID
                FROM Users
                ORDER BY UserScore DESC;
                    """
    cur.execute(query)
    leaderboard = [dict(users) for users in cur.fetchall()]
    conn.close()
    return leaderboard

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

def get_all_challenges(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Get all challenges from other users with their usernames
        query = f"""
                SELECT Challenges.*, Users.UserName 
                FROM Challenges JOIN Users 
                ON Challenges.UserID = Users.UserID
                WHERE Challenges.UserID != {user_id}
                """
        cur.execute(query)

        challenges = [dict(challenge) for challenge in cur.fetchall()]
        challenges.sort(key=lambda challenge: challenge['CreationDate'], reverse=True)
        return challenges
    except Exception as e:
        print('Error:', str(e))
        return None
    finally:
        conn.close()


