import argparse
import uvicorn
from os import environ
from mds.database.minio import GetMinioConfig


# TODO make sure configuration is valid, if not create configured minio bucket and mongo database
parser = argparse.ArgumentParser()
parser.add_argument("--host", default='0.0.0.0')
parser.add_argument("--port", default='8080')


if __name__ == '__main__':

    args = parser.parse_args()

    uvicorn.run(
        'mds.app:app', 
        host='0.0.0.0', 
        port=8080, 
        reload=True
        )
