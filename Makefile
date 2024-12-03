VERSION = RELEASE.2024-12-02.v2

run:
	cd src/ && python -m fairscape_mds

run-docker: 
	docker compose up --build -d

run-local:
	# need to import environment variables
	# source deploy/local.env

	# run all backend services
	docker compose up --build -d ldap mongo minio redis fairscape-worker
	
	# run server in current session
	cd src/ && uvicorn fairscape_mds.app:app --host 0.0.0.0 --port 8080

setup: requirements.txt
	pip install -r requirements.txt

clean:
	rm -rf __pycache__

build:
	docker build -t  ghcr.io/fairscape/mds_python:${VERSION} .

push:
	docker push ghcr.io/fairscape/mds_python:${VERSION}
