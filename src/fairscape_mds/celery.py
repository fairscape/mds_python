from celery import Celery
import logging
import sys
from pydantic import BaseModel, Field
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.models.rocrate import (
    UploadExtractedCrate,
    UploadZippedCrate,
    DeleteExtractedCrate,
    GetMetadataFromCrate,
    ListROCrates,
    StreamZippedROCrate,
    GetROCrateMetadata,
    PublishROCrateMetadata,
    PublishProvMetadata,
    ROCrate,
    ROCrateDistribution
)

from typing import List, Dict
from uuid import UUID, uuid4

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
backgroundTaskLogger = logging.getLogger("backgroundTaskLogger")


fairscapeConfig = get_fairscape_config()
brokerURL = fairscapeConfig.redis.getBrokerURL()

mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
rocrateCollection = mongoDB[fairscapeConfig.mongo.rocrate_collection]
identifierCollection = mongoDB[fairscapeConfig.mongo.identifier_collection]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]

minioConfig= fairscapeConfig.minio
minioClient = fairscapeConfig.CreateMinioClient()


celeryApp = Celery()
celeryApp.conf.broker_url = brokerURL

class ROCrateUploadJob(BaseModel):
    uid: UUID = Field(default_factory= uuid4)
    status: str = 'in progress'
    filePath: str
    processedFiles: List[str] = Field(default=[])
    identifiersMinted: List[str] = Field(default=[])
    errors: List[str] = Field(default=[])
    completed: bool = Field(default=False)



@celeryApp.task
def celeryRegisterROCrate(transactionFolder: str, filePath: str):

    ''' Task of Unzipping Crate, Processing all metadata and Minting Individual Identifiers
    '''

    backgroundTaskLogger.info(
            f"transaction: {str(transactionFolder)}\tmessage: init background rocrate processing"
            )

    try:
        objectResponse = minioClient.get_object(
            bucket_name=fairscapeConfig.minio.rocrate_bucket, 
            object_name=filePath
            ).read()
        zippedContent = objectResponse.read()

    except Exception as minioException:
        # TODO abort the job
        backgroundTaskLogger.error(
                f"transaction: {str(transactionFolder)}" +
                "\tmessage: failed to read minio object" + f"\terror: {str(minioException)}"
                )
        pass

    finally:
        objectResponse.close()
        objectResponse.release_conn()


    backgroundTaskLogger.info(
            f"transaction: {str(transactionFolder)}\tmessage: read zipped rocrate object from minio"
            )
    
    # upload extracted crate to minio
    extractStatus, extractedFileList = UploadExtractedCrate(
            minioClient,
            zippedContent,
            fairscapeConfig.minio.default_bucket,
            transactionFolder
            )

    if !extractStatus.success:
        backgroundTaskLogger.error(
            f"transaction: {str(transactionFolder)}" +
            "\tmessage: uploaded extracted rocrate to minio" +
            f"\terror: {extractStatus.message}"
            )
        # TODO abort the job
        pass


    backgroundTaskLogger.info(
            f"transaction: {str(transactionFolder)}\tmessage: uploaded extracted rocrate to minio"
            )

    crateDistribution = ROCrateDistribution(
        extractedROCrateBucket = fairscapeConfig.minio.default_bucket,
        archivedROCrateBucket = fairscapeConfig.minio.rocrate_bucket,
        extractedObjectPath = extractedFileList,
        archivedObjectPath =  filePath   
        )

    # validate metadata
    try:
        crate = GetMetadataFromCrate(
            MinioClient=minioClient, 
            BucketName=fairscapeConfig.minio.default_bucket,
            TransactionFolder=transaction_folder,
            CratePath=zip_foldername, 
            Distribution = crateDistribution
            )
    except Exception as e:
        backgroundTaskLogger.error(
                f"transaction: {str(transactionFolder)}\t" +
                "message: error retreiving rocrate metadata from crate"
                )
        # TODO kill the task
        pass


    backgroundTaskLogger.info(
            f"transaction: {str(transactionFolder)}\t" +
            "message: read metadata from rocrate"
            )

    # mint identifiers
    provMetadataMinted = PublishProvMetadata(crate, identifierCollection)

    if !provMetadataMinted:
        backgroundTaskLogger.error(
                f"transaction: {str(transactionFolder)}\t" +
                "message: error minting prov identifiers"
                )
        # TODO kill the task
        pass
    else: 
        backgroundTaskLogger.info(
                f"transaction: {str(transactionFolder)}\t" +
                "message: published prov metadata"
                )


    rocrateMetadataMinted = PublishROCrateMetadata(crate, rocrateCollection)

    if !rocrateMetadataMinted:
        backgroundTaskLogger.error(
                f"transaction: {str(transactionFolder)}\t" +
                "message: error minting rocrate identifiers"
                )
        # TODO kill the task
        pass
    else: 
        backgroundTaskLogger.info(
                f"transaction: {str(transactionFolder)}\t" +
                "message: published rocrate metadata"
                )

    backgroundTaskLogger.info(
            f"transaction: {str(transactionFolder)}\t" +
            "message: task succeeded"
            )
    
    # TODO mark task as sucessfull
    pass



if __name__ == '__main__':
    args = ['worker', '--loglevel=INFO']
    app.worker_main(argv=args)

