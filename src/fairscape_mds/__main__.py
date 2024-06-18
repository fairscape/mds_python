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
    fairscapeConfig = get_fairscape_config(config) 

    # try to instantiate

    #try:
    #    fairscapeConfig.SetupMinio()
    #    print("setup_minio")
    #    fairscapeConfig.SetupMongo()
    #    print("setup_mongo")
    #except Exception:
    #    pass

    fairscapeConfig.RunServer()

if __name__ == '__main__':
    run()
