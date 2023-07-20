from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from mds.routers.user import router as UserRouter
from mds.routers.group import router as GroupRouter
from mds.routers.software import router as SoftwareRouter
from mds.routers.dataset import router as DatasetRouter
from mds.routers.rocrate import router as ROCrateRouter
from mds.routers.computation import router as ComputationRouter
from mds.routers.project import router as ProjectRouter
from mds.routers.organization import router as OrganizationRouter
from mds.routers.evidencegraph import router as EvidenceGraphRouter
from mds.routers.transfer import router as TransferRouter

from mds.web.routers.index import router as WebIndexRouter
from mds.web.routers.signin import router as WebSigninRouter
from mds.web.routers.signup import router as WebSignupRouter
from mds.web.routers.home import router as WebHomeRouter
from mds.routers.auth import router as AuthHandlerRouter


tags_metadata = [
    {
        "name": "user",
        "description": "Operations with users.",
    },
    {
        "name": "group",
        "description": "Operations with groups.",
    },
    {
        "name": "software",
        "description": "Operations with software.",
    },
    {
        "name": "dataset",
        "description": "Operations with dataset.",
    },
    {
        "name": "rocrate",
        "description": "Operations with rocrate.",
    },
    {
        "name": "computation",
        "description": "Operations with computation.",
    },
    {
        "name": "project",
        "description": "Operations with project.",
    },
    {
        "name": "organization",
        "description": "Operations with organization.",
    },
    {
        "name": "evidencegraph",
        "description": "Operations with evidencegraph.",
    },
    {
        "name": "transfer",
        "description": "Operations with Object Transfer.",
    },
    {
        "name": "compute",
        "description": "Operations with Performing Computation.",
    }

]


app = FastAPI(
    title="Fairscape Metadata Service (MDS)",
    description="",
    version="0.1.0",
    #terms_of_service="http://example.com/terms/",
    contact={
        "name": "Max Levinson",
        "email": "mal8ch@virginia.edu",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=tags_metadata
)


# mounting templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get('/', response_class=HTMLResponse, tags=["Root"])
async def get_root(request: Request):
    context = {
        "request": request
    }
    return templates.TemplateResponse("/page/index.html", context=context)

@app.get('/healthz')
async def healthcheck():
    return JSONResponse(
        status_code=200,
        content={"status": "server is healthy"}
    )

# Routes for the API
app.include_router(UserRouter, tags=["user"])
app.include_router(GroupRouter, tags=["group"])
app.include_router(SoftwareRouter, tags=["software"])
app.include_router(DatasetRouter, tags=["dataset"])
app.include_router(ROCrateRouter, tags=["rocrate"])
app.include_router(ComputationRouter, tags=["computation"])
app.include_router(ProjectRouter, tags=["project"])
app.include_router(OrganizationRouter, tags=["organization"])
app.include_router(EvidenceGraphRouter, tags=["evidencegraph"])
app.include_router(TransferRouter, tags=["transfer"])

# Routes for Web pages
app.include_router(WebIndexRouter, tags=["webindex"])
#app.include_router(WebSigninRouter, tags=["websignin"])
#app.include_router(WebSignupRouter, tags=["websignup"])
app.include_router(WebHomeRouter, tags=["webhome"])
app.include_router(AuthHandlerRouter, tags=["webauth"])

@app.get("/page/{page_name}", response_class=HTMLResponse)
def show_page(request: Request, page_name: str):
    return templates.TemplateResponse("page/" + page_name + ".html", {"request": request})

from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from mds.config import (
    get_minio,
    get_casbin,
    get_mongo,
    MongoConfig,
    CasbinConfig
) 

from mds.models.auth import (
    Session,
    LoginUserBasic
)

mongo_config = get_mongo()
mongo_client = mongo_config.CreateClient()


@app.post("/token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    mongo_db = mongo_client[mongo_config.db]
    mongo_collection = mongo_db[mongo_config.collection]

    try:
        session = LoginUserBasic(mongo_collection, form_data.username, form_data.password) 

    except UserNotFound:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": session.encode(), "token_type": "bearer"}


