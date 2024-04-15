from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from fairscape_mds.web.models.signin import SignInForm, SigninRequest
from fairscape_mds.web.models.active_user import ActiveUser
from fairscape_mds.web.utils.signin import *

router = APIRouter()

templates = Jinja2Templates(directory="templates")

# object to track the successfully logged-in user
active_user = ActiveUser()


""" @router.post("/page/signin", response_class=HTMLResponse)
def create_signin_page(request: Request, form_data: SignInForm = Depends(SignInForm.as_form)):

    is_valid_user, logged_in_user_id = check_signin_credentials(email=form_data.email, password=form_data.password)
    if logged_in_user_id:
        active_user.set_id(logged_in_user_id)
    if is_valid_user:        
        context = {
            "request": request            
        }
        return templates.TemplateResponse("page/home.html", context=context)
    else:
        context = {
            "request": request,
            "message": "Incorrect Email/Password! Try again."
        }
        return templates.TemplateResponse("page/signin.html", context=context)
 """



@router.post("/page/signin")
def login(login_request: SigninRequest):
    print('email and password')
    print(login_request.email)
    print(login_request.password)
    is_valid_user, logged_in_user_id = check_signin_credentials(email=login_request.email, password=login_request.password)

    if logged_in_user_id:
        active_user.set_id(logged_in_user_id)

    if is_valid_user:
        return {
            "success": True,
            "message": "User successfully logged in :)"
        }
    else:
        return {
            "success": False,
            "message": "Incorrect email/password!"
        }

