FROM python:3.12-slim as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

RUN python3 -m pip install --upgrade pip && \ 
    python -m venv /opt/venv 

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM python:3.12-slim as fairscape
COPY --from=builder /opt/venv /opt/venv

# copy source code
COPY src/ /fairscape/src/
WORKDIR fairscape/src/

# add users to run fairscape server
RUN addgroup --system fair && adduser --system --group fair
# add permission to file path 
RUN chgrp -R fair /fairscape
# switch to limited user
USER fair


#RUN export PYTHONPATH=$PYTHONPATH:/fairscape_mds
ENV PATH="/opt/venv/bin:$PATH"

# run using uvicorn
CMD ["uvicorn", "fairscape_mds.app:app", "--host", "0.0.0.0", "--port", "80"]
