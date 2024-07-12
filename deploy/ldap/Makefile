
build:
	docker build -t ldap .

run:
	docker run --privileged -u 0:0 -it ldap /bin/bash

run-bitnami:
	
	docker run -p 1389:1389 \
	  --name openldap \
	  --env LDAP_ROOT="dc=fairscape,dc=net" \
	  --env LDAP_ADMIN_USERNAME="admin" \
	  --env LDAP_ADMIN_PASSWORD="adminpassword" \
	  --env LDAP_ADMIN_DN="cn=admin,dc=fairscape,dc=net" \
	  --env LDAP_CONFIG_ADMIN_ENABLED=yes \
	  --env LDAP_CONFIG_ADMIN_USERNAME=configadmin \
	  --env LDAP_CONFIG_ADMIN_PASSWORD=configadminpassword \
	  --env LDAP_USER_DC=users \
	  --env LDAP_GROUP=admins \
	  --env LDAP_USERS=fairscapeUser \
	  --env LDAP_PASSWORDS=fairscapePass \
	  --mount type=bind,source=/Users/mal8ch-admin/fairscape/mds_python/deploy/ldap/ldif,target=/ldif \
	  bitnami/openldap

setup:
	docker exec openldap ldapadd -x -D cn=configadmin,cn=config -w configadminpassword  -H ldapi:/// -f /ldif/memberof.ldif
	docker exec openldap ldapadd -x -D cn=configadmin,cn=config -w configadminpassword  -H ldapi:/// -f /ldif/memberof_overlay.ldif
	docker exec openldap ldapadd -x -H ldapi:/// -D cn=admin,dc=fairscape,dc=net -w adminpassword -f /ldif/example.ldif

sc:
	docker exec openldap slapcat -n 2 -F /bitnami/openldap/slapd.d

sc0:
	docker exec openldap slapcat -n 0 -F /bitnami/openldap/slapd.d

