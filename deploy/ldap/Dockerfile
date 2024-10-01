FROM ubuntu:latest

USER root
RUN apt-get update && apt-get install -y sudo slapd ldap-utils

WORKDIR /ldap
COPY ldif/ ldif/
COPY scripts/ scripts/
COPY ldap-config/slapd.d/ ldap-config/

RUN chmod +x scripts/*

#ENTRYPOINT ./entrypoint.sh

#ENTRYPOINT slapd -u root -h ldap:/// -h ldapi:/// -F /etc/ldap/slapd/

# Using the bitnami/openldap container
#FROM bitnami/openldap:latest
#RUN apt-get update && apt-get install -y sudo slapd ldap-utils
#RUN cp /usr/lib/ldap/* /opt/bitnami/openldap/libexec/openldap/
