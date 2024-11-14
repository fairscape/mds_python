import os
import sys

# add fairscape mds to path
sys.path.insert(0, 
	os.path.abspath(
		os.path.join(
			os.path.dirname(__file__), 
			'../../src'
			)
		)
	)

from fastapi.testclient import TestClient
import unittest
from fairscape_mds.app import app



client = TestClient(app)

class TestLDAPRouter(unittest.TestCase):

	def test_ldap_crud(self):
		# login and get user token

		testEmail="max_headroom@example.org"
		testPassword="testpassword"

		loginResponse = client.post(
			'/api/login', 
			data={
				"username": testEmail, 
				"password": testPassword
				}
			)

		self.assertEqual(loginResponse.status_code, 200)
		
		loginJSON = loginResponse.json()
		accessToken = loginJSON['access_token']
		authHeaders = {"Authorization": f"Bearer {accessToken}"}

		newToken = {
			"tokenUID": "basic-token",
			"tokenValue": "a-test-token-value",
			"endpointURL": "https://example.org"
		}	

		addTokenResponse = client.post(
			'/api/profile/credentials', 
			headers=authHeaders, 
			json=newToken
			)

		print(addTokenResponse.json())

		self.assertEqual(addTokenResponse.status_code, 201)

		tokenUpdate = {
			"tokenUID": newToken.get("tokenUID"),
			"endpointURL": "https://fairscape.net/"
		}

		updateTokenResponse = client.put(
			'/api/profile/credentials',
			headers=authHeaders, 
			json=tokenUpdate
		)
		
		self.assertEqual(updateTokenResponse.status_code, 200)

		getTokenResponse = client.get(
			'/api/profile/credentials',
			headers=authHeaders,
		)

		userTokens = getTokenResponse.json()

		self.assertEqual(getTokenResponse.status_code, 200)


		deleteTokenReponse = client.delete(
			f'/api/profile/credentials/{newToken.get("tokenUID")}',
			headers=authHeaders,
		)

		self.assertEqual(deleteTokenReponse, 200)




if __name__=="__main__":
	unittest.main()