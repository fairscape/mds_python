import argparse
import uvicorn
import click
from fairscape_mds.mds.config import (
    get_fairscape_config,
    setup_minio,
    setup_mongo
)

@click.command()
@click.option("--config", default=None, help="path to .env file for configuration")
def run(config):


    #load configuration
    fairscape_config = get_fairscape_config() 

    # try to instantiate
    #try:
    #    setup_minio()
    #    print("setup_minio")
    #    setup_mongo()
    #    print("setup_mongo")
    #except Exception:
    #    pass

    fairscape_config.RunServer()

if __name__ == '__main__':
    run()
