from typing_extensions import Annotated

from fastapi import (
    APIRouter,
    Header,
    Depends
)
from fastapi.responses import JSONResponse

from mds.config import (
    get_minio_config,
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
    CasbinConfig
) 

ResolverRouter = APIRouter()

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

casbin_enforcer = get_casbin_enforcer()
casbin_enforcer.load_policy()
casbin_enforcer.load_policy()

@ResolverRouter.get(
    "/ark:{NAAN}/{postfix}",
    summary="Retrieve metadata for a specified ARK",
    response_description="ARK metadata"
)
def resolve(NAAN: str, postfix: str):
    """ Resolve Identifier Metadata and Return in JSON-LD
    """

    # TODO validate NAAN is 5 digits

    # TODO validate that NAAN is configured

    # TODO if not a local NAAN redirect to n2t.net

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    ark_metadata = mongo_collection.find_one({"@id": f"ark:{NAAN}/{postfix}"})

    if ark_metadata == {}:
        return JSONResponse(
            {
                "@id": "ark:{NAAN}/{postfix}",
                "error": "ark not found",
                "status_code": 404
            }, 
            status_code=404, 
        )

    else:

        # TODO normalize all arks into full urls

        return JSONResponse(
            ark_metadata,
            status_code=200
        )
