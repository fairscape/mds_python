import os

MONGO_URI = os.environ.get("MONGO_HOST", "localhost")
MONGO_USER = os.environ.get("MONGO_ACCESS_KEY", "root")
MONGO_PASS = os.environ.get("MONGO_SECRET_KEY", "example")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "test")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "testcol")


MINIO_URI = os.environ.get("MINIO_URI", "localhost")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "test")
MINIO_USER = os.environ.get("MINIO_ACCESS_KEY", "testroot")
MINIO_PASS = os.environ.get("MINIO_SECRET_KEY" ,"testroot")
