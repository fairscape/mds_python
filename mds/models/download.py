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
from fastapi.encoders import jsonable_encoder

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

    def register(self, mongo_collection: pymongo.collection.Collection, MinioClient, Object) -> OperationStatus:
        """
        uploads the file and ammends the dataDownload metadata and dataset metadata
        """

        # check that the data download doesn't already exist
        if mongo_collection.find_one({"@id": self.id}) != None:
            return OperationStatus(False, f"dataDownload {self.id} already exists", 404)

        # obtain creative work @id
        if type(self.encodesCreativeWork) == str:
            creative_work_id = self.encodesCreativeWork
        else:
            creative_work_id = self.encodesCreativeWork.id

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

        self.contentUrl = f"{creative_work.get('name')}/{self.name}"

        # TODO check success of operation
        insert_result = mongo_collection.insert_one(self.dict(by_alias=True))

        # TODO check success of operation
        update_result = mongo_collection.update_one(
                {"@id": creative_work.get("@id")},
                {"$addToSet" : {
                        "distribution": SON([("@id", self.id), ("@type", "DataDownload"), ("name", self.name), ("contentUrl", "")])}
                })

        # TODO run sha256 as a background task
        # create sha256 for object

        # upload object to minio
        try:
            upload_operation = MinioClient.put_object(
                    bucket_name = MINIO_BUCKET,
                    object_name = self.contentUrl,
                    data=Object,
                    length=-1,
                    part_size=10*1024*1024,
                    metadata={"identifier": self.id, "name": self.name}
                    )

            # get the size of the file from the stats
            result_stats = MinioClient.stat_object(
                    bucket_name = MINIO_BUCKET,
                    object_name = self.contentUrl
            )

            # update the download metadata
            update_download_result = mongo_collection.update_one(
                    {"@id": self.id},
                    { "$set": {
                            "uploadDate": str(result_stats.last_modified),
                            "contentSize": result_stats.size,
                    }}
                    )

            # update the dataset metadata
            update_dataset_result = mongo_collection.update_one(
                    {
                            "@id": creative_work.get("@id"),
                            "distribution": { "$elemMatch": {"@id": self.id}}
                            },
                    {"$set": {"distribution.$.contentUrl": self.contentUrl}}
                    )
        except Exception as e:

            

            return OperationStatus(False, f"exception uploading: {str(e)}", 500)


        return OperationStatus(True, "", 201)


    def create_upload(self, Object, MongoClient: pymongo.MongoClient, MinioClient) -> OperationStatus:
        """
        uploads the file and ammends the dataDownload metadata and dataset metadata
        """
        mongo_database = MongoClient[MONGO_DATABASE]
        mongo_collection = mongo_database[MONGO_COLLECTION]

        with MongoClient.start_session(causal_consistency=True) as session:

            # check that the data download metadata record exists
            data_download = mongo_collection.find_one({"@id": self.id}, session=session)

            if data_download == None:
                return OperationStatus(False, f"dataDownload {self.id} not found", 404)

            # TODO handle when data is persisted incorrectly and return an error
            dataset_id = data_download.get("encodesCreativeWork", {}).get("@id")
            dataset_name = data_download.get("encodesCreativeWork", {}).get("name")

            # update self for returning document
            self.name = data_download.get("name")

            # set version if not set
            if data_download.get("version") != None:
                version = "1.0"
            else:
                version = data_download.get("version")


            # TODO change file upload path
            # TODO check that self.encodesCreativeWork is non empty
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

                mongo_collection.delete_one({"@id": self.id})
                mongo_collection.update_one({"$pull": {"distribution": {"@id": self.id}}})
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
                    )

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


def list_download(MongoCollection):
    """
    given a dataset list all versions of a download
    """
    pass
