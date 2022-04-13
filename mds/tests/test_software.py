import test_path
import unittest
import mds


class TestSoftware(unittest.TestCase):
    def test_software_initialization(self):
        owner_inst1 = mds.UserView(
            id="ark:99999/testowner1",
            name="test owner1",
            email="testowner1@example.org"
        )
        self.assertEqual(owner_inst1.id, "ark:99999/testowner1")
        mds.Software(
            id="ark:99999/CAMA-users",
            name="john doe",
            owner=owner_inst1,
            author="author1",
            downloadUrl="ark:99999/downloaddir/thisfile",
            citation="doi://blabla"
        )


if __name__ == "__main__":
    unittest.main()
