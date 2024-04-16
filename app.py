from flask import Flask, jsonify, request, make_response, session, redirect
from datetime import datetime, timedelta
from flask_cors import CORS
from user_login_utils import *
from image_recognition_ai import *
from match_utils import *
from dropbox.files import WriteMode
from user_login_utils import *
from database_utils import *
import time
import base64
import os
import requests
import json

app = Flask(__name__)
app.secret_key = 'secretforsnapmatchteam1766666'

# Ensure that your Flask backend allows requests from your React app's domain.
CORS(app, supports_credentials=True, resources={r"/*": {"origins": ["http://localhost:3000", "https://snapmatch.top", "https://www.snapmatch.top"]}})

# initialises the dropbox client
dropbox_client = get_dropbox_client()

# Specify the Dropbox folder path
DROPBOX_FOLDER_PATH = '/Snapmatch/'

# Google login stuff
with open('client-secret.json', 'r') as f:
    client_secrets = json.load(f)

GOOGLE_CLIENT_ID = client_secrets['web']['client_id']
GOOGLE_CLIENT_SECRET= client_secrets['web']['client_secret'] 
REDIRECT_URI = "https://snapmatchapi.org/login/google/authorised"
SCOPE = 'https://www.googleapis.com/auth/userinfo.email'


# Function that send the objects within the image after being processed by the AI
@app.route('/api/identifyObjectInPhoto', methods=['POST'])
def analyse_photo_with_ai_route():
    try:
        data = request.get_json()
        # Ensure that 'photoData' are present in the request JSON
        if 'photoData' not in data:
            return jsonify({'error': 'Invalid request format. Missing required field}'}), 400

        # Receive the objects in the image from the AI
        image_identity = getImageIdentificationArray(data)
        return jsonify({'message': 'Photo received and identified successfully', 'data': image_identity})

    except Exception as e:
        print('Error processing request:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

# Function to check if the response matches the challenge.
@app.route('/api/checkIfMatch', methods=['POST'])
def check_response_matches_ai_route():
    try:
        data = request.get_json()
        # Ensure that 'photoData' and 'challengeTag' are present in the request JSON
        if 'photoData' not in data or 'challengeTag' not in data:
            return jsonify({'error': 'Invalid request format. Missing required field}'}), 400

        # Receive the objects in the image from the AI
        image_identity = getImageIdentificationArray(data)
        challengeTag = data['challengeTag']

        # Returns True if the response matches else false
        isMatchValue = isMatch(image_identity,challengeTag)
        return jsonify({'message': 'Photo received and identified successfully', 'data': isMatchValue})

    except Exception as e:
        print('Error processing request:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


# Function that uploads the challenge image with its caption and tag to the database and dropbox.
@app.route('/api/uploadChallenge', methods=['POST'])
def upload_photo_to_challenge_route():
    try:
        data = request.get_json()
        user_id = get_user_id_from_session()

        # Ensure that 'photoData' and 'caption' are present in the request JSON
        if 'photoData' not in data or 'caption' not in data or 'tag' not in data:
            return jsonify({'error': 'Invalid request format. Missing required field}'}), 400

        photo_data = data['photoData']
        caption = data['caption']
        tag = data['tag']

        # Decode base64-encoded photo data
        photo_binary = base64.b64decode(photo_data)

        # Generate a unique filename, for example, using a timestamp
        timestamp = str(int(time.time()))
        filename = f'captured_photo_{timestamp}_{user_id}.jpg'

        # Upload the photo to Dropbox
        dropbox_path = os.path.join(DROPBOX_FOLDER_PATH, filename)
        dropbox_client.files_upload(photo_binary, dropbox_path, mode=WriteMode('add'))

        # Receive the Dropbox image URL
        challenge_image_url = get_direct_image_url(dropbox_client, dropbox_path)

        # Insert challenge into the database
        insert_into_challenge_db(user_id, challenge_image_url, tag, caption)

        return jsonify({'message': 'Photo received and uploaded to Dropbox successfully'})

    except Exception as e:
        # Return an error to the frontend if the upload was unsuccessful
        print('Error processing request:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

# Function that uploads the response image with its caption and tag to the database and dropbox.
@app.route('/api/uploadResponse', methods=['POST'])
def upload_photo_to_response_route():
    try:
        data = request.get_json()
        user_id = get_user_id_from_session()

        # Ensure that 'photoData' and 'caption' are present in the request JSON
        if 'photoData' not in data or 'caption' not in data or 'challengeTag' not in data or 'challengeID' not in data:
            return jsonify({'error': 'Invalid request format. Missing required field}'}), 400

        photo_data = data['photoData']
        caption = data['caption']
        challengeTag = data['challengeTag']
        challengeID = data['challengeID']

        # Decode base64-encoded photo data
        photo_binary = base64.b64decode(photo_data)

        # Generate a unique filename, for example, using a timestamp
        timestamp = str(int(time.time()))
        filename = f'captured_photo_{timestamp}_{user_id}.jpg'

        # Upload the photo to Dropbox
        dropbox_path = os.path.join(DROPBOX_FOLDER_PATH, filename)
        dropbox_client.files_upload(photo_binary, dropbox_path, mode=WriteMode('add'))

        # Receive the Dropbox image URL
        response_image_url = get_direct_image_url(dropbox_client, dropbox_path)

        # Insert challenge into the database
        insert_points_into_db(challengeID,user_id)
        insert_into_response_db(challengeID, user_id, response_image_url, challengeTag, caption)
        return jsonify({'message': 'Photo received and uploaded to Dropbox successfully'})

    except Exception as e:
        # Return an error to the frontend if the upload was unsuccessful
        print('Error processing request:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

# Function that provides the frontend with the leaderboard
@app.route('/api/getLeaderboard', methods=['POST'])
def get_leaderboard_route():
    try:
        user_id = get_user_id_from_session()
        # Get leaderboard from the database
        leaderboard = get_leaderboard_from_database()
        for i, user in enumerate(leaderboard):
            print(user, i,user_id)
            if user['UserID'] == user_id:
                index = i + 1
                userInfo = [user]
                break
        leaderboard = leaderboard[:5]
        response_data ={
            'data' : leaderboard,
            'leaderboardPlace' : index,
            'userInfo' : userInfo
        }
        return jsonify(response_data)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500
    
# Function that provides the frontend with the challenge URL, caption and object value to be displayed
@app.route('/api/getResponsesByChallengeID', methods=['POST'])
def get_responses_route():
    try:
        data = request.get_json()
        # Ensure that 'challengeID' present in the request JSON
        if 'challengeID' not in data:
            return jsonify({'error': 'Invalid request format. Missing required field challenge ID}'}), 400

        challengeID = data['challengeID']
        # Get responses from the database
        responses = get_responses_by_challenge_id(challengeID)
        return jsonify(responses)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error in get responses'}), 500

# Function that provides the frontend with the challenge URL, caption and object value to be displayed
@app.route('/api/getChallengesByUserID', methods=['GET'])
def get_challenges_from_database_by_user_id_route():
    try:
        user_id = get_user_id_from_session()

        # Ensure that 'userID' is present in the request query parameters
        if not user_id:
            return jsonify({'error': 'No user ID provided'}), 400
        
        # Get challenges from the database
        challenges = get_challenges_by_user_id(user_id)
        return jsonify(challenges)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

# Function that provides the frontend with other peoples challenge URL, caption and object value to be displayed
@app.route('/api/getAllChallenges', methods=['GET'])
def get_all_challenges_route():
    try:
        user_id = get_user_id_from_session()

        # Get challenges from the database
        challenges = get_all_challenges(user_id)
        return jsonify(challenges)
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500



@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Invalid request format. Missing required field'}), 400

        # Register the user
        result = user_register(username, password)
        if result == 1:
            return jsonify({'message': 'User registered successfully'})
        elif result == -1:
            return jsonify({'error': 'User already exists'}), 400
        else:
            return jsonify({'error': 'Internal Server Error'}), 500
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500
    
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Invalid request format. Missing required field'}), 400

        # Login the user
        user_id = user_login(username, password)
        if user_id != -1 and user_id != None:
            store_user_id_in_session(user_id)
            return jsonify({'message': 'User logged in successfully'})
        else:
            return jsonify({'message': 'User does not exist or password is incorrect'}), 400
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'message': 'Internal Server Error'}), 500
    
@app.route('/api/logout', methods=['GET'])
def logout():
    try:
        # Clear the user session
        session.clear()
        return jsonify({'message': 'User logged out successfully'})
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500

# for Google login
@app.route('/api/google/login', methods = ['GET'])
def google_login():
    # Redirect to Google's OAuth 2.0 server
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}&response_type=code"
    return redirect(auth_url)

@app.route('/login/google/authorised',methods = ['GET', 'POST'])
def auth():
    # Get the authorization code from the request
    code = request.args.get('code')
    if code:
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        token_response = requests.post(token_url, data=token_data)

        # Check if the token request was successful
        if token_response.ok:
            access_token = token_response.json()['access_token']
            user_info_response = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}")
            # Check if the user info request was successful
            if user_info_response.ok:
                user_info = user_info_response.json()
                print(user_info)

                # store the user info to the database and get the true user id
                user_id = saveGoogleUserData(user_info)
                if user_id != -1 and user_id != None:
                    print("user id", user_id)
                    # Encrypt the user id and send it to the frontend
                    user_id = SymmetricEncryption(user_id)
                    # choose the front end url between local and production
                    # front_end_url = "http://127.0.0.1:3000"
                    front_end_url = "https://snapmatch.top"
                    return redirect(f"{front_end_url}/google_return_menu?userid={user_id}")
                else:
                    return jsonify({'message': 'Failed to get user id'}), 400
                
            else:
                return jsonify({'error': 'Failed to retrieve user information.'}), 500
        else:
            return jsonify({'error': 'Failed to exchange authorization code for access token.'}), 500
    else:
        return jsonify({'error': 'Authorization code not found.'}), 400


@app.route('/api/google/login/savesession', methods=['POST'])
def googleLoginJump():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        # Decrypt the user id
        user_id = SymmetricDecryption(user_id)

        if user_id != -1 and user_id != None:
            store_user_id_in_session(user_id)
            return jsonify({'message': 'User logged in successfully'})
        else:
            return jsonify({'message': 'Please do not try to hack into the system: ' + user_id}), 400
    except Exception as e:
        print('Someone is hacking the system Error:', str(e))
        return jsonify({'message': 'Internal Server Error'}), 500


@app.route('/api/google/logout', methods = ['GET'])
def googleLogout():
    # Get the access token from the session
    access_token = session.get('access_token')
    if access_token:
        # Revoke the access token
        revoke_url = f"https://oauth2.googleapis.com/revoke?token={access_token}"
        revoke_response = requests.get(revoke_url)
        # Check if the token was successfully revoked
        if revoke_response.ok:
            # Clear the user's session data
            session.clear()
            #return redirect(url_for('index'))
        else:
            # Handle error when revoking token
            return jsonify({'error': 'Failed to revoke access token.'}), 500
    else:
        # Handle case when access token is not found in session
        return jsonify({'error': 'Access token not found in session.'}), 400
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
