from fastapi import APIRouter, UploadFile, Form, File
from fastapi.responses import JSONResponse
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION

from mds.database import minio
from mds.models.rocrate import ROCrate


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