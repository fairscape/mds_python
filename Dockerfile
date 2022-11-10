FROM python:3.9-slim as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM builder as fairscape

#RUN addgroup --system fair && adduser --system --group fair
#USER fair

COPY mds /mds/mds
COPY static /mds/static
COPY templates /mds/templates
COPY main.py /mds/main.py

WORKDIR /mds

RUN export PYTHONPATH=$PYTHONPATH:/mds

CMD ["python3", "main.py"]
