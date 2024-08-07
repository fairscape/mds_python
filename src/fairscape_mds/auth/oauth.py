from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

from fairscape_mds.models.user import (
    UserLDAP
    )
from fairscape_mds.config import get_fairscape_config

from typing import Annotated
import crypt
import jwt
from datetime import datetime, timezone, timedelta
import ldap3

OAuthScheme = OAuth2PasswordBearer(tokenUrl="token")


fairscapeConfig = get_fairscape_config()
jwtSecret = fairscapeConfig.jwtSecret


def createToken(email: str, fullname: str, userCN: str) -> str:
    """
    Create a new Token on a login session 

    :param str email: user email to use as metadata in the token
    :param str fullname: User's full name 
    :param str userDN: Users's LDAP Common Name
    """
    now = datetime.now(timezone.utc)
    exp = datetime.now(timezone.utc) + timedelta(hours=1)

    nowTimestamp = datetime.timestamp(now)
    expTimestamp = datetime.timestamp(exp)

    tokenMessage = {
        'iss': 'https://fairscape.net/',
        'sub':  userCN,
        'name': fullname,
        'email': email,
        'iat': int(nowTimestamp),
        'exp': int(expTimestamp)
    }
 
    compactJWS = jwt.encode(tokenMessage, jwtSecret, algorithm="HS256")
    return compactJWS


class LoginExceptionUserNotFound(Exception):
    pass

class AuthNExceptionUserNotFound(Exception):
    pass


def loginLDAP(ldapConnection: ldap3.Connection, email: str, password: str) -> str:
    """
    Given a users email and password, search ldap if a matching record is found, create a JWT to return with the API response

    :param str email: A user's email
    :param str password: A user's password
    :return: A newly minted JSON Web token containing user metadata and cryptographically signed
    :rtype: str
    :raises fairscape_mds.auth.oauth.LoginExceptionUserNotFound: Exception Raised when users credentials don't match any user in LDAP
    """

    # search the users 
    ldapConnection.search(
            search_base=fairscapeConfig.ldap.usersDN,
            search_filter=f"(&(userPassword={password})(mail={email}))",
            search_scope=ldap3.SUBTREE,
            attributes=['*']
            )

    query_results = ldapConnection.entries

    # if no users are matched
    if len(query_results)==0:
        raise LoginExceptionUserNotFound


    # if the user is found
    elif len(query_results) == 1:
        user_record = query_results[0]
        user_attributes = user_record.entry_attributes_as_dict

        user_cn = str(user_record.cn)
        user_fullname = f"{user_attributes['givenName'][0]} {user_attributes['sn'][0]}"

        return createToken(
                email=email,
                fullname=user_fullname,
                userCN=user_cn
                )


def getCurrentUser(token: Annotated[str, Depends(OAuthScheme)])->UserLDAP:    
    """
    Given a JWT from a request, return the user record from LDAP

    :param str token: An encoded JSON Web Token
    :returns: A user record
    :rtype: fairscape_mds.models.User
    :raises fastapi.HTTPException: Raises an error when decoding and validating the token fails
    """
    # decode jwt
    try:    
        token_metadata = jwt.decode(    
            token,     
            jwtSecret,    
            algorithms=["HS256"]
        )    
    except Exception as e: 
        raise HTTPException(    
            status_code=401,
            detail=f"Authorization Error Decoding Token\terror: {str(e)}\ttoken: {token}"     
        )    

    user_cn = token_metadata['sub']
    email = token_metadata['email']
    
    ldapConnection = fairscapeConfig.ldap.connectAdmin()

    # search the users 
    ldapConnection.search(
            search_base=fairscapeConfig.ldap.usersDN,
            search_filter=f"(&(cn={user_cn})(mail={email}))",
            search_scope=ldap3.SUBTREE,
            attributes=['cn', 'mail', 'givenName', 'sn', 'o', 'memberOf']
            )

    query_results = ldapConnection.entries
    ldapConnection.unbind()

    if len(query_results) == 0:
        raise HTTPException(
            status_code=404,
            detail="User not found according to token"
        )
    
    elif len(query_results) == 1:
        ldap_user_entry = query_results[0]
        ldap_user_attributes = ldap_user_entry.entry_attributes_as_dict

        try: 
            # construct the user entry
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

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error with User Metadata\tException: {str(e)}\tUser Metadata: {str(ldap_user_attributes)}"
            )

def getUserByCN(ldapConnection, user_cn):
    # search users in ldap
    ldapConnection.search(
            search_base=fairscapeConfig.ldap.usersDN,
            search_filter=f"(cn={user_cn})",
            search_scope=ldap3.SUBTREE,
            attributes=['dn', 'cn', 'mail', 'givenName', 'sn', 'o', 'memberOf']
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

