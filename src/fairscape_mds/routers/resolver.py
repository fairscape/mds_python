from fastapi import (
    APIRouter,
    Path,
    Header,
    Depends,
    Request
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse

from fairscape_mds.config import get_fairscape_config
from fairscape_mds.models import (
    User,
    ROCrate,
    Schema,
    DatasetWriteModel,
    Software,
    Computation,
    EvidenceGraph,
    IdentifierPattern
    )


from typing_extensions import Annotated
import sys
import logging
import json
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import re

# setup logger for minio operations
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
rocrate_logger = logging.getLogger("rosolver")

ResolverRouter = APIRouter()

fairscapeConfig = get_fairscape_config()
mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]
identifierCollection = mongoDB[fairscapeConfig.mongo.identifier_collection]
rocrateCollection = mongoDB[fairscapeConfig.mongo.rocrate_collection]
FAIRSCAPE_URL = fairscapeConfig.url

def convert_to_rdf(json_data):  
    """Convert json data to rdf and turtle"""

    data = json.loads(json_data)
    g = Graph()
    ex = Namespace("https://w3id.org/EVI#")

    # Convert JSON data to RDF triples
    for key, value in data.items():
        subject = URIRef(ex["dataset"])
        predicate = URIRef(ex[key])
        if isinstance(value, str):
            obj = Literal(value, datatype=XSD.string)
        elif isinstance(value, int):
            obj = Literal(value, datatype=XSD.integer)
        else:
            obj = Literal(str(value), datatype=XSD.string)
        g.add((subject, predicate, obj))

    rdf_xml_data = g.serialize(format='application/rdf+xml')
    turtle_data = g.serialize(format='turtle')

    return rdf_xml_data, turtle_data

def add_link(value, download = False):
    """For values that match ark or look like urls add a hyperlink"""
    url_pattern = r'^(http|https)://[^\s]+'
    if download:
        return f'<a href={FAIRSCAPE_URL}rocrate/archived/download/{value}>Download Link</a>'
    if re.match(IdentifierPattern, value):
        return f'<a href={FAIRSCAPE_URL}{value}>{value}</a>'
    elif re.match(url_pattern, value):
        return f'<a href="{value}">{value}</a>'
    return value

def find_metadata(collections, naan, postfix):
    """Look for ID in all possible collections return first document."""

    for collection in collections:
        ark_metadata = collection.find_one({"@id": f"ark:{naan}/{postfix}"}, projection={"_id": 0, "@graph._id": 0})
        if ark_metadata:
            return ark_metadata
    return

templates = Jinja2Templates(directory="fairscape_mds/templates/page")
templates.env.filters['add_link'] = add_link

@ResolverRouter.get(
    "/ark:{NAAN}/{postfix}",
    summary="Retrieve metadata for a specified ARK",
    response_description="ARK metadata",
    responses={
        200: {"description": "Successful Response", "content": {"application/json": {}, "text/html": {}}},
        404: {"description": "ARK not found"},
        500: {"description": "Server error"}
    }
)
def resolve(
    request: Request,
    NAAN: Annotated[str, Path(
        title="ARK Name Assigning Authority Number",
        )], 
    postfix: Annotated[str, Path(
        title="Persitant Identifier"
        )]
    ):
    """ Resolve Identifier Metadata and Return in JSON-LD
    """

    if len(NAAN) != 5:
        return JSONResponse(
                status_code=404,
                content={"error": "NAAN must be 5 digits"}
                )

    # TODO support multiple NAANs
    if NAAN!= fairscapeConfig.NAAN:
        return RedirectResponse(f'https://n2t.net/ark:{NAAN}/{postfix}')
   
    # search for metadata
    arkMetadata = identifierCollection.find_one(
            {"@id": f"ark:{NAAN}/{postfix}"},
            projection={"_id": 0, "@graph._id": 0}
            )


    if not arkMetadata:
        return JSONResponse({"@id": f"ark:{NAAN}/{postfix}", "error": "ark not found", "status_code": 404}, status_code=404)
    
    #look and see if an evidence graph exists if it does return it
    # if not return empty dict.
    eg_ark = arkMetadata.get("hasEvidenceGraph",None)
    if eg_ark:
        prefix_and_naan, eg_postfix = eg_ark.split("/")
        _, eg_NAAN = prefix_and_naan.split(":")
        
        #far from perfect, but default to shwoing first @graph or normal metadata
        eg_metadata = find_metadata([identifierCollecion, rocrateCollection], eg_NAAN, eg_postfix).get("@graph",[ark_metadata])[0]
    else:
        eg_metadata = ark_metadata

    model_map = {
        "user": (User, "user_template.html"),
        "evidencegraph": (EvidenceGraph, "evidencegraph_template.html"),
        "rocrate": (ROCrate, "rocrate_template.html"),
        "schema": (Schema, "schema_template.html"),
        "dataset": (DatasetWriteModel, "dataset_template.html"),
        "software": (Software, "software_template.html"),
        "computation": (Computation, "computation_template.html")
    }

    #TODO clean up this line
    metadata_type = ark_metadata.get("@type").lower().replace('evi:', '').replace('person','user').replace("https://w3id.org/evi#","").replace("https://w2id.org/evi#","")
    type_info = model_map.get(metadata_type)
    try: 
        if type_info:
            model_class, template_name = type_info
            model_instance = model_class.construct(**ark_metadata)
            json_data = json.dumps(model_instance.dict(by_alias=True), default=str, indent=2)
            rdf, turtle = convert_to_rdf(json_data)
            if "text/html" in request.headers.get("Accept", "").lower():
                context = {
                            "request": request, 
                            metadata_type: model_instance,
                            "json": json_data,
                            "rdf_xml": rdf,
                            "turtle": turtle, 
                            "type": metadata_type.title(),
                            "evidencegraph":eg_metadata
                        }
                return templates.TemplateResponse(template_name, context)

        # Default to returning JSON if type is not supported or not specified for HTML
        return JSONResponse(ark_metadata, status_code=200)

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
