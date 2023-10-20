VERSION ?= 0.1.3

run:
	python3 main.py

setup: requirements.txt
	pip install -r requirements.txt

clean:
	rm -rf __pycache__

build:
	docker build -t  ghcr.io/fairscape/mds_python:${VERSION} .

push:
	docker push ghcr.io/fairscape/mds_python:${VERSION}