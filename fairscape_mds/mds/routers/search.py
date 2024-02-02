from typing import Annotated
from fastapi import (
    Query
    APIRouter
)
from fastapi.responses import JSONResponse

from fairscape_mds.mds.search.search import (
    SearchRequest
)
from fairscape_mds.mds.config import (
    get_casbin_enforcer,
    get_mongo_config,
    get_mongo_client,
    MongoConfig,
    CasbinConfig
) 

router = APIRouter()

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

mongo_db = mongo_client[mongo_config.db]
mongo_collection = mongo_db[mongo_config.identifier_collection]

@router.post('/search',
             summary="Search for Identifier",
             response_description="Identifier Metadata that matched the query")
def search_metadata(
    entityType: Annotated[str | None, Query(max_length=50)] = None,
    textSearch: Annotated[str | None, Query(max_length=50)] = None,
    name: Annotated[str | None, Query(max_length=50)] = None,
    description: Annotated[str | None, Query(max_length=50)] = None,
    organization: Annotated[str | None, Query(max_length=50)] = None
    project: Annotated[str | None, Query(max_length=50)] = None
    download_available: Annotated[bool | None, Query(max_length=50)] = None

):


    #entityType: Union[TypeEnum, None] = None
#    textSearch: Optional[str] = None
#    name: Optional[str] = None
#    nameContains: Optional[str] = None
#    descriptionContains: Optional[str] = None
#    isPartOfOrganizationGUID: Optional[str] = None
#    isPartOfProjectGUID: Optional[str] = None
#    isPartOfROCrateGUID: Optional[str] = None
#    dataInFairscape: Optional[bool] = None
#    dataSizeGreaterThan: Optional[int] = None
#    dataSizeLessThan: Optional[int] = None
#    datatype: Optional[str] = None

    search_instance = SearchRequest(
        entityType = entityType,
        textSearch = textSearch,
        name = name,
        descriptionContains= description,
        isPartofOrganizationGUID= organization
        
    )
    

    search_text = search_instance.ReturnQuery()
    


    return {}
