from typing_extensions import Annotated

from fastapi import (
    APIRouter,
    Path,
    Header,
    Depends
)
from fastapi.responses import JSONResponse

from fairscape_mds.mds.config import (
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
    CasbinConfig
) 

import logging
import sys


# setup logger for minio operations
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
rocrate_logger = logging.getLogger("rocrate")

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
def resolve(
    NAAN: Annotated[str, Path(
        title="ARK Name Assigning Authority Number",
        # TODO import ark NAAN from config
        default = "59852",
        )], 
    postfix: Annotated[str, Path(
        title="Persitant Identifier"
        )]
    ):
    """ Resolve Identifier Metadata and Return in JSON-LD
    """

    # TODO validate NAAN is 5 digits

    # TODO validate that NAAN is configured

    # TODO if not a local NAAN redirect to n2t.net

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.identifier_collection]

    ark_metadata = mongo_collection.find_one(
        {"@id": f"ark:{NAAN}/{postfix}"}, 
        projection={"_id": 0, "@graph._id": 0}
        )


    if ark_metadata == {} or ark_metadata is None:
        return JSONResponse(
            {
                "@id": f"ark:{NAAN}/{postfix}",
                "error": "ark not found",
                "status_code": 404
            }, 
            status_code=404, 
        )

    else:
        try:
            # TODO normalize all arks into full urls
            return JSONResponse(
                ark_metadata,
                status_code=200
            )

        except Exception as e:
            return JSONResponse(
                {
                    "error": "error returning ark metadata",
                    "message": f"{str(e)}",
                    "identifier": f"ark:{NAAN}/{postfix}",
                    "metadata": str(ark_metadata)
                    },
                status_code=500
            )
