import re


def validate_ark(guid: str) -> str:
    """Validate ark syntax and return the value of the passed string if correct, otherwise raise a ValueError exeption

    The current validation that occurs is as follows:
    The structure of an ark is broken into two parts, the prefix and the postfix.
    The prefix and the postfix are seperated by a single slash "/".
    The prefix must be start with "ark:" followed by 5 numbers.
    And the postfix can have any number of characters or digits and dashes are allowed.

    This function could  be improved to identify more aspects of ark structure
    i.e.
    According to the ark RFC
    ? may determine the type of content to return

    Args:
        guid (str): string to be validated

    Returns:
        str: the value of the passed guid, only returned if validation succeeds
    """

    ark_regex = r"(ark:[0-9]{5})/([a-zA-Z0-9\-]*)"

    ark_matches = re.findall(ark_regex, guid)

    if len(ark_matches) != 1:
        raise ValueError(f"ark syntax error: {guid}")

    prefix, postfix = ark_matches[0]

    if len(postfix) == 0:
        raise ValueError(f"ark syntax error: Missing Identifier Postfix guid: {guid}")

    return guid


def validate_email(email_str: str) -> str:
    """Checks if an email address provided by an user is formatted correctly.

    Args:
        email_str (str): The email address submitted by an user

    Raises:
        ValueError: Raises if the email address is not formatted correctly

    Returns:
        str: The correctly-formatted email address of the user
    """
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    email_matches = re.findall(email_regex, email_str)

    if len(email_matches) != 1:
        raise ValueError(f"email syntax error: {email_str}")

    return email_str
