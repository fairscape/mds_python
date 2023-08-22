import argparse
import uvicorn
from mds.config import (
    setup_minio,
    setup_mongo
)


# TODO make sure configuration is valid, if not create configured minio bucket and mongo database
parser = argparse.ArgumentParser()
parser.add_argument("--host", default='0.0.0.0')
parser.add_argument("--port", default='8080')


if __name__ == '__main__':

    args = parser.parse_args()

    try:
        setup_minio()
        setup_mongo()
    except:
        pass

    uvicorn.run(
        'mds.app:app', 
        host='0.0.0.0', 
        port=8080, 
        reload=True
        )
