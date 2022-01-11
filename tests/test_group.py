import unittest
from mds import Group, UserView

class TestGroup(unittest.TestCase):

	def test_userview(self):
		member = UserView(
			id = "ark:99999/testuser1",
			name = "test user1",
			email = "testuser1@example.org"
			)


	def test_group(self):
		owner = UserView(
			id = "ark:99999/testowner",
			name = "test owner",
			email = "testowner@example.org"
			)
		member = UserView(
			id = "ark:99999/testuser1",
			name = "test user1",
			email = "testuser1@example.org"
			)
		grp = Group(
			id="ark:99999/CAMA-users",
			name="Cama Users"
			owner=owner,
			members=[member]
			)
		


if __name__=="main":
	unittest.main()