import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mds
import unittest

class TestUserView(unittest.TestCase):
	def test_userview(self):
		member = mds.UserView(
			id = "ark:99999/testuser1",
			name = "test user1",
			email = "testuser1@example.org"
			)

		self.assertEqual(member.id, "ark:99999/testuser1")


class TestGroup(unittest.TestCase):



	def test_group(self):
		owner = mds.UserView(
			id = "ark:99999/testowner",
			name = "test owner",
			email = "testowner@example.org"
			)
		self.assertEqual(owner.id, "ark:99999/testowner")

		member = mds.UserView(
			id = "ark:99999/testuser1",
			name = "test user1",
			email = "testuser1@example.org"
			)
		grp = mds.Group(
			id="ark:99999/CAMA-users",
			name="Cama Users",
			owner=owner,
			members=[member]
			)	


if __name__=="__main__":
	unittest.main()