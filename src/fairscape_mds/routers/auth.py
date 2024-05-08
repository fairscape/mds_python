from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from fairscape_mds.models.user import getUserByEmail
from fairscape_mds.config import get_fairscape_config
from fairscape_mds.auth.oauth import (
        OAuthScheme,
        createToken

)
import crypt
from typing import Annotated


fairscapeConfig = get_fairscape_config()
mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]

router = APIRouter()

@router.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    userInstance, findUserResult = getUserByEmail(form_data.username, userCollection)
    if not findUserResult.success:
        return JSONResponse(
            status_code= findUserResult.status_code, 
            content={
                "error": findUserResult.message,
                "message": "incorrect combination of username and password" 
                }
            )

    hashed_password = crypt.crypt(form_data.password, fairscapeConfig.passwordSalt)
    if not hashed_password == userInstance.password:
        return JSONResponse(
            status_code=400, 
            content={"message": "incorrect combination of username and password" }
            )

    # create a JWT for the token
    new_token = createToken(userInstance.email, userInstance.name)


    return JSONResponse(
            status_code=200,
            content={
                "access_token": str(new_token), "token_type": "bearer"}
            )
