import re

def validate_ark(guid: str) -> str:

	ark_regex = r"(ark:[0-9]{5})/([a-zA-Z0-9\-]*)"

	ark_matches = re.findall(ark_regex, guid)

	if len(ark_matches) != 1:
		raise ValueError(f"ark syntax error: {guid}")

	prefix, postfix = ark_matches[0]
	
	if len(postfix) == 0:
		raise ValueError(f"ark syntax error: Missing Identifier Postfix guid: {guid}")

	return guid
