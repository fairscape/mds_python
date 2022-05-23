from typing import Optional
from datetime import datetime
from pydantic import Extra
from bson import SON
import pymongo

from mds.models.fairscape_base import FairscapeBaseModel
from mds.models.dataset import Dataset
from mds.models.compact.dataset import DatasetCompactView
from mds.utilities.operation_status import OperationStatus

from mds.database.config import MINIO_BUCKET
from minio.error import ResponseError


class Download(FairscapeBaseModel, extra=Extra.allow):
	context = {"@vocab": "https://schema.org/", "evi": "https://w3id/EVI#"}
	type = "DataDownload"
	encodingFormat: str
	contentSize: Optional[str]
	contentUrl: Optional[str]
	encodesCreativeWork: Optional[DatasetCompactView]
	sha256: Optional[str]
	uploadDate: Optional[datetime]
	version: Optional[str]
	# status: str


	def create_metadata(self, DatasetId: str, MongoCollection: pymongo.collection.Collection) -> OperationStatus:

		if self.version == None:
			# create versioning
			self.version = "1.0"

		# check that dataset exists
		dataset = Dataset.construct(id=DatasetId)
		dataset_read_status = dataset.read(MongoCollection)

		if dataset_read_status.status != True:
			# TODO make a more informative error message
			return dataset_read_status

		# update the encodesCreativeWork property with a DatasetCompactView
		self.encodesCreativeWork = DatasetCompactView(id=dataset.id, type="Dataset", name=dataset.name)

		create_download_bulk_write = [
			# update the dataset containing this download
			pymongo.UpdateOne(
				{"@id": dataset.id}, 
				{"$push" : { 
					"distribution": SON([("@id", self.id), ("@type", "DataDownload"), ("name", self.name)])}
				}),

			# create metadata record in mongo
			pymongo.InsertOne(self.json(by_alias=True))
		]

		try:
			bulk_write_result = MongoCollection.bulk_write(create_download_bulk_write)
		except Exception as bwe:
			return OperationStatus(False, f"create download error: {bwe}", 500)

		if bulk_write_result.inserted_count != 1:
			return OperationStatus(False, "create download error: {bulk_write_result.bulk_api_result}", 500)

		return OperationStatus(True, "", 201)


	def create_upload(self, Object, MongoCollection: pymongo.collection.Collection, MinioClient) -> OperationStatus:
		"""
		uploads the file and ammends the dataDownload metadata and dataset metadata
		"""

		# TODO change file upload path
		upload_path = f"{self.encodesCreativeWork.name}/{self.name}"

		# check that the data download metadata record exists
		read_status = self.read(MongoCollection)

		if read_status.success != True:
			return read_status

		# TODO run sha256 as a background task
		# create sha256 for object
				
		
		# upload object to minio
		try:
			upload_operation = MinioClient(
				bucket_name = MINIO_BUCKET,
				object_name = upload_path,
				data=Object,
				metadata={"@id": self.id, "name": self.name}
				)

			# TODO check output of upload operation more thoroughly
			if upload_operation == None:
				return OperationStatus(False, "minio error: upload failed", 500)

		except ResponseError as minio_err:
			return OperationStatus(False, f"minio error: {minio_err}", 500)


		# update mongo 
		bulk_update = [
			# update the download metadata 
			pymongo.UpdateOne(
				{"@id": self.id}, 
				{
					"contentUrl": upload_path,
					"uploadDate": datetime.now(),
					"version": self.version,
					"contentSize": str(len(Object))
				}
				),

			# update the dataset metadata
			pymongo.UpdateOne(
				{"@id": self.encodesCreativeWork.id, "distribution": {"@id": self.id}}, 
				{"$set": {"distribution.$.contentUrl": upload_path}}	
				)
		]

		# run the bulk update
		try:
			bulk_write_result = MongoCollection.bulk_write(bulk_update)
		except pymongo.errors.BulkWriteError as bwe:
			return OperationStatus(False, f"mongo error: bulk write error {bwe}", 500)

		# TODO check the bulk_write_result more thoroughly


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
		return self.super(MongoCollection).read()


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