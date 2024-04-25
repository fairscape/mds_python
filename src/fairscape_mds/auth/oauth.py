from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException

from fairscape_mds.models.user import (
    getUserByEmail,
    User
    )
from fairscape_mds.config import get_fairscape_config

from typing import Annotated
import crypt
import jwt
from datetime import datetime, timezone, timedelta

OAuthScheme = OAuth2PasswordBearer(tokenUrl="token")


fairscapeConfig = get_fairscape_config()
mongoClient = fairscapeConfig.CreateMongoClient()
mongoDB = mongoClient[fairscapeConfig.mongo.db]
userCollection = mongoDB[fairscapeConfig.mongo.user_collection]

jwtSecret = fairscapeConfig.jwtSecret

def getCurrentUser(token: Annotated[str, Depends(OAuthScheme)]):    
     
    try:    
        token_metadata = jwt.decode(    
            token,     
            jwtSecret,    
            algorithms=["HS256"]  
        )    
    except Exception as e:    
        raise HTTPException(    
            status_code=status.HTTP_401_UNAUTHORIZED,                
            detail=f"Authorization Error {str(e)}"     
        )    
     
       
    # find the current user
    user_metadata = userCollection.find_one({
        "email": token_metadata.get("sub"),
        "name": token_metadata.get("name"),
    })
 
    if user_metadata is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,            
            detail=f"User Not Found" 
        )

    return User.model_validate(user_metadata) 



def createToken(userEmail, userName):
    now = datetime.now(timezone.utc)
    exp = datetime.now(timezone.utc) + timedelta(hours=1)

    nowTimestamp = datetime.timestamp(now)
    expTimestamp = datetime.timestamp(exp)

    tokenMessage = {
        'iss': 'https://fairscape.net/',
        'sub':  userEmail,
        'name': userName,
        'iat': int(nowTimestamp),
        'exp': int(expTimestamp)
    }
 
    compactJWS = jwt.encode(tokenMessage, jwtSecret, algorithm="HS256")
    return compactJWS


