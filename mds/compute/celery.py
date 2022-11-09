import os
from celery import Celery


# setup Celery configuration
redis_service_port = os.environ.get("REDIS_SERVICE_PORT")

workflow = Celery(
    'compute', 
    broker=f"redis://{redis_service_port.strip('tcp://')}/0",
    backend=f"redis://{redis_service_port.strip('tcp://')}/1"
)

if __name__ == "__main__":
	workflow.start()