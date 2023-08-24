import os
import sys
from mds.models.rocrate import (
	UploadZippedCrate,
	UploadExtractedCrate,
	get_metadata_from_crate
)
from mds.config import (
	get_mongo_config,
	get_mongo_client,
	get_minio_config,
	get_minio_client
)
import uuid
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))


class TestROCrateParsing(unittest.TestCase):
	def __init__(self):
		self.minio_config = get_minio_config()
		self.minio_client = get_minio_client()
		self.mongo_config = get_mongo_config()
		self.mongo_client = get_mongo_client()
		self.transaction_folder = uuid.uuid4()



	def test_0_upload_zipped_crate(self):

		# open zipped crate as a file
		with open("./tests/data/1.ppi_download.zip", "rb") as zipfile:

			# test uploading the
			upload_result = UploadZippedCrate(
				MinioClient=self.minio_client,
				ZippedObject=zipfile,
				BucketName=self.minio_config.rocrate_bucket,
				TransactionFolder=self.transaction_folder
			)

			assert upload_result is not None

		# TODO check that the folder was uploaded to the bucket


	def test_1_upload_extracted_crate(self):
		# open zipped crate as a file
		with open("./tests/data/1.ppi_download.zip", "rb") as zipfile:

			upload_result = UploadExtractedCrate(
				MinioClient=self.minio_client,
				ZippedObject=zipfile,
				BucketName=self.minio_config.default_bucket,
				TransactionFolder=self.transaction_folder
			)

			assert upload_result is not None

		# TODO test that all files are extracted
		

	def test_2_get_metadata():
		pass


	def test_3_entailment():
		pass


	def test_4_verify_crate_contents():
		pass

	def test_5_publish_identifiers():
		pass
