import argparse
import uvicorn
import click
from fairscape_mds.config import (
    get_fairscape_config,
)

@click.command()
@click.option("--config", default=None, help="path to .env file for configuration")
def run(config):


    #load configuration
    fairscape_config = get_fairscape_config(config) 

    # try to instantiate
    try:
        fairscape_config.SetupMinio()
        print("setup_minio")
        fairscape_config.SetupMongo()
        print("setup_mongo")
    except Exception:
        pass

    fairscape_config.RunServer()

if __name__ == '__main__':
    run()
