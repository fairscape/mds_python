from fastapi import APIRouter, UploadFile, Form, File
from fastapi.responses import JSONResponse
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION
from pydantic import ValidationError
from mds.database import minio, mongo
from mds.models.rocrate import ROCrate
from mds.utilities.funcs import to_str
from mds.utilities.utils import get_file_from_zip
import zipfile

import json

router = APIRouter()




@router.post("/rocrate/publish",
             summary="Validate ROCrate metadata before transfer",
             response_description="The transferred rocrate")
def rocrate_publish(rocrate = Form(...), file: UploadFile = File(...)):
    """
    Create a rocrate with the following properties:

    - **@id**: a unique identifier
    - **@type**: ROCrate
    - **name**: a name- 
    - **isPartOf**: an organization, a project
    - **@graph**: a list of dataset, software, computations
    """

    crate = ROCrate(**json.loads(rocrate))

    minio_client = minio.GetMinioConfig()
    
    registration_status = crate.rocrate_transfer(         
        minio_client, 
        file.file
        )

    if registration_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": crate.guid,
                    "@type": "ROCrate",
                    "name": crate.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=registration_status.status_code,
            content={"error": registration_status.message}
        )
    



@router.post("/rocrate/transfer",
             summary="Transfer a valid ROCrate object",
             response_description="The ROCrate object")
def rocrate_transfer(#rocrate = Form(...), 
                     rocrate : bytes = File(...), 
                     file: UploadFile = File(...)
                     ):
    """
    Create a rocrate with the following properties:

    - **@id**: a unique identifier
    - **@type**: ROCrate
    - **name**: a name
    - **isPartOf**: a project within an organization
    - **@graph**: a list of DatasetContainer, Dataset, Software, Computation
    """

    # TODO: Get back the file of interest from the archived file
    # This will allow us only to use the zip file to read the metadata
    # POST method Parameter rocrate : bytes = File(...) can thus be avoided
    # get_file_from_zip('ro-crate-metadata.json', file.file)

    # Alternative approach by receiving the ro-crate-metadata.json
    # convert bytes received as crate into string
    rocrate_content = to_str(rocrate)
    
    
    try:
        # parse and instantiate the ro-crate-metadata.json
        rocrate = ROCrate(**json.loads(rocrate_content))    
    except ValidationError as e:
        print(e)
    
    
    mongo_client = mongo.GetConfig()
    minio_client = minio.GetMinioConfig()
    
    transfer_status = rocrate.attempt_transfer(   
        mongo_client,      
        minio_client, 
        file.file
        )
    
    mongo_client.close()

    if transfer_status.success:
        return JSONResponse(
            status_code=201,
            content={
                "created": {
                    "@id": rocrate.guid,
                    "@type": "ROCrate",
                    "name": rocrate.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=transfer_status.status_code,
            content={"error": transfer_status.message}
        )