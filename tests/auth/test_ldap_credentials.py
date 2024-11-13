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

import unittest
from fairscape_mds.auth.ldap import (
	getUserTokens,
	updateUserToken,
	deleteUserToken,
	addUserToken,
	UserToken,
	UserTokenUpdate
)
# form an ldap connection
from fairscape_mds.config import get_fairscape_config


class TestLDAPCredentials(unittest.TestCase):
	testUserCN = 'maxheadroom'
	testUserDN = 'cn=maxheadroom,ou=users,dc=fairscape,dc=net'
	tokenUID = 'basic-token'


	@classmethod
	def setUpClass(cls) -> None:
		cls._config = get_fairscape_config(
			'deploy/local.env'
		)

		cls._config.ldap.hostname = 'localhost'
		cls._ldapConnection = cls._config.ldap.connectAdmin()
		return super().setUpClass()

	@classmethod
	def tearDownClass(cls) -> None:
		cls._ldapConnection.unbind()
		return super().tearDownClass()

	def test_create_credentials(self):
		tokenInstance = UserToken(
			tokenUID= self.tokenUID,
			tokenValue = 'i-ama-token',
			endpointURL = 'https://example.org'
		)

		addToken = addUserToken(
			self._ldapConnection,
			self.testUserDN,
			tokenInstance
		)

		self.assertEqual(addToken, True)

		# get the tokens and make sure 
		userTokens = getUserTokens(
			self._ldapConnection,
			self.testUserDN
			)

		self.assertEqual(len(userTokens), 1)
		self.assertIn(tokenInstance, userTokens)

		# update token
		updatedValue = 'new-token-value'
		updatedURL = 'https://cm4ai.org'

		testTokenUpdate = UserTokenUpdate(
			tokenUID=self.tokenUID,
			tokenValue=updatedValue
		)

		updateStatus = updateUserToken(
			self._ldapConnection,
			userDN=self.testUserDN,
			tokenUpdate=testTokenUpdate
		)
		self.assertTrue(updateStatus)

		testTokenUpdate = UserTokenUpdate(
			tokenUID=self.tokenUID,
			endpointURL=updatedURL
		)

		updateURLStatus = updateUserToken(
			self._ldapConnection,
			userDN=self.testUserDN,
			tokenUpdate=testTokenUpdate
		)

		self.assertTrue(updateURLStatus)

		deleteStatus = deleteUserToken(
			self._ldapConnection, 
			userDN=self.testUserDN, 
			tokenID=self.tokenUID
			)

		self.assertTrue(deleteStatus)

		# lookup tokens and	
		userTokens = getUserTokens(
			self._ldapConnection,
			self.testUserDN
			)

		self.assertEqual(len(userTokens), 0)


if __name__ == "__main__":
	unittest.main()	