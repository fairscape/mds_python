from typing import Dict    

def formatROCrate(rocrateMetadata: Dict, fairscapeURL: str)->Dict:
	''' Format ROCrate metadata from mongoDB to be returned to the user
	'''

	# format json-ld with absolute URIs
	rocrateMetadata['@id'] = f"{fairscapeURL}/{ rocrateMetadata['@id']}"

	# remove _id object id from metadata
	rocrateMetadata.pop('_id', None)
	# remove permissions from top level metadata
	rocrateMetadata.pop("permissions", None)
	
	# process every crate elem in @graph of ROCrate 
	for crateElem in rocrateMetadata.get("@graph", []):
			crateElem['@id'] = f"{fairscapeURL}/{crateElem['@id']}"
			crateElem.pop("_id", None)
			crateElem.pop("permissions", None)

			# set resolvable download links
			if 'file' in crateElem.get('contentURL'):
					crateElem["contentURL"] = f"{fairscapeURL}/dataset/download/{crateElem.get('@id')}"

	return rocrateMetadata

def formatDataset(datasetMetadata: Dict)->Dict:
	''' Format Dataset Metadata from mongoDB to be returned to the user
  '''

	return datasetMetadata


def formatComputation(computationMetadata: Dict)->Dict:
	''' Format Computation Metadata from mongoDB to be returned to the user
  '''

	return computationMetadata 


def formatSoftware(softwareMetadata: Dict)->Dict:
	''' Format Software Metadata from mongoDB to be returned to the user

	Must format usedBy property on software for resolvable arks
  '''

	return softwareMetadata 