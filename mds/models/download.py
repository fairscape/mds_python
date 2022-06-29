from typing import Optional, Union
from datetime import datetime
from pydantic import Extra
from bson import SON
import pymongo

from mds.models.fairscape_base import FairscapeBaseModel
from mds.models.dataset import Dataset
from mds.models.compact.dataset import DatasetCompactView
from mds.models.compact.software import SoftwareCompactView
from mds.utilities.operation_status import OperationStatus

from mds.database.config import MINIO_BUCKET, MONGO_DATABASE, MONGO_COLLECTION


class Download(FairscapeBaseModel, extra=Extra.allow):
	context = {"@vocab": "https://schema.org/", "evi": "https://w3id/EVI#"}
	type = "DataDownload"
	encodingFormat: str
	contentSize: Optional[str]
	contentUrl: Optional[str]
	encodesCreativeWork: Union[DatasetCompactView, SoftwareCompactView, str]
	sha256: Optional[str]
	uploadDate: Optional[datetime]
	version: Optional[str]
	# status: str


	def create_metadata(self, MongoClient: pymongo.MongoClient) -> OperationStatus:

		if self.version == None:
			# create versioning
			self.version = "1.0"

		# handle if encodesCreativeWork is string or dictionary
		if type(self.encodesCreativeWork) == str:
			if self.encodesCreativeWork == "":
				return OperationStatus(False, "missing dataset", 400)

			dataset_id = self.encodesCreativeWork

		elif type(self.encodesCreativeWork) == dict:
			dataset_id = self.encodesCreativeWork.get("@id")

		# TODO test for different types of encodesCreativeWork	
		else:
			return OperationStatus(False, f"encodesCreativeWork {self.encodesCreativeWork} not valid", 400)


		# preform all operations as a single transaction
		with MongoClient.start_session(causal_consistency=True) as session:
			mongo_database = MongoClient[MONGO_DATABASE]
			mongo_collection = mongo_database[MONGO_COLLECTION]

			dataset_metadata = mongo_collection.find_one({"@id": dataset_id}, session=session)
			if dataset_metadata == None:
				return OperationStatus(False, f"dataset {dataset_id} not found", 404)

			# Construct not working	
			#dataset = Dataset.construct(_fields_set= dataset_metadata.keys(), **dataset_metadata)

			# update the encodesCreativeWork property with a DatasetCompactView
			self.encodesCreativeWork = {
				"id": dataset_metadata.get("@id"), 
				"@type": dataset_metadata.get("@type"), 
				"name": dataset_metadata.get("name")
			}


			# TODO test output of operations
			# create metadata record in mongo
			insert_result = mongo_collection.insert_one(self.dict(by_alias=True), session=session)

			# TODO check that update was successfull
			# test update result	
			update_result = mongo_collection.update_one(
				{"@id": dataset_metadata.get("id")}, 
				{"$addToSet" : { 
					"distribution": SON([("@id", self.id), ("@type", "DataDownload"), ("name", self.name), ("contentUrl", "")])}
				}, session=session),

		# TODO handle errors
		#except Exception as bwe:
		#	return OperationStatus(False, f"create download error: {bwe}", 500)

		#if bulk_write_result.inserted_count != 1:
		#	return OperationStatus(False, "create download error: {bulk_write_result.bulk_api_result}", 500)

		return OperationStatus(True, "", 201)


	def register(self, Object, MongoClient: pymongo.MongoClient, MinioClient) -> OperationStatus:
		"""
		uploads the file and ammends the dataDownload metadata and dataset metadata
		"""
		mongo_database = MongoClient[MONGO_DATABASE]
		mongo_collection = mongo_database[MONGO_COLLECTION]


		# check that the data download metadata record exists
		data_download = mongo_collection.find_one({"@id": self.id})
			
		if data_download == None:
			return OperationStatus(False, f"dataDownload {self.id} not found", 404)

		encodesCreativeWork = data_download.get("encodesCreativeWork")

		# obtain creative work @id 
		if type(encodesCreativeWork) == str:
			creative_work_id = data_download.get("encodesCreativeWork")

		if type(encodesCreativeWork) == dict:
			creative_work_id = encodesCreativeWork.get("@id")

		# Get the creative work 
		creative_work = mongo_collection.find_one({"@id": creative_work_id})
		if creative_work is None:
			return OperationStatus(False, f"creative work {creative_work_id} not found", 404)	

		# update format of creative work	
		self.encodesCreativeWork = {
			"id": creative_work.get("@id"), 
			"@type": creative_work.get("@type"), 
			"name": creative_work.get("name")
		}


		insert_result = mongo_collection.insert_one(self.dict(by_alias=True))

		
		# TODO change file upload path
		upload_path = f"{dataset_name}/{self.name}"
		
		# TODO run sha256 as a background task
		# create sha256 for object
		
		# upload object to minio
		try:
			upload_operation = MinioClient.put_object(
				bucket_name = MINIO_BUCKET,
				object_name = upload_path,
				data=Object.file,
				length=-1,
				part_size=10*1024*1024,
				#metadata={"@id": self.id, "name": self.name}
				)

			# TODO check output of upload operation more thoroughly
			if upload_operation == None:
				return OperationStatus(False, "minio error: upload failed", 500)

			# get the size of the file from the stats
			result_stats = MinioClient.stat_object(
				bucket_name = MINIO_BUCKET,
				object_name = upload_path
			)

		# TODO handle minio errors
		except Exception as minio_err:
			return OperationStatus(False, f"minio error: {minio_err}", 500)


		# update the download metadata 
		update_download_result = mongo_collection.update_one(
			{"@id": self.id}, 
			{ "$set": {
				"contentUrl": upload_path,
				"uploadDate": str(result_stats.last_modified),
				"version": version,
				"contentSize": result_stats.size,
			}},	
			session = session
			),

		# update the dataset metadata
		update_dataset_result = mongo_collection.update_one(
			{
				"@id": dataset_id, 
				"distribution": { "$elemMatch": {"@id": self.id}} 
				}, 
			{"$set": {"distribution.$.contentUrl": upload_path}},
			session = session
			)

		# TODO check update results

		return OperationStatus(True, "", 201)


	def delete(self, MongoCollection: pymongo.collection.Collection, MinioClient) -> OperationStatus:
		"""
		removes the contentUrl property from the object, and deletes the file from minio
		"""

		# get metadata record
		read_status = self.super(MongoCollection).read()

		if read_status.success != True:
			return read_status


		bulk_update = [ 
			# TODO: update the metadata for the dataset record, i.e. status property for deleted versions
			# update the metadata for the download record
			pymongo.UpdateOne({"@id": self.id}, {"contentUrl": ""})
		]

		# run the bulk update
		try:
			bulk_write_result = MongoCollection.bulk_write(bulk_update)
		except pymongo.errors.BulkWriteError as bwe:
			return OperationStatus(False, f"mongo error: bulk write error {bwe}", 500)

		# remove the object from minio	
		delete_object = MinioClient.remove_object(MINIO_BUCKET, self.contentUrl)

		# TODO: determine when minio client fails to remove an object and handle those cases

		return OperationStatus(True, "", 200)


	def read_metadata(self, MongoCollection: pymongo.collection.Collection) -> OperationStatus:
		return self.read(MongoCollection)


	def read_object(self, MinioClient):
		"""
		reads the object and returns a file reader from the minio client	
		"""

		# lookup the url
		if self.contentUrl == "":
			return OperationStatus(False, "download has no contentUrl", 404)

		with MinioClient.get_object(MINIO_BUCKET, self.contentUrl) as minio_object:
			yield from minio_object




	def update_new_version(self, object, MongoCollection: pymongo.collection.Collection, MinioClient):
		pass


	def update_metadata(self, MongoCollection: pymongo.collection.Collection):
		pass


def list_downloads(MongoCollection):
	"""
	given a dataset list all versions of a download	
	"""
	pass
