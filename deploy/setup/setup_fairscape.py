import minio
import ldap3
from dotenv import dotenv_values


# helper utilities

configValues = dotenv_values(dotenv_path="./setup.env")
ldapServerURI = f"ldap://{configValues['FAIRSCAPE_LDAP_HOST']}:{configValues['FAIRSCAPE_LDAP_PORT']}"
ldapBaseDN = configValues['FAIRSCAPE_LDAP_BASE_DN']
ldapUsersDN = configValues['FAIRSCAPE_LDAP_USERS_DN']
ldapGroupsDN = configValues['FAIRSCAPE_LDAP_GROUPS_DN']
configAdminDN = configValues['FAIRSCAPE_LDAP_CONFIG_ADMIN_DN']
configAdminPassword = configValues['FAIRSCAPE_LDAP_CONFIG_ADMIN_PASSWORD']
adminDN = configValues['FAIRSCAPE_LDAP_ADMIN_DN']
adminPassword = configValues['FAIRSCAPE_LDAP_ADMIN_PASSWORD']


class LDAPConnectionError(Exception):
	def __init__(self,exception: Exception | None=None, message: str="failed to connect to ldap"):

		self.message = message
		self.exception = exception
		super().__init__(self.message)


def connectLDAP(userDN, userPassword):
	try:
		server = ldap3.Server(ldapServerURI, get_info=ldap3.ALL)
		connection = ldap3.Connection(server,          
			user=userDN, 
			password=userPassword,
			lazy=False
			) 
		bind_response = connection.bind()
		if bind_response:
			ldapSetupLogger.info(f"msg: 'connected to LDAP server'\tserver: '{ldapServerURI}'\tuserDN: '{userDN}'")
		return connection
	
	except ldap3.core.exceptions.LDAPBindError as bindError:
		ldapSetupLogger.error(f"msg: 'ldap bind error'\tserver: '{ldapServerURI}'\tuserDN: '{userDN}'")
		raise LDAPConnectionError(
			exception=bindError, 
			message="ldap bind error"
			) 

	except ldap3.core.exceptions.LDAPSocketOpenError as connError:
		ldapSetupLogger.error(f"msg: 'ldap failed to open connection'\tserver: '{ldapServerURI}'\tuserDN: '{userDN}'")
		raise LDAPConnectionError(
			exception=connError, 
			message=f"ldap connection error: failed to open connection at {ldapServerURI}"
			) 

	except ldap3.core.exceptions.LDAPException as ldapException:
		ldapSetupLogger.error(f"msg: 'ldap exception'\tserver: '{ldapServerURI}'\tuserDN: '{userDN}'")
		raise LDAPConnectionError(
			exception=ldapException, 
			message=f"ldap error: {str(ldapException)}"
			)

def setupOverlay():
    # connect as the config admin
    configAdminConnection =connectLDAP(
        userDN=configAdminDN,
        userPassword=configAdminPassword
        )

    # add the module list to the config database 
    addModuleList = configAdminConnection.add(
        dn="cn=module,cn=config",
        attributes={
            "objectClass": "olcModuleList",
            "olcModuleLoad": [ "memberof.so", "refint.so"],
            "olcModulePath": "/opt/bitnami/openldap/lib/openldap"
        }
    )

    if not addModuleList:
        ldapSetupLogger.error(msg="msg: failed to add module list to config database")
        raise Exception("Setup Failed")

    configAdminConnection.rebind()

    try:
        ldap3.ObjectDef(['olcMemberOf'], configAdminConnection)

    except ldap3.core.exceptions.LDAPSchemaError as schemaError:
        ldapSetupLogger.error("failed to find olcMemberOf schema")
        raise Exception("Setup Failed")


    memberOfOverlayDN="olcOverlay={0}memberof,olcDatabase={2}mdb,cn=config"
    memberOfOverlayAttributes={
        "objectClass": [ "olcOverlayConfig", "olcMemberOf"],
        "olcOverlay": "memberof",
        "olcMemberOfRefInt": "TRUE",
    }

    addOverlay = configAdminConnection.add(
        dn=memberOfOverlayDN,
        attributes=memberOfOverlayAttributes,
    )


    configAdminConnection.rebind()

    if not addOverlay:
        overlayAppliedResult = configAdminConnection.search(
            search_base="olcDatabase={2}mdb,cn=config",
            search_scope=ldap3.SUBTREE,
            search_filter="(objectClass=olcOverlayConfig)"
        )

        if not overlayAppliedResult:
            ldapSetupLogger.error("failed to find applied memberOf overlay")
            raise Exception("ldap setup failure")

def loadGroups():
	""" load in all the groups to the fairscape ldap
	"""

	pass

def loadUsers():
	""" load in the users to add to the fairscape ldap
	"""
	with open("/data/user_data.csv", "r") as csvFile:

		# ignore the first line
		csvFile.readline()

		userData = csvFile.readline().split(",")

		user = {
			"firstName": userData[0],
			"lastName": userData[1],
			"dn": userData[2],
			"email": userData[3],
			"password": userData[4]
		}



	pass

if __name__ =="__main__":
	pass