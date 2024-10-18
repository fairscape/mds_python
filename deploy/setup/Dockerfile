FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

RUN python3 -m pip install --upgrade pip && \ 
    python -m venv /opt/venv 

COPY requirements.txt .
RUN pip install -r requirements.txt


COPY setup_fairscape.py .
COPY data /data

COPY setup.env /setup.env

CMD ["python", "setup_fairscape.py"]
