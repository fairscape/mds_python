from fastapi import FastAPI, Response 
from mds.models import User, Group, ListUsers, Software, Computation
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


@app.put("/user")
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


@app.get("/user")
def user_list(response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	users = ListUsers(mongo_collection)

	mongo_client.close()

	return users


@app.get("/user/ark:{NAAN}/{postfix}")
def user_get(NAAN: str, postfix: str, response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	user_id = f"ark:{NAAN}/{postfix}" 

	user = User.construct(id=user_id)
	read_status = user.read(mongo_collection)

	mongo_client.close()


	if read_status.success:
		return user
	else:
		response.status_code = read_status.status_code
		return {"error": read_status.message}


@app.delete("/user/ark:{NAAN}/{postfix}")
def user_delete(NAAN: str, postfix: str):	
	# TODO change response codes depending on outcome

	user_id = f"ark:{NAAN}/{postfix}"
	
	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	user = User.construct(id=user_id)
	delete_status = user.delete(mongo_collection)

	mongo_client.close()

	if delete_status.success:
		return {"deleted": {"@id": user_id}}
	else:
		return {"error": f"{str(delete_status.message)}"}


@app.post("/group")
def group_create(group: Group, response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	create_status = group.create(mongo_collection)

	mongo_client.close()

	if create_status.success:
		return {"created": {"@id": group.id, "@type": "Organization"}}
	else:
		response.status_code = create_status.status_code
		return {"error": create_status.message}


@app.get("/group")
def group_list():

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	mongo_client.close()

	return {}


@app.get("/group/ark:{NAAN}/{postfix}")
def group_get(NAAN: str, postfix: str):
	group_id = f"ark:{NAAN}/{postfix}" 

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	group = Group.construct(id=group_id)

	group_read = group.read(mongo_collection)

	if group_read.success:
		return group
	else:
		return {"error": group_read.message}


@app.delete("/group/ark:{NAAN}/{postfix}")
def group_delete(group_id: str):
	return {}


@app.put("/group/ark:{NAAN}/{postfix}/addUser/")
def group_add_user():
	return {}


@app.put("/group/{group_id}/rmUser/")
def group_remove_user():
	return {}


# dataset handlers
@app.post("/dataset")
def dataset_create():
	return {}


@app.get("/dataset/ark:{NAAN}/{postfix}")
def dataset_get(NAAN: str, postfix: str):
	return {}

@app.post("/dataset/ark:{NAAN}/{postfix}/file")
def dataset_add_file(NAAN: str, postfix: str):
	return {}

# software handlers
@app.post("/software")
def software_create(software: Software, response: Response):

	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	create_status = software.create(mongo_collection)

	mongo_client.close()

	if create_status.success:
		return {"created": {"@id": software.id, "@type": "Software", "name": software.name}}
	else:
		response.status_code = create_status.status_code
		return {"error": create_status.message}



@app.get("/software/ark:{NAAN}/{postfix}")
def software_get(NAAN: str, postfix: str):
	return {}

# computation handlers
@app.post("/computation")
def computation_create(computation: Computation, response: Response):
	# TODO refactor connection
	mongo_client = get_config()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	create_status = computation.create(mongo_collection)

	mongo_client.close()

	if create_status.success:
		return {"created": {"@id": software.id, "@type": "Software", "name": software.name}}
	else:
		response.status_code = create_status.status_code
		return {"error": create_status.message}


@app.post("/computation/ark:{NAAN}/{postfix}/execute")
def computation_execute(NAAN: str, postfix: str):
	return {}

@app.get("/computation/ark:{NAAN}/{postfix}")
def computation_get(NAAN: str, postfix: str):
	return {}