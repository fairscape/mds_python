#!/bin/bash
NAME="fairscape"
DIR="/fairscape"
USER=fastapi-user
GROUP=fastapi-user
WORKERS=4
WORKER_CLASS=uvicorn.workers.UvicornWorker
VENV=/fairscape/.venv/bin/activate
BIND=unix:$DIR/run/gunicorn.sock
LOG_LEVEL=error

cd $DIR
source $VENV
exec gunicorn main:app \
  --name $NAME \
  --workers $WORKERS \
  --worker-class $WORKER_CLASS \
  --user=$USER \
  --group=$GROUP \
  --bind=$BIND \
  --log-level=$LOG_LEVEL \
  --log-file=-
