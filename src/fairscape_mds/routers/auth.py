from fastapi import Depends, HTTPException, status, APIRouter, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from fairscape_mds.models.user import getUserByEmail
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.auth.oauth import (
        OAuthScheme,
        loginLDAP,
        UserLDAP,
        LoginExceptionUserNotFound,
        getCurrentUser,
)
from fairscape_mds.auth.ldap import (
    getUserByCN,
    getUserTokens,
    addUserToken,
    updateUserToken,
    deleteUserToken,
    UserToken,
    UserTokenUpdate 
)
from typing import Annotated


fairscapeConfig = get_fairscape_config()
ldapConnection = fairscapeConfig.ldap.connectAdmin()

router = APIRouter()

@router.post("/login")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    try:
        mintedToken = loginLDAP(
                ldapConnection, 
                email=form_data.username, 
                password=form_data.password
                )

    except LoginExceptionUserNotFound:
        return JSONResponse(
            status_code= 401, 
            content={
                "error": "login failed",
                "message": "incorrect combination of username and password" 
                }
            )


    return JSONResponse(
            status_code=200,
            content={
                "access_token": str(mintedToken), 
                "token_type": "bearer"
                }
            )

#@router.get("/profile")
def getProfile(
   currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
):
    '''
    Return the Profile of the Current User
    '''
    pass


#@router.put("/profile")
def updateProfile(
   currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
):
    pass

@router.get("/profile/credentials")
def getCredentials(
   currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
): 
    tokens = getUserTokens(
        ldapConnection,
        userDN=currentUser.dn
    )
    return tokens

@router.post("/profile/credentials")
def addCredentials(
   currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
   newToken: UserToken
):

    addToken = addUserToken(
        ldapConnection,
        userDN=currentUser.dn,
        tokenInstance=newToken
    )

    if addToken:
        return JSONResponse(
            content={
                "uploaded": {
                    "tokenUID": newToken.tokenUID
                    }
            },
            status_code=201
        )

    # TODO check if token already exists    
    else:
        return JSONResponse(
            content= {"error": "failed to upload token"},
            status_code=400
        )


@router.delete("/profile/credentials/{tokenUID}")
def deleteCredentials(
    currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
    tokenUID: Annotated[str, Path(title="token id")]
):
    deleteStatus = deleteUserToken(
        ldapConnection,
        userDN=currentUser.dn,
        tokenID=tokenUID
    )

    if deleteStatus:
        return JSONResponse(
            content={
                "deleted": {
                    "tokenUID": tokenUID
                    }
            },
            status_code=200
        )

    # TODO check if token exists    
    else:
        return JSONResponse(
            content= {
                "error": "failed to delete token",
                "tokenUID": tokenUID
            },
            status_code=400
        )


@router.put("/profile/credentials")
def updateCredentials(
   currentUser: Annotated[UserLDAP, Depends(getCurrentUser)],
   tkUpdate: UserTokenUpdate
):
    updateTokenStatus = updateUserToken(
        ldapConnection,
        userDN=currentUser.dn,
        tokenUpdate=tkUpdate
    )

    if updateTokenStatus:
        return JSONResponse(
            content={
                "updated": {
                    "tokenUID": tkUpdate.tokenUID
                    }
            },
            status_code=200
        )

    # TODO check if token exists    
    else:
        return JSONResponse(
            content= {
                "error": "failed to update token",
                "tokenUID": tkUpdate.tokenUID
            },
            status_code=400
        )