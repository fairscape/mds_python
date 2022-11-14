import os
from celery import Celery

app = Celery(
    'compute', 
    include=["mds.compute.tasks"]
)

# setup Celery configuration
redis_service_port = os.environ.get("REDIS_SERVICE_PORT")

if redis_service_port is None:
    pass

else:
    app.conf.broker_url =f"redis://{redis_service_port.strip('tcp://')}/0"
    app.conf.result_backend=f"redis://{redis_service_port.strip('tcp://')}/1"


if __name__ == "__main__":
	app.start()