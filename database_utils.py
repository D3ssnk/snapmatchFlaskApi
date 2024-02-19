import pymysql.cursors

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
    cur.execute('SELECT * FROM Challenges WHERE UserID = %s', (user_id,))
    challenges = [dict(challenge) for challenge in cur.fetchall()]
    conn.close()
    challenges.sort(key=lambda challenge: challenge['CreationDate'], reverse=True)
    return challenges
