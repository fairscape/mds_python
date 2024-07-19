from typing_extensions import Annotated

from fastapi import (
    APIRouter,
    Path,
    Header,
    Depends,
    Request
)

from fairscape_mds.models.user import User
from fairscape_mds.models.rocrate import ROCrate
from fairscape_mds.models.schema import Schema
from fairscape_mds.models.dataset import Dataset
from fairscape_mds.models.software import Software
from fairscape_mds.models.computation import Computation
from fairscape_mds.models.evidencegraph import EvidenceGraph
from fairscape_mds.models.fairscape_base import IdentifierPattern

from fastapi.responses import JSONResponse

from fairscape_mds.config import (
    get_mongo_config,
    get_mongo_client,
    get_fairscape_url,
) 
from datetime import datetime
from fastapi.templating import Jinja2Templates
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
mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

FAIRSCAPE_URL = get_fairscape_url()

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
    if isinstance(value,list):
        return value
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
    print(f"ark:{naan}/{postfix}")
    for collection in collections:
        ark_metadata = collection.find_one({"@id": f"ark:{naan}/{postfix}"}, projection={"_id": 0, "@graph._id": 0})
        if ark_metadata:
            return ark_metadata
    return {}

def filter_nonprov(d, keys_to_keep):
    """
    Recursively filter a dictionary, keeping only the keys in keys_to_keep.
    If a list is encountered, apply the filtering to any dictionaries within the list.

    Parameters:
    d (dict): The dictionary to filter.
    keys_to_keep (list): The list of keys to keep.

    Returns:
    dict: A new dictionary with only the keys in keys_to_keep.
    """
    if isinstance(d, dict):
        return {k: filter_nonprov(v, keys_to_keep) for k, v in d.items() if k in keys_to_keep}
    elif isinstance(d, list):
        return [filter_nonprov(item, keys_to_keep) for item in d]
    return d

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
        # TODO import ark NAAN from config
        #default = "59852",
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
    collections = [mongo_db[mongo_config.identifier_collection], 
                   mongo_db[mongo_config.user_collection],
                   mongo_db[mongo_config.rocrate_collection]]
    
    ark_metadata = find_metadata(collections, NAAN, postfix)

    if not ark_metadata:
        return JSONResponse({"@id": f"ark:{NAAN}/{postfix}", "error": "ark not found", "status_code": 404}, status_code=404)
    
    #look and see if an evidence graph exists if it does return it
    # if not return empty dict.
    eg_ark = ark_metadata.get("hasEvidenceGraph",None)
    if eg_ark:
        prefix_and_naan, eg_postfix = eg_ark.split("/")
        _, eg_NAAN = prefix_and_naan.split(":")
        
        #far from perfect, but default to shwoing first @graph or normal metadata
        eg_metadata = find_metadata(collections, eg_NAAN, eg_postfix)
        if '@graph' in eg_metadata.keys():
            eg_metadata = eg_metadata.get("@graph",[ark_metadata])[0]

    else:
        eg_metadata = filter_nonprov(ark_metadata,["@id",'name','description',"@type",'generatedBy',"isPartOf","@graph","usedByComputation","usedSoftware","usedDataset"])

    model_map = {
        "user": (User, "user_template.html"),
        "evidencegraph": (EvidenceGraph, "evidencegraph_template.html"),
        "rocrate": (ROCrate, "rocrate_template.html"),
        "schema": (Schema, "schema_template.html"),
        "dataset": (Dataset, "dataset_template.html"),
        "software": (Software, "software_template.html"),
        "computation": (Computation, "computation_template.html")
    }

    #TODO clean up this line
    metadata_type = ark_metadata.get("@type").lower().replace('evi:', '').replace('person','user').replace("https://w3id.org/evi#","").replace("https://w2id.org/evi#","")
    type_info = model_map.get(metadata_type)

    try:
        if type_info:
            model_class, template_name = type_info
            ark_metadata.pop('distribution', None)
            model_instance = model_class.construct(**ark_metadata)
            json_data = json.dumps(model_instance.dict(by_alias=True), default=str, indent=2)
            eg_json = json.loads(json.dumps(eg_metadata, default=str))

            rdf, turtle = convert_to_rdf(json_data)
            if "text/html" in request.headers.get("Accept", "").lower():
                context = {
                            "request": request, 
                            metadata_type: model_instance,
                            "json": json_data,
                            "rdf_xml": rdf,
                            "turtle": turtle, 
                            "type": metadata_type.title(),
                            "evidencegraph":eg_json
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
