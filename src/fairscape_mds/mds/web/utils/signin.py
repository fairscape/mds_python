import requests
import json

root_url = "http://localhost:8000/"


def list_existing_users():
    list_users = requests.get(root_url + "user")
    return list_users.json()


def get_user(user_id: str):
    user = requests.get(root_url + f"user/{user_id}")
    return user.json()


def get_user_attributes(user_id: str):
    user = get_user(user_id)
    user_stat = {
        "organizations": len(user['organizations']),
        "projects": len(user['projects']),
        "datasets": len(user['datasets']),
        "software": len(user['software']),
        "computations": len(user['computations']),
        "evidencegraphs": len(user['evidencegraphs'])
    }
    return user_stat


def check_signin_credentials(email: str, password: str):
    existing_users = list_existing_users()
    print(existing_users)
    for existing_user in existing_users['users']:
        if existing_user['@id']:
            user = get_user(existing_user['@id'])
            if email == user['email'] and password == user['password']:
                return True, existing_user['@id']
    return False, ""


def get_software_info():
    list_software = requests.get(root_url + "software")
    return list_software.json()


