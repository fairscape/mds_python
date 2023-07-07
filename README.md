# Python Metadata Service

The Metadata Service (MDS) of the FAIRSCAPE application, is the core backend service responsible for metadata managment. MDS is a RESTfull API implemented in python with the fastAPI framework. This service provides persitant globally unique identifiers (guids) as ARKS for many types of digital objects and maintains provenance metadata during the data science life-cycle. 

As a generalist repository MDS supports a core metadata requirement derived from schema.org, but can be extended with any ontology annotation in JSON-LD.
