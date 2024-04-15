import requests
import json
import re
from fairscape_mds.web.utils.signin import *
from fairscape_mds.config import get_fairscape_config

fairscapeConfig = get_fairscape_config()
root_url = 'http:\\{fairscapeConfig.host}'



def email_exists(email: str):
    existing_users = list_existing_users()
    for existing_user in existing_users['users']:
        if existing_user['@id']:
            user = get_user(existing_user['@id'])
            if email == user['email']:
                return True
    return False


def initiate_signup(first_name: str, last_name: str, email: str, password: str, confirm_password: str):
    count = 1001
    user_data = {
        "@id": f"ark:99999/test-user{count}",
        "name": f"{first_name} {last_name}",
        "type": "Person",
        "email": email,
        "password": password,
        "organizations": [],
        "projects": [],
        "datasets": [],
        "software": [],
        "computations": [],
        "evidencegraphs": []
    }
    create_user = requests.post(root_url + "user", data=json.dumps(user_data))
    create_user.json()
    if create_user.status_code == 201:
        count+= 1
        return True
    else:
        return False

