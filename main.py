import uvicorn
from os import environ
from mds.database.minio import GetMinioConfig


# TODO make sure configuration is valid, if not create configured minio bucket and mongo database


if __name__ == '__main__':

    uvicorn.run(
        'mds.app:app', 
        host='0.0.0.0', 
        port=8080, 
        reload=True
        )
