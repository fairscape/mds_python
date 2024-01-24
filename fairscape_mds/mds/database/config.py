import os
from urllib.parse import quote_plus

MONGO_URI = os.environ.get("MONGO_HOST", "localhost")
MONGO_USER = os.environ.get("MONGO_ACCESS_KEY", "root")
MONGO_PASS = os.environ.get("MONGO_SECRET_KEY", "example")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "test")
MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "testcol")


MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING")

if MONGO_CONNECTION_STRING is None:
    
    if MONGO_USER=="root":
        MONGO_CONNECTION_STRING = "mongodb://root:example@localhost:27017"
    else:
        MONGO_CONNECTION_STRING = f"mongodb://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASS)}@{MONGO_URI}:{str(MONGO_PORT)}/{MONGO_DATABASE}"

MINIO_URI = os.environ.get("MINIO_URI", "localhost:9000")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "test")
MINIO_ROCRATE_BUCKET = os.environ.get("MINIO_ROCRATE_BUCKET", "crate-contents")
MINIO_USER = os.environ.get("MINIO_ACCESS_KEY", "testroot")
MINIO_PASS = os.environ.get("MINIO_SECRET_KEY" ,"testroot")
