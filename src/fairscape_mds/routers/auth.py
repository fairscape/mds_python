from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from fairscape_mds.models.user import getUserByEmail
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.auth.oauth import (
        OAuthScheme,
        loginLDAP,
        LoginExceptionUserNotFound
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
