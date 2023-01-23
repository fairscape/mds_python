#FROM python:3.7-alpine as builder
#FROM ubuntu:23.04 as builder
FROM continuumio/miniconda3

# install the statsmodels package
RUN conda install -c conda-forge statsmodels

COPY /MuSIC /MuSIC
WORKDIR /MuSIC


#FROM builder

# install required python libraries
RUN pip install -r ./installation/requirements.txt

# install clixo dependancy
#RUN ./installation/install.sh; exit 0