import os
import sys
import uuid
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from mds.models.rocrate import (  # noqa: E402
	ROCrate,
	PublishProvMetadata,
	PublishROCrateMetadata,
	UploadZippedCrate,
	UploadExtractedCrate,
	GetMetadataFromCrate
)
from mds.config import ( # noqa: E402
	#setup_minio,
	#setup_mongo,
	get_mongo_config,
	get_mongo_client,
	get_minio_config,
	get_minio_client
)
#import unittest



#class TestROCrateParsing(unittest.TestCase):
class TestROCrateParsing():
	def __init__(self):
		self.minio_config = get_minio_config()
		self.minio_client = get_minio_client()
		self.mongo_config = get_mongo_config()
		self.mongo_client = get_mongo_client()
		self.transaction_folder = str(uuid.uuid4())

		self.crate_path = "./tests/data/1.ppi_download.zip"
		self.crate_name = str(Path(self.crate_path).name)
		self.crate_stem = str(Path(self.crate_path).stem)
		# open zipped crate as a file
		self.guid = "ark:59842/test-crate"



	def test_0_upload_zipped_crate(self):

		# open zipped crate as a file
		with open("./tests/data/1.ppi_download.zip", "rb") as zipfile:

			# test uploading the
			upload_result = UploadZippedCrate(
				MinioClient=self.minio_client,
				ZippedObject=zipfile,
				BucketName=self.minio_config.rocrate_bucket,
				TransactionFolder=self.transaction_folder,
				Filename="1.ppi_download.zip"
			)

			assert upload_result is not None

		# TODO check that the folder was uploaded to the bucket


	def test_1_upload_extracted_crate(self):

		with open("./tests/data/1.ppi_download.zip", "rb") as zipfile:

			upload_result = UploadExtractedCrate(
				MinioClient=self.minio_client,
				ZippedObject=zipfile,
				BucketName=self.minio_config.default_bucket,
				TransactionFolder=self.transaction_folder,
			)

			assert upload_result.success 

		# TODO test that all files are extracted
		

	def test_2_get_metadata(self):
		""" test get_metadata_from_crate function
		"""
		self.rocrate = GetMetadataFromCrate(
			self.minio_client,
			BucketName=self.minio_config.default_bucket,
			TransactionFolder=self.transaction_folder,
			CratePath=self.crate_stem
			)

		assert self.rocrate is not None		

		assert isinstance(self.rocrate, ROCrate)


	def test_3_entailment(self):
		""" run entailment on the rocrate graph
		"""

		self.rocrate.entailment()

		# check that one computation has inverse properties
		graph = self.rocrate.metadataGraph

		example_computation = next(
			filter(
				lambda x: x.additionalType == "Computation", 
				graph
				)
			)

		# find inverse edges exist
		computation_guid  = example_computation.guid

		datasets = list(
			filter(
				lambda x:  x.additionalType=="Dataset",
				graph
			)
		)

		used_datasets = list(
			filter(
				lambda x: computation_guid in x.usedByComputation,	
				datasets
			)
		)

		dataset_guids = set([ dataset_elem.guid for dataset_elem in used_datasets])
		used_datasets = set(example_computation.usedDataset)

		assert len(dataset_guids.intersection(used_datasets)) == len(dataset_guids)


	def test_4_verify_crate_contents(self):

		rocrate_validation = self.rocrate.validateObjectReference(
			MinioClient=self.minio_client,
			MinioConfig=self.minio_config,
			TransactionFolder=self.transaction_folder,
			CrateName=self.crate_stem,
		)
	
		assert rocrate_validation.success


	def test_5_publish_identifiers(self):
		database = self.mongo_client[self.mongo_config.db]	
		rocrate_collection = database[self.mongo_config.rocrate_collection]
		identifier_collection = database[self.mongo_config.identifier_collection]

		crate_mongo_result = PublishROCrateMetadata(self.rocrate, rocrate_collection)	
		guid_mongo_result = PublishProvMetadata(self.rocrate, identifier_collection)

		assert crate_mongo_result
		assert guid_mongo_result


if __name__ == "__main__":
	#setup_minio()
	#setup_mongo()

	test_case = TestROCrateParsing()

	test_case.test_0_upload_zipped_crate()

	test_case.test_1_upload_extracted_crate()

	test_case.test_2_get_metadata()

	test_case.test_3_entailment()

	test_case.test_4_verify_crate_contents()

	test_case.test_5_publish_identifiers()