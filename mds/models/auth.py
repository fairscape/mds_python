from pydantic import BaseModel, validator
import pymongo
from mds.utilities.operation_status import OperationStatus
from mds.models.user import User
import base64
from datetime import datetime, timezone
import jwt

JWT_SECRET = "test jwt"

class Session(BaseModel):
	'''
	Data Model for persisting Session Records of User Logins
	'''

	sub: str
	name: str
	iat: int
	exp: int
	iss: str = "fairscape"
	aud: str = "fairscape"


	def regsiter(self, MongoCollection) -> OperationStatus:

		# if there exists a session that isn't expired	
		current_utc_timestamp = int(datetime.now().replace(tzinfo=timezone.utc).timestamp())
		query_session = MongoCollection.find_one({
			"sub": self.sub, 
			"exp": {"$gt": current_utc_timestamp}
			})

		if query_session is not None:
			# revoke the all active credentials and persist new credential
			delete_result = MongoCollection.delete_many({"sub": self.sub, "exp": {"$gt": current_utc_timestamp}})

		# register the new token
		insert_result = MongoCollection.insert_one(self.dict(by_alias=True))

		return OperationStatus(True, "", 200)


	def refresh(self, MongoCollection) -> OperationStatus:
		current_utc_timestamp = int(datetime.now().replace(tzinfo=timezone.utc).timestamp())
		expiration_datetime  = datetime.datetime.now() + datetime.datetime.timedelta(hours=1)
		expiration_utc_timestamp = int(
			expiration_datetime.replace(
				tzinfo=datetime.timezone.utc
				).timestamp()
			)

		self.iat = current_utc_timestamp
		self.exp = expiration_utc_timestamp

		update_result = MongoCollection.update_one(
			{"sub": self.sub, "exp": self.exp, "iat": self.iat}, 
			{"iat": current_utc_timestamp, "exp": expiration_utc_timestamp}
			)

		return OperationStatus(True, "", 200)


	def revoke(self, MongoCollection) -> OperationStatus:
		delete_result = MongoCollection.delete_one({
			"sub": self.sub, 
			"exp": self.exp, 
			"iat": self.iat
			})

		return OperationStatus(True, "", 200)


	def encode(self) -> str:
		return jwt.encode(self.dict(), JWT_SECRET)


class UserNotFound(Exception):
    """ 
    exception raised when credentials passed in the 
    authorization header don't match any users in the database 
    """

    def __init__(self, email, password, message="user not found"):

        self.email = email
        self.password = password
        self.message = f"User Not Found\temail: {email} password: {password}"

        super().__init__(self.message)


class TokenError(Exception):
	"""
	Exception Raised for Other Token Errors

	i.e. 
	- Auth Header missing Bearer or Basic
	- JWT cannot be decoded
	"""
	def __init__(self, message="Error Parsing Token") -> None:
		self.message = message
		super().__init__(self.message)


def LoginUserBasic(
	MongoCollection: pymongo.collection.Collection, 
	email: str, 
	password: str
	) -> Session:
	'''
	given a users email and password create and register a session, and return the session object
	'''

	auth_user = MongoCollection.find_one({
		"@type": "Person", 
		"email": email,
		"password": password
		})

	if auth_user == None:
		raise UserNotFound(email, password)
	
	user_model = User(**auth_user)

	# create a session for the user
	current_utc_timestamp = int(
		datetime.datetime.now().replace(
			tzinfo=datetime.timezone.utc
			).timestamp()
		)

	expiration_datetime  = datetime.datetime.now() + datetime.datetime.timedelta(hours=1)
	expiration_utc_timestamp = int(
		expiration_datetime.replace(
			tzinfo=datetime.timezone.utc
			).timestamp()
		)


	sess = Session(
		aud = "fairscape",
		name = user_model.name,
		sub = user_model.email,
		iat = current_utc_timestamp,
		exp = expiration_utc_timestamp
		)

	session_create = sess.register(MongoCollection)	

	return sess
	

def ParseSession(EncodedSession: str) -> Session:
	if "Bearer " in EncodedSession:
		raw_session = EncodedSession.strip("Bearer ")
	else:
		raw_session = EncodedSession

	try:
		session_values = jwt.decode(raw_session, JWT_SECRET)
	except Exception as e:
		raise TokenError(str(e))

	return Session(**session_values)


def DecodeBearerAuth(MongoCollection, AuthHeader: str)-> User:
	stripped_header = AuthHeader.strip("Bearer ")
	session_values = jwt.decode(stripped_header, JWT_SECRET)
	sess = Session(**session_values)

	user_values = MongoCollection.find_one({"email": sess.sub})
	
	if user_values is None:
		raise UserNotFound

	return User(**user_values)


def DecodeBasicAuth(
	MongoCollection: pymongo.collection.Collection, 
	AuthHeader: str
	) -> User:
	""" lookup a user by credentials"""
	
	stripped_header = AuthHeader.strip("Basic ")
	email, password = str(base64.b64decode(stripped_header), 'utf-8').split(":")

	auth_user = MongoCollection.find_one({
		"@type": "Person", 
		"email": email,
		"password": password
		})

	if auth_user == None:
		raise UserNotFound(email, password)
	
	return User(**auth_user)


def ParseAuthHeader(
	MongoCollection: pymongo.collection.Collection,
	AuthHeader: str 
	) -> User:
	""" 
	given a string for the authorization header return the user model for 
	the credentials or raise a UserNotFound exception 
	"""

	if "Basic " in AuthHeader:
		return DecodeBasicAuth(MongoCollection, AuthHeader)

	if "Bearer " in AuthHeader:
		return DecodeBearerAuth(MongoCollection, AuthHeader)

	else:
		raise TokenError(AuthHeader)
    


