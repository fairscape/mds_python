FROM python:3.9-slim as builder

WORKDIR /mds

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM builder as fairscape

RUN addgroup --system fair && adduser --system --group fair
USER fair

WORKDIR mds

COPY mds mds/mds
COPY main.py mds/main.py

CMD ["python3", "mds/main.py"]