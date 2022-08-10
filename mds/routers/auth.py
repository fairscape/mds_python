from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from mds.database import mongo, casbin
from mds.models.project import Project, list_project
import mds.models.auth as auth

router = APIRouter()

@router.post(
	"/login",
        summary="Log a User in Returning a JWT Token in the response"
	)
def login(email: str = Form(), password: str = Form()):

	# set up database connetion
	mongo_client = mongo.GetConfig()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]

	try:
		session = auth.LoginUserBasic(mongo_collection, email, password)
	except auth.UserNotFound:
		return JSONResponse(
			status_code=401, 
			content= {"error": "invalid login credentials"}
			)

	encoded_session = session.encode()

	response = JSONResponse(
		status_code=200, 
		content={"session": encoded_session}
		)

	response.set_cookie(
		key="fairscape-session", 
		value=encoded_session,
		# set the cookie to expire in an hour
		max_age=360 
		)
	return response


@router.post(
	"/refresh",
	summary="Refresh a login token"
	)
def refresh(
	request: Request
	):

	# set up database connetion
	mongo_client = mongo.GetConfig()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]


	# check if the session is in the cookie
	session_cookie = request.cookies.get('fairscape-session')

	# check if the session is in the auth header
	session_header = request.headers.get('Authorization')

	if session_cookie is None and session_header is None:
		return JSONResponse(
			status_code=401,
			content={"error": "no valid credentials provided"}
			)

	if session_cookie is not None:
		# parse the cookie
		session = auth.ParseSession(session_cookie)
	else:
		# parse the header
		session = auth.ParseSession(session_header)

	refresh_status = session.refresh(mongo_collection)

	if refresh_status.success != True:
		return JSONResponse(
			status_code=500, 
			content={"error": "failed to refresh token"}
			)

	# return the new session encoded
	encoded_session = session.encode()
	response = JSONResponse(status_code=200, content={"session": encoded_session})
	response.set_cookie(
		key="fairscape-session", 
		value=encoded_session,
		# set the cookie to expire in an hour
		max_age=360 
		)
	return response


@router.post(
	"/revoke",
	summary="Invalidate a JWT login credential"
	)
def revoke(
	request: Request
	):

	# set up database connetion
	mongo_client = mongo.GetConfig()
	mongo_db = mongo_client["test"]
	mongo_collection = mongo_db["testcol"]


	# check if the session is in the cookie
	session_cookie = request.cookies.get('fairscape-session')

	# check if the session is in the auth header
	session_header = request.headers.get('Authorization')

	if session_cookie is None and session_header is None:
		return JSONResponse(
			status_code=401,
			content={"error": "no valid credentials provided"}
			)

	if session_cookie is not None:
		session = auth.ParseSession(session_cookie)
	else:
		session = auth.ParseSession(session_header)

	operation_status = session.revoke(mongo_collection)	

	return JSONResponse(
		status_code=200, 
		content={"status": "token revoked"}
		)
