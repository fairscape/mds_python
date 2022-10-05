import casbin_pymongo_adapter
import casbin
from urllib.parse import quote_plus
from mds.database.config import MONGO_URI, MONGO_USER, MONGO_PASS, MONGO_DATABASE

# TODO create class for enforcer and specific adapters

def GetEnforcer() -> casbin.Enforcer:
	""" return the casbin enforcer """
	adapter = casbin_pymongo_adapter.Adapter(
		f"mongodb://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASS)}@{MONGO_URI}:27017/", 
		MONGO_DATABASE)

	# TODO configure casbin model as parameter
	e = casbin.Enforcer('./tests/model.conf', adapter)
	return e