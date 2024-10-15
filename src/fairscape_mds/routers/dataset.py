from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import JSONResponse

from fairscape_mds.config import (
        get_fairscape_config,
        get_mongo_client
) 

from fairscape_mds.models.dataset import (
    DatasetCreateModel, 
    DatasetWriteModel,
    DatasetUpdateModel,
    listDatasets, 
    deleteDataset, 
    createDataset, 
)
from fairscape_mds.models.acl import Permissions
from typing import Annotated, Optional
from fairscape_mds.models.user import UserLDAP
from fairscape_mds.auth.oauth import getCurrentUser

router = APIRouter()

fairscapeConfig = get_fairscape_config()
mongo_client = get_mongo_client()
mongo_db = mongo_client[fairscapeConfig.mongo.db]
identifierCollection = mongo_db[fairscapeConfig.mongo.identifier_collection]
userCollection = mongo_db[fairscapeConfig.mongo.user_collection]


@router.post(
     "/dataset",
    summary="Create a dataset",
    response_description="The created dataset"
)
def dataset_create(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    datasetMetadata: DatasetCreateModel,
    datasetFile: Optional[UploadFile]
    ):
    """
    API endpoint to create a dataset record in fairscape, optionally uploading a file

    """


    datasetPermissions = Permissions(
            owner= currentUser.dn,
            group=currentUser.memberOf[0]
            )
   
    distributionMetadata = []

    if datasetMetadata.contentURL:
        distributionMetadata.append(DatasetDistribution(
            distributionType= DistributionTypeEnum.URL,
            distribution=URLDistribution(uri=datasetMetadata.contentURL)
            ))

    # if a file is provided from user
    if datasetFile:
        minioPath = "f{currentUser.cn}/datasets/{datasetMetadata.guid}/{datasetFile.filename}"
        try:
            # upload the object to minio
            uploadOperation = minioClient.put_object(
                bucket_name=fairscapeConfig.minio.default_bucket,
                object_name=minioPath,
                data=datasetFile.file,
                length=-1,
                part_size=10 * 1024 * 1024,
                )

            # get the size of the file from the stats
            resultStats = minioClient.stat_object(
                bucket_name=minioConfig.default_bucket,
                object_name=minioPath
            )

            # set the distribution metadata
            distributionMetadata.append(DatasetDistribution(
                    distributionType= DistributionTypeEnum.minio,
                    distribution=MinioDistribution(path=minioPath)
                    ))

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": "error minting identifier", "message": str(e)}
            )

    datasetWrite = DatasetWriteModel(
            distribution = distributionMetadata,
            published = True,
            permissions = datasetPermissions,
            **datasetMetadata
            )

    datasetJSON = datasetWrite.model_dump(by_alias=True)
    insertResponse = identifierCollection.insertOne(datasetJSON)
    
    if insertResponse.inserted_id is None:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": "error minting identifier"}
        )

    else: 
        return JSONResponse(
            status_code=201,
            content={"created": {"@id": datasetMetadata.guid, "@type": "evi:Dataset", "name": datasetMetadata.name}}
        )

    



@router.get("/dataset",
            summary="List all datasets",
            response_description="Retrieved list of datasets")
def dataset_list(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    ):
    datasets = listDatasets(identifierCollection)
    return datasets


@router.get("/dataset/download/ark:{NAAN}/{postfix}")
def download_dataset(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    NAAN: str,
    postfix: str
    ):
    pass

@router.get("/dataset/ark:{NAAN}/{postfix}",
            summary="Retrieve a dataset",
            response_description="The retrieved dataset")
def dataset_get(NAAN: str, postfix: str):
    """
    Retrieves a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    datasetGUID = f"ark:{NAAN}/{postfix}"

    dataset = Dataset.construct(guid=datasetGUID)
    read_status = dataset.read(identifier_collection)

    if read_status.success:
        return dataset
    else:
        return JSONResponse(
            status_code=read_status.status_code,
            content={"error": read_status.message}
        )


@router.put("/dataset/ark:{NAAN}/{postfix}",
            summary="Update a dataset",
            response_description="The updated dataset")
def dataset_update(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    NAAN: str,
    postfix: str,
    datasetUpdateInstance: DatasetUpdateModel,
    ):

    datasetGUID = f"ark:{NAAN}/{postfix}"

    updateStatus = updateDataset(currentUser, datasetGUID, datasetUpdateInstance, identifier_collection)


    if updateStatus.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": dataset.id, "@type": "evi:Dataset"}}
        )
    else:
        return JSONResponse(
            status_code=updateStatus.status_code,
            content={"error": updateStatus.message}
        )


@router.delete("/dataset/ark:{NAAN}/{postfix}",
    summary="Delete a dataset",
    response_description="The deleted dataset")
def dataset_delete(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    NAAN: str, 
    postfix: str
    ):
    """
    Deletes a dataset based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    datasetGUID = f"ark:{NAAN}/{postfix}"

    datasetMetadata, deleteStatus = deleteDataset(
            currentUser,
            datasetGUID,
            identifier_collection,
            user_collection
            )

    if deleteStatus.success:
        return JSONResponse(
            status_code=200,
            content={
                "deleted": datasetMetadata.model_dump(by_alias=True, include=['guid', 'name', 'description', 'metadataType'])
                }
        )

    else:
        return JSONResponse(
            status_code=deleteStatus.status_code,
            content={"error": f"{str(deleteStatus.message)}"}
        )
