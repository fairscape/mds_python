from typing import Optional
from pydantic import Extra
from mds.models.fairscape_base import FairscapeBaseModel
from mds.models.compact.dataset import DatasetCompactView
from datetime import datetime

class Download(FairscapeBaseModel, extra=Extra.allow):
	context = {"@vocab": "https://schema.org/", "evi": "https://w3id/EVI#"}
	type = "DataDownload"
	contentSize: str
	encodingFormat: str
	contentUrl: Optional[str]
	encodesCreativeWork: DatasetCompactView
	sha256: Optional[str]
	uploadDate: datetime


	def create(self, object, MongoCollection: pymongo.collection.Collection, MinioClient):

		# TODO run sha256 as a background task
		# create sha256 for object


		# create metadata record in mongo


		# upload object to minio


		pass


	def delete(self, MongoCollection: pymongo.collection.Collection, MinioClient):
		pass


	def get_metadata(self):
		pass

	def get_object(self):
		pass

	def update(self, object, MongoCollection: pymongo.collection.Collection, MinioClient):
		pass


def list_downloads(MongoCollection):
	pass