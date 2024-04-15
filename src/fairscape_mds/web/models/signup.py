from fastapi import Form
from pydantic import BaseModel


# Compatible with POST when sent via ajax requests
class SignupRequest(BaseModel):
    firstName: str
    lastName: str
    email: str
    password1: str
    password2: str


# Compatible with POST when sent via form directly
class SignupForm(BaseModel):
    # must match with name="firstName" in the signup html form
    firstName: str
    # must match with name="lastName" in the signup html form
    lastName: str
    # must match with name="email" in the signup html form
    email: str
    # must match with name="password1" in the signup html form
    password1: str
    # must match with name="password2" in the signup html form
    password2: str

    @classmethod
    def as_form(cls, firstName: str = Form(...), lastName: str = Form(...), email: str = Form(...),
                password1: str = Form(...), password2: str = Form(...)):
        return cls(firstName=firstName, lastName=lastName, email=email, password1=password1, password2=password2)
