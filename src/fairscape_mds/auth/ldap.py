from fairscape_mds.models.user import UserLDAP
from pydantic import BaseModel, Field
import ldap3
from typing import Optional
from fairscape_mds.config import get_fairscape_config

fairscapeConfig = get_fairscape_config()

class UserToken(BaseModel):
    tokenUID: str
    tokenValue: str
    endpointURL: str

class UserTokenUpdate(BaseModel):
    tokenUID: str
    tokenValue: Optional[str] = Field(default=None)
    endpointURL: Optional[str] = Field(default=None)


def getUserByCN(ldapConnection, user_cn):
    # search users in ldap
    ldapConnection.search(
            search_base=fairscapeConfig.ldap.usersDN,
            search_filter=f"(cn={user_cn})",
            search_scope=ldap3.SUBTREE,
            attributes=['cn', 'mail', 'givenName', 'sn', 'o', 'memberOf']
            )

    query_results = ldapConnection.entries
    
    if len(query_results)==0:
        raise Exception('User not found')

    elif len(query_results)>1:
        raise Exception('Multiple Users Found with CN')
   
    else:
        ldap_user_entry = query_results[0]
        ldap_user_attributes = ldap_user_entry.entry_attributes_as_dict

        user_instance = UserLDAP.model_validate({
            "dn": ldap_user_entry.entry_dn,
            "cn": str(ldap_user_entry.cn),
            "email": ldap_user_attributes.get('mail')[0],
            "givenName": ldap_user_attributes.get('givenName')[0],
            "surname": ldap_user_attributes.get('sn')[0],
            "organization": ldap_user_attributes.get('o')[0],
            "memberOf": ldap_user_attributes.get('memberOf')
            })

        return user_instance


def getUserTokens(
    ldapConnection: ldap3.Connection,
    userDN: str
    ):
    '''
    Return all Tokens stored in LDAP for a user

    Args:
        ldapConnection (ldap3.Connection): An active LDAP connection to search the DIT
        userDN (str): DN for the user in LDAP

    Returns:
        tokenList (list[fairscape_mds.auth.ldap.UserToken]): List of all stored tokens for a user
    '''
    ldapConnection.search(
        search_base=userDN,
        search_scope=ldap3.SUBTREE,
        search_filter="(objectClass=account)",
        attributes=["*"]
    )
    tokens = ldapConnection.entries
    tokenList = []

    for tk in tokens:
      tkAttributes = tk.entry_attributes_as_dict
      tokenList.append(
        UserToken(
                tokenUID= tkAttributes.get('uid')[0],
								tokenValue= tkAttributes.get('userPassword')[0],
								endpointURL=tkAttributes.get('host')[0]
					 )
			)
    return tokenList


def updateUserToken(
    ldapConnection: ldap3.Connection,
    userDN: str,
    tokenUpdate: UserTokenUpdate
    )-> bool:
    '''
    Edit metadata for a single LDAP token

    Args:
        ldapConnection (ldap3.Connection): An active LDAP connection to search the DIT
        userDN (str): DN of the user editing this token

    Returns:
        updateSuccess (bool): Indicates whether the modification was successfull

    '''

    tokenDN = f"uid={tokenUpdate.tokenUID},{userDN}"

    tokenChanges = {}

    if tokenUpdate.endpointURL:
        tokenChanges['host'] = (ldap3.MODIFY_REPLACE, tokenUpdate.endpointURL)

    if tokenUpdate.tokenValue:
        tokenChanges['userPassword'] = (ldap3.MODIFY_REPLACE, tokenUpdate.tokenValue)

    updateSuccess = ldapConnection.modify(
        tokenDN,
        changes=tokenChanges
    )

    updateSuccess = True
    return updateSuccess


def deleteUserToken(
    ldapConnection: ldap3.Connection,
    userDN: str,
    tokenID: str
    )-> bool:
    '''
    Remove a specific stored token from a users DIT

    Args:
        ldapConnection (ldap3.Connection): An active LDAP connection to edit the DIT
        userDN (str): Distringuished Name of the user in LDAP
        tokenID (str): Unique ID for this token to be set as the uid for the ldap entry

    Returns:
        tokenRemoved (bool): Boolean indicating whether the token was removed
    '''
    tokenDN = f"uid={tokenID},{userDN}"
    tokenRemoved = ldapConnection.delete(tokenDN)

    return tokenRemoved


def addUserToken(
    ldapConnection: ldap3.Connection,
    userDN: str,
    tokenInstance: UserToken
    )-> bool:
    '''
    Store a token in LDAP, adding the token as an account under the Users account RDN

    Args:
        ldapConnection (ldap3.Connection): An active LDAP connection to edit the DIT
        userDN (str): Distinguished Name of the user in LDAP
        tokenInstance (fairscape_mds.auth.oauth.UserToken): Metadata of new token to add
    
    Returns:
        addOperation (bool): Boolean indicating if the addition was successfull
        
    '''

    tokenDN = f"uid={tokenInstance.tokenUID},{userDN}"

    addOperation = ldapConnection.add(
        tokenDN,
        attributes={
            "objectClass": [
                "account",
                "simpleSecurityObject"
            ],
            "uid": tokenInstance.tokenUID,
            "userPassword": tokenInstance.tokenValue,
            "description": "dataverse",
            "host": tokenInstance.endpointURL
        }
    )

    return addOperation
