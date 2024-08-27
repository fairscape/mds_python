from celery import Celery
import logging
import sys
import pathlib
import io
import datetime
import re
from pathlib import Path


# temporary fix for importing module problems
# TODO change background tasks to module
pathRoot = pathlib.Path(__file__).parents[1]
sys.path.append(str(pathRoot))

from pydantic import BaseModel, Field
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.models.user import UserLDAP
from fairscape_mds.models.dataset import DatasetDistribution, MinioDistribution
from fairscape_mds.models.rocrate import (
    ExtractCrate,
    PublishMetadata,
    DeleteExtractedCrate,
    GetMetadataFromCrate,
    StreamZippedROCrate,
    ROCrate,
    ROCrateDistribution
)
from fairscape_mds.auth.oauth import getUserByCN

from typing import List, Dict, Optional
from uuid import UUID, uuid4


# setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
backgroundTaskLogger = logging.getLogger("workerLogger")

# setup clients
fairscapeConfig = get_fairscape_config()
brokerURL = fairscapeConfig.redis.getBrokerURL()

mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
rocrateCollection = mongoDB[fairscapeConfig.mongo.rocrate_collection]
identifierCollection = mongoDB[fairscapeConfig.mongo.identifier_collection]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]
asyncCollection = mongoDB[fairscapeConfig.mongo.async_collection]

minioConfig= fairscapeConfig.minio
minioClient = fairscapeConfig.CreateMinioClient()

celeryApp = Celery()
celeryApp.conf.broker_url = brokerURL

def serializeTimestamp(time):
    if time:
        return time.timestamp()
    else:
        return None

class ROCrateUploadJob(BaseModel):
    userCN: str
    transactionFolder: str
    zippedCratePath: str
    timeStarted: datetime.datetime | None = Field(default=None)
    timeFinished: datetime.datetime | None = Field(default=None)
    status: Optional[str] = Field(default='in progress')
    completed: Optional[bool] = Field(default=False)
    success: Optional[bool] = Field(default=False)
    processedFiles: List[str] = Field(default=[])
    identifiersMinted: List[str] = Field(default=[])
    error: str | None = Field(default=None)


def createUploadJob(
        userCN: str,
        transactionFolder: str, 
        zippedCratePath: str,
        ):
    ''' Insert a record into mongo for the submission of a job.

    Keyword arguments:
    transactionFolder -- (str) the UUID representing the unique path in minio
    zippedCratePath   -- (str) the filename of the zipped crate contents
    '''

    # setup job model
    uploadJobInstance = ROCrateUploadJob(
        userCN = userCN,
        transactionFolder=transactionFolder,
        zippedCratePath=zippedCratePath,
        timeStarted= datetime.datetime.now(tz=datetime.timezone.utc),
    )

    insertResult = asyncCollection.insert_one(
            uploadJobInstance.model_dump()
            )

    return uploadJobInstance 


def getUploadJob(
        transactionFolder: str,
    ):
    ''' Return a upload Job record from mongo by the job UUID generated by celery.

    Keyword arguments:
    transactionFolder -- (str) the UUID representing the unique path in minio
    zippedCratePath   -- (str) the filename of the zipped crate contents
    '''

    jobMetadata = asyncCollection.find_one(
        {"transactionFolder": transactionFolder},
        { "_id": 0}
    )

    if jobMetadata:
        return ROCrateUploadJob.model_validate(jobMetadata)
    else:
        return None


def updateUploadJob(transactionFolder: str, update: Dict):
    ''' Update async job using the transactionFolder as the primary key

    Keyword arguments:
    transactionFolder -- (str) the UUID representing the job
    update            -- (Dict) the update representing the dictionary
    '''

    # update job with extracted status status
    asyncCollection.update_one(
            {
                "transactionFolder": transactionFolder,
                }, 
            {"$set": update}
            )

@celeryApp.task(name='async-register-ro-crate')
def AsyncRegisterROCrate(userCN: str, transactionFolder: str, filePath: str):
    """
    Background task for processing Zipped ROCrates.
    :param str userCN: Current User's CN uploading the ROCrate
    :param str transactionFolder: UUID folder representing the unique path in minio
    :param str filePath: The filename of the zipped crate contents
    """
    # connect to ldap
    ldapConnection = fairscapeConfig.ldap.connectAdmin()
    currentUser = getUserByCN(ldapConnection, userCN)
    ldapConnection.unbind()

    try:
        objectResponse = minioClient.get_object(
            bucket_name=fairscapeConfig.minio.rocrate_bucket, 
            object_name=filePath
        )
        zippedContent = objectResponse.read()
    except Exception as minioException:
        backgroundTaskLogger.error(
            f"transaction: {str(transactionFolder)}" +
            "\tmessage: failed to read minio object" + f"\terror: {str(minioException)}"
        )
        updateUploadJob(
            transactionFolder, 
            {
                "completed": True,
                "success": False,
                "error": f"Failed to read minio Object \terror: {str(minioException)}"
            }
        )
        return False
    finally:
        objectResponse.close()
        objectResponse.release_conn()

    # extracting crate from path
    roCrateMetadata = ExtractCrate(
        minioClient=minioClient,
        bucketName=fairscapeConfig.minio.default_bucket,
        bucketRootPath=fairscapeConfig.minio.default_bucket_path,
        currentUser=currentUser,
        transactionFolder=transactionFolder,
        zippedObject=io.BytesIO(zippedContent)
    )

    # update the uploadJob record
    if roCrateMetadata is None:
        updateUploadJob(
            transactionFolder,
            {
                "completed": True,
                "success": False,
                "error": "error reading ro-crate-metadata"
            }
        )
        return False

    # Add distribution information if not present
    if 'distribution' not in roCrateMetadata:
        crate_name = Path(filePath).stem  # Get filename without extension
        zip_bucket = fairscapeConfig.minio.rocrate_bucket
        object_path = f"{transactionFolder}/{crate_name}"

        roCrateMetadata['distribution'] = {
            "extractedROCrateBucket": fairscapeConfig.minio.default_bucket,
            "archivedROCrateBucket": zip_bucket,
            "extractedObjectPath": [f"{object_path}/{file}" for file in roCrateMetadata.get('hasPart', [])],
            "archivedObjectPath": filePath
        }
        roCrateMetadata['contentURL'] = f"s3a://{zip_bucket}/{object_path}.zip"

    updateUploadJob(
        transactionFolder,
        {"status": "minting identifiers"}
    )

    publishMetadata = PublishMetadata(
        currentUser=currentUser,
        rocrateJSON=roCrateMetadata,
        transactionFolder=transactionFolder,
        rocrateCollection=rocrateCollection,
        identifierCollection=identifierCollection,
    )

    if publishMetadata is None:
        updateUploadJob(
            transactionFolder,
            {
                "status": "Failed",
                "timeFinished": datetime.datetime.now(tz=datetime.timezone.utc),
                "completed": True,
                "success": False,
            }
        )
        return False
    else:
        backgroundTaskLogger.info(
            f"transaction: {str(transactionFolder)}\t" +
            "message: task succeeded"
        )
        updateUploadJob(
            transactionFolder,
            {
                "status": "Finished",
                "timeFinished": datetime.datetime.now(tz=datetime.timezone.utc),
                "completed": True,
                "success": True,
                "identifiersMinted": publishMetadata
            }
        )
        return True


 



if __name__ == '__main__':
    args = ['worker', '--loglevel=INFO']
    celeryApp.worker_main(argv=args)

