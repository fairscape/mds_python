from multiprocessing import context
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from fairscape_mds.mds.web.models.signup import SignupRequest, SignupForm
from fairscape_mds.mds.web.utils.signup import *
from pydantic import BaseModel

router = APIRouter()

templates = Jinja2Templates(directory="templates")

"""@router.post("/page/signup", response_class=HTMLResponse)
def create_signup_page(request: Request, form_data: SignupForm = Depends(SignupForm.as_form)):

    context = {
        "request": request
    }

    if email_exists(form_data.email):                
        context["message"] = "User with this email already exists"
        return templates.TemplateResponse("page/signup.html", context=context)

    signup_create_status = initiate_signup(
        form_data.firstName,
        form_data.lastName,
        form_data.email,
        form_data.password1,
        form_data.password2)

    if signup_create_status:
        return templates.TemplateResponse("page/home.html", context=context)
    else:
        context["message"] = "Error signin up! Please contact support."
        return templates.TemplateResponse("page/home.html", context=context)
"""


def accountExists(email):
    if email == "testuser1@example.org":
        return True
    else:
        return False


@router.post('/page/signup')
def create_signup_page(signup_request: SignupRequest):
    if not accountExists(signup_request.email):
        return {
            "success": True,
            "message": "successfully signed up"
        }
    else:
        return {
            "success": False,
            "message": "Email already exists :)"
        }
