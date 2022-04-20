import path
from fastapi.testclient import TestClient
from mds.main import app


client = TestClient(app)


def test_0_user_0_list():
	response = client.get("/user")
	assert response.status_code == 200


def test_0_user_1_create():
	user_data = {
		"@id": "ark:99999/test-user",
		"@type": "Person",
		"name": "Test McTest",
		"email": "test@example.org",
		"password": "pass"
	}
	response = client.post("/user", json = user_data)
	assert response.status_code == 201


def test_0_user_2_delete():
	response = client.delete("/user/ark:99999/test-user/")
	assert response.status_code == 200


def test_0_user_3_update():
	user_data = {
		"@id": "ark:99999/test-user",
		"@type": "Person",
		"name": "Test McTest",
		"email": "test@example.org",
		"password": "pass"
	}
	response = client.post("/user", json = user_data)
	assert response.status_code == 201
	pass


def test_1_group_0_create():
	pass