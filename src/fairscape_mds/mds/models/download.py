from typing import Optional, Union, Literal
from datetime import datetime
from pydantic import (
    Extra,
    Field,
    constr
)
from bson import SON
from fastapi.encoders import jsonable_encoder
import pymongo

from fairscape_mds.mds.models.fairscape_base import (
    FairscapeBaseModel,
    IdentifierPattern
)
from fairscape_mds.mds.models.dataset import Dataset
from fairscape_mds.mds.utilities.operation_status import OperationStatus

from fairscape_mds.mds.config import (
        get_minio_config,
        get_mongo_config,
)


class Download(FairscapeBaseModel, extra=Extra.allow):
    context: dict = Field(
        default={
            "@vocab": "https://schema.org/", 
            "evi": "https://w3id.org/EVI#"
        },
        alias="@context"
    )
    metadataType: Literal['evi:DataDownload'] = Field(alias="@type")
    encodingFormat: str
    owner: constr(pattern=IdentifierPattern) = Field(...)
    contentSize: Optional[int]
    contentUrl: Optional[str]
    encodesCreativeWork: constr(pattern=IdentifierPattern) = Field(...)
    sha256: Optional[str]
    uploadDate: Optional[datetime] = Field(default_factory=datetime.now)
    version: Optional[str] = Field(default="0.1.0")
    sourceOrganization: Optional[constr(pattern=IdentifierPattern)] = Field(default=None)
    includedInDataCatalog: Optional[constr(pattern=IdentifierPattern)] = Field(default=None)


    def create_metadata(self, MongoClient: pymongo.MongoClient) -> OperationStatus: 

        mongo_config = get_mongo_config()
        mongo_database = MongoClient[mongo_config.db]
        mongo_collection = mongo_database[mongo_config.identifier_collection]

        # check that the data download doesn't already exist
        if mongo_collection.find_one({"@id": self.guid}) != None:
            return OperationStatus(False, f"dataDownload {self.guid} already exists", 404)

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
        # self.encodesCreativeWork = {
        #     "id": creative_work.get("@id"),
        #     "@type": creative_work.get("@type"),
        #     "name": creative_work.get("name")
        # } breaks validation

        self.contentUrl = f"{creative_work.get('name')}/{self.name}"

        # TODO check success of operation
        insert_result = mongo_collection.insert_one(self.dict(by_alias=True))

        # TODO check success of operation
        update_result = mongo_collection.update_one(
            {"@id": creative_work.get("@id")},
            {"$addToSet": {
                "distribution": SON(
                    [("@id", self.guid), ("@type", "DataDownload"), ("name", self.name), ("contentUrl", "")])}
            })

        return OperationStatus(True, "", 201)


    def register(self, MongoClient: pymongo.MongoClient, MinioClient, Object) -> OperationStatus:
        """
        uploads the file and ammends the dataDownload metadata and dataset metadata
        """

        mongo_config = get_mongo_config()
        minio_config = get_minio_config()

        mongo_database = MongoClient[mongo_config.db]
        mongo_collection = mongo_database[mongo_config.identifier_collection]

        # check that the data download doesn't already exist
        if mongo_collection.find_one({"@id": self.guid}) != None:
            return OperationStatus(False, f"dataDownload {self.guid} already exists", 404)

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
        # self.encodesCreativeWork = {
        #     "id": creative_work.get("@id"),
        #     "@type": creative_work.get("@type"),
        #     "name": creative_work.get("name")
        # } Does not match schmea of thing

        # TODO format the contentUrl
        #prefix, org, proj, creative_work_id, identifier  = self.guid.split("/")

        #self.contentUrl = f"{org}/{proj}/{creative_work_id}/{self.name}"

        # TODO check success of operation
        insert_result = mongo_collection.insert_one(self.dict(by_alias=True))

        # TODO check success of operation
        update_result = mongo_collection.update_one(
            {"@id": creative_work.get("@id")},
            {"$addToSet": {
                "distribution": SON(
                    [("@id", self.guid), ("@type", "DataDownload"), ("name", self.name), ("contentUrl", "")])}
            })

        # TODO run sha256 as a background task
        # create sha256 for object

        # upload object to minio
        try:
            upload_operation = MinioClient.put_object(
                bucket_name=minio_config.default_bucket,
                object_name=self.contentUrl,
                data=Object,
                length=-1,
                part_size=10 * 1024 * 1024,
                #metadata={"identifier": self.guid, "name": self.name}
            )

            # get the size of the file from the stats
            result_stats = MinioClient.stat_object(
                bucket_name=minio_config.default_bucket,
                object_name=self.contentUrl
            )

            # update the download metadata
            update_download_result = mongo_collection.update_one(
                {"@id": self.guid},
                {"$set": {
                    "uploadDate": str(result_stats.last_modified),
                    "contentSize": result_stats.size,
                }}
            )

            # update the dataset metadata
            update_dataset_result = mongo_collection.update_one(
                {
                    "@id": creative_work.get("@id"),
                    "distribution": {"$elemMatch": {"@id": self.guid}}
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
        mongo_config = get_mongo_config()
        minio_config = get_minio_config()

        mongo_database = MongoClient[mongo_config.db]
        mongo_collection = mongo_database[mongo_config.identifier_collection]

        with MongoClient.start_session(causal_consistency=True) as session:

            # check that the data download metadata record exists
            data_download = mongo_collection.find_one({"@id": self.guid}, session=session)

            if data_download == None:
                return OperationStatus(False, f"dataDownload {self.guid} not found", 404)

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
                    bucket_name=minio_config.default_bucket,
                    object_name=upload_path,
                    data=Object.file,
                    length=-1,
                    part_size=10 * 1024 * 1024,
                    # metadata={"@id": self.guid, "name": self.name}
                )

                # TODO check output of upload operation more thoroughly
                if upload_operation == None:
                    return OperationStatus(False, "minio error: upload failed", 500)

                # get the size of the file from the stats
                result_stats = MinioClient.stat_object(
                    bucket_name=minio_config.default_bucket,
                    object_name=upload_path
                )

            # TODO handle minio errors
            except Exception as minio_err:

                mongo_collection.delete_one({"@id": self.guid})
                mongo_collection.update_one({"$pull": {"distribution": {"@id": self.guid}}})
                return OperationStatus(False, f"minio error: {minio_err}", 500)

            # update the download metadata
            update_download_result = mongo_collection.update_one(
                {"@id": self.guid},
                {"$set": {
                    "contentUrl": upload_path,
                    "uploadDate": str(result_stats.last_modified),
                    "version": version,
                    "contentSize": result_stats.size,
                }},
                session=session
            ),

            # update the dataset metadata
            update_dataset_result = mongo_collection.update_one(
                {
                    "@id": dataset_id,
                    "distribution": {"$elemMatch": {"@id": self.guid}}
                },
                {"$set": {"distribution.$.contentUrl": upload_path}},
                session=session
            )

            # TODO check update results

        return OperationStatus(True, "", 201)


    def delete(self, MongoClient: pymongo.MongoClient, MinioClient) -> OperationStatus:
        """
        removes the contentUrl property from the object, and deletes the file from minio
        """

        mongo_config = get_mongo_config()
        minio_config = get_minio_config()

        mongo_database = MongoClient[mongo_config.db]
        mongo_collection = mongo_database[mongo_config.identifier_collection]

        # get metadata record
        read_status = self.super(mongo_collection).read()

        if read_status.success != True:
            return read_status

        bulk_update = [
            # TODO: update the metadata for the dataset record, i.e. status property for deleted versions
            # update the metadata for the download record
            pymongo.UpdateOne({"@id": self.guid}, {"contentUrl": ""})
        ]

        # run the bulk update
        try:
            bulk_write_result = mongo_collection.bulk_write(bulk_update)
        except pymongo.errors.BulkWriteError as bwe:
            return OperationStatus(False, f"mongo error: bulk write error {bwe}", 500)

        # remove the object from minio
        delete_object = MinioClient.remove_object(minio_config.default_bucket, self.contentUrl)

        # TODO: determine when minio client fails to remove an object and handle those cases

        return OperationStatus(True, "", 200)


    def read_metadata(self, MongoClient: pymongo.MongoClient) -> OperationStatus:
        mongo_config = get_mongo_config()
        minio_config = get_minio_config()

        mongo_db = MongoClient[mongo_config.db]
        mongo_collection = mongo_db[mongo_config.identifier_collection]
        return self.read(mongo_collection)


    def read_object(self, MinioClient):
        """
        reads the object and returns a file reader from the minio client
        """

        minio_config = get_minio_config()
        # lookup the url
        if self.contentUrl == "":
            return OperationStatus(False, "download has no contentUrl", 404)

        with MinioClient.get_object(minio_config.default_bucket, self.contentUrl) as minio_object:
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
