from fastapi import FastAPI, Response 
from mds.models import User, Group, ListUsers
from mds.mongo import MongoConfig

app = FastAPI()


def get_config():
    return MongoConfig(
            host_uri = "localhost",
            port = 27017,
            user = "root",
            password = "example"
            ).connect()


"""
def mongo_operation(callable) -> operation_status:

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	create_status = callable()

	mongo_client.close()
"""

@app.get("/ark:{NAAN}/{identifier}")
def resolve_ark():
	pass

@app.post("/user", status_code = 201)
def user_create(user: User, response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	create_status = user.create(mongo_collection)

	mongo_client.close()

	if create_status.success:
		return {"created": {"@id": user.id, "@type": "Person"}}
	else:
		response.status_code = create_status.status_code
		return {"error": create_status.message}


@app.get("/user")
def user_list(response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	users = ListUsers(mongo_collection)

	mongo_client.close()

	return users


@app.get("/user/{user_id: path}")
def user_get(user_id: str, response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	user = User.construct(id=user_id)
	read_status = user.read(mongo_collection)

	mongo_client.close()


	if read_status.success:
		return user
	else:
		response.status_code = read_status.status_code
		return {"error": read_status.message}


@app.put("/user/{user_id: path}")
def user_update(user: User, response: Response):
	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	update_status = user.update(mongo_collection)

	mongo_client.close()

	if update_status.success:
		return {"updated": {"@id": user.id, "@type": "Person"}}
	else:
		response.status_code = update_status.status_code
		return {"error": update_status.message}


@app.delete("/user/{user_id}")
def user_delete():
	return {}


@app.post("/group")
def group_create(group: Group):
	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	create_status = group.create(mongo_collection)

	mongo_client.close()

	if create_status.success:
		return {"created": {"@id": group.id, "@type": "Person"}}
	else:
		response.status_code = create_status.status_code
		return {"error": create_status.message}


@app.get("/group/{group_id}")
def group_get(group_id: str):
	return {}


@app.delete("/group/{group_id}")
def group_delete(group_id: str):
	return {}


@app.put("/group/{group_id}/add/{user_id}")
def group_add_user():
	return {}


@app.put("/group/{group_id}/rm/{user_id}")
def group_remove_user():
	return {}