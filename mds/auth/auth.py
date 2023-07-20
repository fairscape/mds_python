from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Annotated

from mds.config import (
    get_mongo 
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

mongo_config = get_mongo()
mongo_client = mongo_config.CreateClient()

mongo_db = mongo_client[mongo_config.db]
mongo_collection = mongo_db[mongo_config.collection]

JWT_SECRET="test jwt"


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

    # find the current user
    user_metadata = mongo_collection.find_one({
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
    
 
