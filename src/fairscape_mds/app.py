import os
from typing_extensions import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from fastapi.middleware.cors import CORSMiddleware
from fairscape_mds.routers.user import router as UserRouter
from fairscape_mds.routers.schema import router as SchemaRouter
#from fairscape_mds.routers.group import router as GroupRouter
from fairscape_mds.routers.software import router as SoftwareRouter
from fairscape_mds.routers.dataset import router as DatasetRouter
from fairscape_mds.routers.rocrate import router as ROCrateRouter
from fairscape_mds.routers.computation import router as ComputationRouter
from fairscape_mds.routers.project import router as ProjectRouter
from fairscape_mds.routers.organization import router as OrganizationRouter
from fairscape_mds.routers.evidencegraph import router as EvidenceGraphRouter
from fairscape_mds.routers.transfer import router as TransferRouter
from fairscape_mds.routers.resolver import ResolverRouter

from fairscape_mds.config import (
    get_mongo_config,
    get_mongo_client
) 

mongo_config = get_mongo_config()
mongo_client = get_mongo_client()

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
    },
        {
        "name": "schema",
        "description": "Operations with Schemas.",
    }

]


app = FastAPI(
    title="Fairscape Metadata Service (MDS)",
    description="",
    version="0.1.0",
    contact={
        "name": "Max Levinson",
        "email": "mal8ch@virginia.edu",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/license/MIT"
    },
    openapi_tags=tags_metadata
)

origins = [
    "http://localhost:5173",  # Your frontend origin
    "http://localhost:8080",  # Your backend origin
    # Add other origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

# mounting templates
app.mount("/static", StaticFiles(directory='fairscape_mds/static'), name="static")
templates = Jinja2Templates(directory="fairscape_mds/templates")


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
#app.include_router(GroupRouter, tags=["group"])
app.include_router(SoftwareRouter, tags=["software"])
app.include_router(DatasetRouter, tags=["dataset"])
app.include_router(ROCrateRouter, tags=["rocrate"])
app.include_router(ComputationRouter, tags=["computation"])
app.include_router(ProjectRouter, tags=["project"])
app.include_router(OrganizationRouter, tags=["organization"])
app.include_router(EvidenceGraphRouter, tags=["evidencegraph"])
app.include_router(TransferRouter, tags=["transfer"])
app.include_router(ResolverRouter, tags=["resolver"])
app.include_router(SchemaRouter, tags=["schema"])

# Routes for Web pages
#app.include_router(WebIndexRouter, tags=["webindex"])
#app.include_router(WebSigninRouter, tags=["websignin"])
#app.include_router(WebSignupRouter, tags=["websignup"])
#app.include_router(WebHomeRouter, tags=["webhome"])

@app.get("/page/{page_name}", response_class=HTMLResponse)
def show_page(request: Request, page_name: str):
    return templates.TemplateResponse("page/" + page_name + ".html", {"request": request})


