from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from mds.database import mongo, casbin
from mds.database.config import MONGO_DATABASE, MONGO_COLLECTION
from mds.models.project import Project, list_project
import mds.models.auth as auth

router = APIRouter()

@router.post(
    "/login",
    summary="Log a User in Returning a JWT Token in the response"
)
def login(email: str, password: str):
    # set up database connetion
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

    try:
        session = auth.LoginUserBasic(mongo_collection, email, password)
    except auth.UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "invalid login credentials"}
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
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

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
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_db[MONGO_COLLECTION]

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

@router.post("/oauth/login")
def globus_login():
    return {"status": "not implemented"}


@router.post("/oauth/logout")
def globus_login():
    return {"status": "not implemented"}


async def CheckTokenMiddleware(request, call_next):
    """
    Middleware for checking for the presence of session credentials in authentication

    """

    # check if the session is in the cookie
    session_cookie = request.cookies.get('fairscape-session')

    if session_cookie is None:
        # check if the session is in the auth header
        session_header = request.headers.get('Authorization')
        Authorization = session_header
    else:
        Authorization = session_cookie

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client[MONGO_DATABASE]
    mongo_collection = mongo_client[MONGO_COLLECTION]

    # parse the credentials
    try:
        calling_user = auth.ParseAuthHeader(mongo_collection, Authorization)
    except auth.UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except auth.TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )


    
    # request.headers.get("Accept")

    response = await call_next(request)
    return response
