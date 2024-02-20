from flask import Flask, jsonify, request, make_response
from datetime import datetime, timedelta
from flask_cors import CORS
from dropbox_utils import *
from user_login_utils import *
from image_recognition_ai import *
from dropbox.files import WriteMode
import time
import base64
import os

app = Flask(__name__)

# Ensure that your Flask backend allows requests from your React app's domain.
CORS(app)

# initialises the dropbox client
dropbox_client = get_dropbox_client()

# Specify the Dropbox folder path
DROPBOX_FOLDER_PATH = '/Snapmatch/'


# Function that send the objects within the image after being processed by the AI
@app.route('/api/identifyObjectInPhoto', methods=['POST'])
def analyse_photo_with_ai_route():
    try:
        data = request.get_json()
        if 'photoData' not in data:
            return jsonify({'error': 'Invalid request format. Missing required field}'}), 400
        photo_data = data['photoData']
        photo_binary = base64.b64decode(photo_data)

        # Generate a unique filename, for example, using a timestamp
        timestamp = str(int(time.time()))
        filename = f'captured_photo_{timestamp}.jpg'

        # Upload the temporary photo to Dropbox
        dropbox_path = os.path.join(DROPBOX_FOLDER_PATH, filename)
        dropbox_client.files_upload(photo_binary, dropbox_path, mode=WriteMode('add'))

        # Receive the Dropbox image URL
        challenge_image_url = get_direct_image_url(dropbox_client, dropbox_path)

        # Identify objects in the image
        image_identity = list(get_image_items_from_ai(challenge_image_url))

        # delete the temporary image
        delete_image_from_dropbox(dropbox_client, dropbox_path)
        return jsonify({'message': 'Photo received and identified successfully', 'data': image_identity})

    except Exception as e:
        print('Error processing request:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


# Function that uploads the image with its caption and tag to the database and dropbox.
@app.route('/api/uploadChallenge', methods=['POST'])
def upload_photo_to_database_route():
    try:
        data = request.get_json()

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
        filename = f'captured_photo_{timestamp}.jpg'

        # Upload the photo to Dropbox
        dropbox_path = os.path.join(DROPBOX_FOLDER_PATH, filename)
        dropbox_client.files_upload(photo_binary, dropbox_path, mode=WriteMode('add'))

        # Receive the Dropbox image URL
        challenge_image_url = get_direct_image_url(dropbox_client, dropbox_path)

        # Insert challenge into the database
        user_id = 1  # dummy user until login is implemented
        insert_data_into_db('Challenges', user_id, challenge_image_url, tag, caption)
        return jsonify({'message': 'Photo received and uploaded to Dropbox successfully'})

    except Exception as e:
        # Return an error to the frontend if the upload was unsuccessful
        print('Error processing request:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


# Function that provides the frontend with the challenge URL, caption and object value to be displayed
@app.route('/api/getChallengesByUserID', methods=['GET'])
def get_challenges_from_database_by_user_id_route():
    try:
        user_id = 1  # fake user id exists in the database now

        # Ensure that 'userID' is present in the request query parameters
        if not user_id:
            return jsonify({'error': 'No user ID provided'}), 400

        # Get challenges from the database
        challenges = get_challenges_by_user_id(user_id)

        # Modify the filename part of the image URLs to include a cache-busting identifier
        for challenge in challenges:
            img_path_parts = os.path.splitext(challenge['ImgPath'])
            cache_busting_url = f"{img_path_parts[0]}_v={int(time.time())}{img_path_parts[1]}"
            challenge['ImgPath'] = cache_busting_url

        response = make_response(jsonify(challenges))
        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response

    except Exception as e:
        # Return an error to the frontend if the upload was unsuccessful
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
            return jsonify({'error': 'Invalid request format. Missing required field'}), 400

        # Login the user
        user_id = user_login(username, password)
        if user_id != -1:
            return jsonify({'userID': user_id})
        else:
            return jsonify({'error': 'User does not exist or password is incorrect'}), 400
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
