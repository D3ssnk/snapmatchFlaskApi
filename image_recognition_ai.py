from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from flask import jsonify, request
from dropbox_utils import *
from dropbox.files import WriteMode
import time
import base64
import os
import requests

# initialises the dropbox client
dropbox_client = get_dropbox_client()
# Specify the Dropbox folder path
DROPBOX_FOLDER_PATH = '/Snapmatch/'
##################################################################################################
# In this section, we set the user authentication, user and app ID, model details, and the URL
# of the image we want as an input. Change these strings to run your own example.
#################################################################################################

# Your PAT (Personal Access Token) can be found in the Account's Security section
PAT = '04e3bce0eb5f4488b325b4658c2e13d3'
# Specify the correct user_id/app_id pairings
# Since you're making inferences outside your app's scope
USER_ID = 'clarifai'
APP_ID = 'main'
# Change these to whatever model and image URL you want to use
MODEL_ID = 'general-image-detection'
MODEL_VERSION_ID = '1580bb1932594c93b7e2e04456af7c6f'
IMAGE_URL = 'https://samples.clarifai.com/metro-north.jpg'
# To use a local file, assign the location variable
# IMAGE_FILE_LOCATION = 'YOUR_IMAGE_FILE_LOCATION_HERE'

############################################################################
# YOU DO NOT NEED TO CHANGE ANYTHING BELOW THIS LINE TO RUN THIS EXAMPLE
############################################################################

def get_image_items_from_ai(image_url):
    
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (('authorization', 'Key ' + PAT),)

    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    # To use a local file, uncomment the following lines
    # with open(IMAGE_FILE_LOCATION, "rb") as f:
    #     file_bytes = f.read()

    image_response = requests.get(image_url)

    # Check if the request was successful
    if image_response.status_code == 200:
        # Get the image data as bytes
        image_bytes = image_response.content

        # Pass the image data as bytes to Clarifai
        post_model_outputs_response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                user_app_id=userDataObject,
                model_id=MODEL_ID,
                version_id=MODEL_VERSION_ID,
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            image=resources_pb2.Image(
                                base64=image_bytes
                            )
                        )
                    )
                ]
            ),
            metadata=metadata
        )
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        return set()

    regions = post_model_outputs_response.outputs[0].data.regions
    results = []
    for region in regions:
        for concept in region.data.concepts:
            # Accessing and rounding the concept value
            name = concept.name
            results.append(name)

    return set(results)




    


def getImageIdentificationArray(data):
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

    return image_identity


