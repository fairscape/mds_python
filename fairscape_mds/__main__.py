import argparse
import uvicorn
from fairscape_mds.mds.config import (
    setup_minio,
    setup_mongo
)


parser = argparse.ArgumentParser()
parser.add_argument("--host", default='0.0.0.0')
parser.add_argument("--port", default='8080')


if __name__ == '__main__':

    args = parser.parse_args()

    # try to instantiate
    #try:
    #    setup_minio()
    #    print("setup_minio")
    #    setup_mongo()
    #    print("setup_mongo")
    #except Exception:
    #    pass

    uvicorn.run(
        'fairscape_mds.mds.app:app', 
        host='0.0.0.0', 
        port=8080, 
        reload=True
        )