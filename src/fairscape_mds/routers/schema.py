from fastapi import APIRouter, Header, Depends
from fastapi.responses import JSONResponse

from fairscape_mds.models.schema import Schema, list_schemas
from fairscape_mds.config import (
    get_fairscape_config,
)

from fairscape_mds.auth.oauth import getCurrentUser
from fairscape_mds.models.user import UserLDAP
from typing_extensions import Annotated

router = APIRouter()

fairscapeConfig = get_fairscape_config()

mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
identifierCollection = mongoDB[fairscapeConfig.mongo.identifier_collection]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]



@router.post('/schema',
             summary="Create a schema",
             response_description="The created schema")
def schema_create(schema: Schema, currentUser: Annotated[UserLDAP, Depends(getCurrentUser)]):
    """
    Create a schema with the following properties:

    - **@context**: the JSON-LD context
    - **@type**: the type of the metadata, typically "evi:Schema"
    - **@id**: a unique identifier for the schema
    - **name**: the name of the schema
    - **description**: a brief description of the schema
    - **properties**: a dictionary mapping property names to their definitions
    - **type**: the type of the schema, usually "object" (optional)
    - **additionalProperties**: whether additional properties are allowed (default: True)
    - **required**: a list of required properties
    - **separator**: the separator used in the schema (default: ",")
    - **header**: whether the schema includes a header (default: False)
    - **examples**: a list of example instances of the schema (optional)
    - **url**: the URL of the schema (optional)
    - **keywords**: a list of keywords associated with the schema (optional)
    - **license**: the license of the schema (optional)
    """

    create_status = schema.create(identifierCollection)

    if create_status.success:
        return JSONResponse(
            status_code=201,
            content={
                'created': {
                    '@id': schema.guid, 
                    '@type': 'evi:Schema', 
                    'name': schema.name
                }
            }
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={'error': create_status.message}
        )


@router.get('/schema', status_code=200,
            summary="List all schemas",
            response_description="Retrieved list of schemas")
def schema_list(
        currentUser: Annotated[UserLDAP, Depends(getCurrentUser)]
    ):
    schemas = list_schemas(identifierCollection)
    return schemas


@router.get("/schema/ark:{NAAN}/{postfix}",
            summary="Retrieve a schema",
            response_description="The retrieved schema")
def schema_get(
        currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
        NAAN: str, 
        postfix: str 
    ):
    """
    Retrieves a schema based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    schema_id = f"ark:{NAAN}/{postfix}"

    schema = Schema.model_construct(guid=schema_id)
    read_status = schema.read(identifierCollection)

    if read_status.success:
        return schema
    else:
        return JSONResponse(
            status_code=read_status.status_code, 
            content={
                "error": read_status.message
            }
        )


@router.put("/schema/ark:{NAAN}/{postfix}",
            summary="Update a schema",
            response_description="The updated schema")
def schema_update(
        currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
        NAAN: str,
        postfix: str,
        schema: Schema
    ):
    
    schema_id = f"ark:{NAAN}/{postfix}"
    schema = Schema.model_construct(guid=schema_id)
    read_status = schema.read(identifierCollection)
    
    if not read_status.success:
        return JSONResponse(
            status_code=read_status.status_code, 
            content={
                "error": read_status.message
            }
        )

    
    update_status = schema.update(identifierCollection)

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": schema.guid, "@type": "Schema", "name": schema.name}}
        )

    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/schema/ark:{NAAN}/{postfix}",
               summary="Delete a schema",
               response_description="The deleted schema")
def schema_delete(
        currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
        NAAN: str, 
        postfix: str
    ):
    """
    Deletes a schema based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    schema_id = f"ark:{NAAN}/{postfix}"

    schema = Schema.model_construct(guid=schema_id)

    delete_status = schema.delete(identifierCollection)

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={
                "deleted": {
                    "@id": schema_id, 
                    "@type": "evi:Schema"
                }
            }
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
