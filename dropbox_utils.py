from database_utils import get_db_connection
import dropbox
from dropbox.sharing import SharedLinkSettings
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


# Function to get the dropbox parameters from the database
def get_app_parameter(pname):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT pValue FROM AppParameters WHERE pName = %s', (pname,))
        result = cur.fetchone()
        conn.close()
        return result['pValue'] if result else None
    except Exception as e:
        print(f"Error retrieving app parameter: {str(e)}")

# Function to use said parameters to create a client that can upload images
def get_dropbox_client():
    refresh_token = get_app_parameter('REFRESH_TOKEN')
    app_key = get_app_parameter('APP_KEY')

    return dropbox.Dropbox(oauth2_refresh_token=refresh_token, app_key=app_key)


# A function that takes in the file name and give us the url of that file in dropbox

def get_direct_image_url(dropbox_client, file_path):
    try:
        # Create a shared link with default settings
        link = dropbox_client.files_get_temporary_link(file_path)
        print(link)

        return link
    except dropbox.exceptions.ApiError as err:
        # Handle Dropbox API errors (e.g., file not found)
        print(f"Dropbox API error: {err}")
        return None


def delete_image_from_dropbox(dropbox_client, file_path):
    try:
        dropbox_client.files_delete_v2(file_path)
    except dropbox.exceptions.ApiError as err:
        print(f"Error deleting photo: {err}")
