VERSION = RELEASE.2024-06-10

run:
	cd src/ && python -m fairscape_mds

run-docker: 
	docker run -p 80:80 --env-file deploy/docker.env -it ghcr.io/fairscape/mds_python:${VERSION}

setup: requirements.txt
	pip install -r requirements.txt

clean:
	rm -rf __pycache__

build:
	docker build -t  ghcr.io/fairscape/mds_python:${VERSION} .

push:
	docker push ghcr.io/fairscape/mds_python:${VERSION}
