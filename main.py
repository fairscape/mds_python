import uvicorn
from os import environ
from mds.database.minio import GetMinioConfig


# TODO make sure configuration is valid, if not create configured minio bucket and mongo database

# create the minio bucket
minio_client = GetMinioConfig()
MINIO_BUCKET = environ.get("MINIO_BUCKET", "test")

found = minio_client.bucket_exists(MINIO_BUCKET)
if not found:
    minio_client.make_bucket(MINIO_BUCKET)


if __name__ == '__main__':

    uvicorn.run(
        'mds.app:app', 
        host='0.0.0.0', 
        port=8080, 
        reload=True
        )
