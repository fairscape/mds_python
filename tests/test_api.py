import path
from fastapi.testclient import TestClient
from mds.app import app


client = TestClient(app)


def test_0_user_0_create():
	user_data = {
		"@id": "ark:99999/test-user",
		"@type": "Person",
		"name": "Test McTest",
		"email": "test@example.org",
		"password": "pass"
	}
	response = client.post("/user", json = user_data)
	assert response.status_code == 201
	assert response.json() == {"created": {"@id": user_data["@id"], "@type": "Person", "name": user_data["name"]}}


def test_0_user_1_list():
	# clear database
	response = client.get("/user")
	print(response.json())
	assert response.status_code == 200


def test_0_user_2_get():
	# clear database
	response = client.get("/user/ark:99999/test-user")
	assert response.status_code == 200


def test_0_user_3_update():
	# update the users name
	user_data = {
		"@id": "ark:99999/test-user",
		"@type": "Person",
		"name": "Testy McTesterson",
		"email": "test@example.org",
		"password": "pass"
	}

	response = client.put("/user", json = user_data)

	response_json = response.json()

	print(response_json)
	assert response.status_code == 200
	assert response_json == {"updated": {"@id": user_data["@id"], "@type": "Person", "name": user_data["name"]}}


def test_0_user_4_delete():
	response = client.delete("/user/ark:99999/test-user")
	assert response.status_code == 200
	assert response.json() == {"deleted": {"@id": "ark:99999/test-user", "@type": "Person", "name": "Testy McTesterson"}}


def test_1_group_0_create():
	# create test users
	user1_data = {
		"@id": "ark:99999/test-user1",
		"name": "Test User1",
		"type": "Person",
		"email": "testuser1@example.org",
		"password": "test1",
		"organizations": [],
		"projects": [],
		"datasets": [],
		"software": [],
		"computations": [],
		"evidencegraphs": []
		}
	user2_data = {
		"@id": "ark:99999/test-user2",
		"name": "Test User2",
		"type": "Person",
		"email": "testuser2@example.org",
		"password": "test2",
		"organizations": [],
		"projects": [],
		"datasets": [],
		"software": [],
		"computations": [],
		"evidencegraphs": []
		}
	user3_data = {
		"@id": "ark:99999/test-user3",
		"name": "Test User3",
		"type": "Person",
		"email": "testuser3@example.org",
		"password": "test3",
		"organizations": [],
		"projects": [],
		"datasets": [],
		"software": [],
		"computations": [],
		"evidencegraphs": []
		}

	group_data = {
		"@id": "ark:99999/test-group",
		"@type": "Organization",
		"name": "test group",
		"owner": {
			"@id": "ark:99999/test-user1",
			"@type": "Person",
			"name": "Test User1",
			"email": "testuser1@example.org"
			},
		"members": [{"@id": "ark:99999/test-user2",
		"name": "Test User2",
		"type": "Person",
		"email": "testuser2@example.org"}],
	}

	# create user1
	create_user1 = client.post("/user", json = user1_data)
	create_user2 = client.post("/user", json = user2_data)
	create_user3 = client.post("/user", json = user3_data)


	group_create = client.post("/group", json = group_data)

	print(group_create.json())

	assert group_create.status_code == 201
	assert group_create.json() == {"created": {"@id": group_data["@id"], "@type": "Organization", "name": group_data["name"]}}


def test_1_group_1_list():
	list_users = client.get("/user")

	print(list_users.json())
	assert list_users.status_code == 200


def test_1_group_2_get():

	get_group = client.get("/group/ark:99999/test-group")

	expected_group = {
		"@id": "ark:99999/test-group",
		"@type": "Organization",
		"name": "test group",
		"owner": {
			"@id": "ark:99999/test-user1",
			"@type": "Person",
			"name": "Test User1",
			"email": "testuser1@example.org"
			},
		"members": [
			{"@id": "ark:99999/test-user2",
			"name": "Test User2",
			"type": "Person",
			"email": "testuser2@example.org"}
			],
	}

	assert get_group.status_code == 200
	assert get_group.json() == expected_group


def test_1_group_3_update():


	expected_group = {

		"@id": "ark:99999/test-group",
		"@type": "Organization",
		"name": "test group",
		"owner": {
			"@id": "ark:99999/test-user1",
			"@type": "Person",
			"name": "Test User1",
			"email": "testuser1@example.org"
			},
		"members": [
			{"@id": "ark:99999/test-user2",
			"name": "Test User2",
			"type": "Person",
			"email": "testuser2@example.org"}
			],
		}

	group_update = {
		"name": "Updated Test Name"
	}

	expected_group["name"] = group_update["name"]

	update_group = client.put("/group/ark:99999/test-group", json=group_update)

	assert update_group.status_code == 200
	assert update_group.json() == {"updated": {"@id": expected_group["@id"], "@type": "Organization", "name": expected_group["name"]}}

	get_updated_group = client.get("/group/ark:99999/test-group")

	assert get_updated_group.status_code == 200
	assert get_updated_group.json() == expected_group


def test_1_group_4_add_user():
	pass


def test_1_group_5_rm_user():
	pass


def test_1_group_6_delete():
	group_delete = client.delete("/group/ark:99999/test-group")

	assert group_delete.status_code == 200
	assert group_delete.json() == {"deleted": {"@id": "ark:99999/test-group", "@type": "Organization", "name": "test group"}}