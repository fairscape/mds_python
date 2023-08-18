from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing_extensions import Annotated

from mds.config import (
    get_mongo_config,
    get_mongo_client,
    get_jwt_secret
)
from mds.models.user import (
    User
)
from mds.models.auth import (
    UserNotFound,
    TokenError,
    DecodeBearerAuth
)

import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

mongo_db = mongo_client[mongo_config.db]
user_collection = mongo_db[mongo_config.user_collection]
session_collection = mongo_db[mongo_config.session_collection]

JWT_SECRET= get_jwt_secret()


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

    try:
        token_metadata = jwt.decode(
            token, 
            JWT_SECRET,
            algorithms="HS256"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,            
            detail=f"Authorization Error {str(e)}" 
        )

    # TODO is the session registered

    # find the current user
    user_metadata = user_collection.find_one({
        "@type": "Person",
        "email": token_metadata.get("sub"),
        "name": token_metadata.get("name"),
    })

    if user_metadata is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,            
            detail=f"User Not Found" 
        )

    return User(**user_metadata)
    
 
