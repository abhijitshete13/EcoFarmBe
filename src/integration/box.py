import json
from django.core.exceptions import ObjectDoesNotExist
from .models import Integration
from boxsdk import (OAuth2, Client)
from boxsdk.exception import (BoxOAuthException,
    BoxException,)
from core.settings import (
    REDIS_URL,
    BOX_CLIENT_ID,
    BOX_CLIENT_SECRET,
    BOX_REFRESH_TOKEN,
    BOX_ACCESS_TOKEN)

def get_redis_obj():
    """
    Return redis object.
    """
    return redis.from_url(REDIS_URL)

def set_tokens(access_token, refresh_token):
    """
    Store box tokens in redis.Callable method can be
    passed to Box OAuth2 as a parameter to store token
    automatically.
    
    @param access_token: Access token to store.
    @param refresh_token: Refresh token to store.
    """
    import redis
    
    db = get_redis_obj()
    redis_value = json.dumps({'access_token': access_token, 'refresh_token': refresh_token})
    db.set("box_api_tokens", redis_value)

def set_tokens_db(access_token, refresh_token):
    """
    Store box tokens in database.Callable method can be
    passed to Box OAuth2 as a parameter to store token
    automatically.
    
    @param access_token: Access token to store.
    @param refresh_token: Refresh token to store.
    """
    _, created = Integration.objects.update_or_create(
        name='box',
        defaults={
            'access_token': access_token,
            'refresh_token': refresh_token}
    )

def get_oauth2_obj():
    """
    Return Box OAuth2 object.
    
    @return boxsdk.OAuth2 object.
    """
    try:
        try:
            obj = Integration.objects.get(name='box')
            access_token = obj.access_token
            refresh_token = obj.refresh_token
        except Integration.DoesNotExist:
            access_token = BOX_ACCESS_TOKEN
            refresh_token = BOX_REFRESH_TOKEN
        oauth = OAuth2(
            client_id=BOX_CLIENT_ID,
            client_secret=BOX_CLIENT_SECRET,
            access_token=access_token,
            refresh_token=refresh_token,
            store_tokens=set_tokens_db
        )
        return oauth
    except BoxOAuthException as exc:
        print(exc)
        return {'error': exc}

def get_box_tokens():
    """
    DO NOT MODIFY THIE METHOD.
        - Method is used in Zoho CRM to upload file to box.
    
    @return dict object.
    """
    try:
        oauth2 = get_oauth2_obj()
        client = Client(oauth2)
        user = client.user().get()
        return {'status': 'success','access_token': oauth2.access_token, 'refresh_token': oauth2._refresh_token}
    except BoxException as exc:
        return {'status_code': 'error', 'error': exc}
    
def get_box_client():
    """
    Return Box client.
    
    @return boxsdk.Client object.
    """
    obj = get_oauth2_obj()
    return Client(obj)

#-------------------------------------
# Box functions for folder.
#-------------------------------------
def get_folder_obj(folder_id):
    """
    Return box folder object.
    
    @param folder_id: Box folder id.
    @return boxsdk.Folder object.
    """
    client = get_box_client()
    return client.folder(folder_id=folder_id).get()

def get_folder_information(folder_id):
    """
    Return box folder information.
    
    @param folder_id: Box folder id.
    @return dict object.
    """
    folder = get_folder_obj(folder_id)
    return parse_folder(folder)

def create_folder(parent_folder_id, new_folder_name):
    """
    Create subfolder in parent folder.
    
    @param parent_folder_id: Parent folder id.
    @param new_folder_name: Name of new folder to create.
    @return folder_id.
    """
    return get_folder_obj(
        parent_folder_id).create_subfolder(
            new_folder_name
        ).id

def upload_file(folder_id, file_path):
    """
    Upload file to parent folder.
    
    @param folder_id: Box folder id.
    @param file_path: file path to upload.
    @return file id.
    """
    client = get_box_client()
    return client.folder(folder_id).upload(file_path)
    
def get_folder_items(folder_id):
    """
    Return sub-directories of folder.
    
    @param folder_id: Box folder id.
    @return dict object.
    """
    folders = get_folder_obj(folder_id).item_collection['entries']
    response = dict()
    for folder in folders:
        response[folder.object_id] = folder.name
    return response
    
def parse_folder(folder):
    """
    Parse folder information from api.
    
    @param boxsdk Folder object.
    @return dict object.
    """
    response = dict()
    response["id"] = folder.object_id
    response["type"] = folder.object_type
    response["Owner"] = {"id": folder.owned_by.id, "user": folder.owned_by.name}
    response["name"] = folder.name
    response["parent"] = folder.parent
    response["items"] = folder.item_collection
    response["shared_link"] = folder.get_shared_link()
    return response

#-------------------------------------
# Box functions for files.
#-------------------------------------

def get_file_obj(file_id):
    """
    Return box file object.
    
    @param file_id: Box file id.
    @return boxsdk File object.
    """
    client = get_box_client()
    return client.file(file_id).get()

def get_file_information(file_id):
    """
    Return file information.
    
    @param file_id: Box file id.
    @return dict object.
    """
    file_ = get_file_obj(file_id)
    return parse_file(file_)
    
def update_file_version(file_id, file_path):
    """
    Update latest version of file.
    
    @param file_id: Box file id.
    @param file_path: file path to update.
    @return file id.
    """
    client = get_box_client()
    return client.file(file_id).update_contents(file_path)
        
def parse_file(file_obj):
    """
    Paarse file from box.
    
    @param file_obj: boxsdk File object
    @return dict object
    """
    response = dict()
    response["id"] = file_obj.object_id
    response["name"] = file_obj.name
    response["type"] = file_obj.object_type
    response["ownder"] = {"id": file_obj.owned_by.id, "user": file_obj.owned_by.name}
    response["parent"] = file_obj.parent
    response["shared_link"] = file_obj.get_shared_link_download_url()
    return response

def get_shared_link(file_id):
    """
    Get shareable link for file
    """
    client = get_box_client()
    return client.file(file_id).get_shared_link()
    