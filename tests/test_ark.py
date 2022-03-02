import os
import sys
import mds
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestValidateArk(unittest.TestCase):
    def test_validate_ark_missing_ark(self):
        with self.assertRaises(ValueError):
            mds.validate_ark("99999/test-ark")

        with self.assertRaises(ValueError):
            mds.validate_ark("ark99999/test-ark")

        with self.assertRaises(ValueError):
            mds.validate_ark(":99999/test-ark")

    def test_validate_ark_naan_error(self):
        with self.assertRaises(ValueError):
            mds.validate_ark("ark:9999/test-ark")

        with self.assertRaises(ValueError):
            mds.validate_ark("ark:999/test-ark")

        with self.assertRaises(ValueError):
            mds.validate_ark("ark:99/test-ark")

        with self.assertRaises(ValueError):
            mds.validate_ark("ark:9/test-ark")

        with self.assertRaises(ValueError):
            mds.validate_ark("ark:/test-ark")

    def test_validate_ark_postfix_missing(self):
        with self.assertRaises(ValueError):
            mds.validate_ark("ark:99999/")

    def test_missing_slash(self):
        with self.assertRaises(ValueError):
            mds.validate_ark("ark:99999CAMA-test")


if __name__ == "__main__":
    unittest.main()
