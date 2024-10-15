import os
from typing_extensions import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

#from fairscape_mds.routers.user import router as UserRouter
from fairscape_mds.routers.schema import router as SchemaRouter
from fairscape_mds.routers.auth import router as AuthRouter
from fairscape_mds.routers.software import router as SoftwareRouter
from fairscape_mds.routers.dataset import router as DatasetRouter
from fairscape_mds.routers.rocrate import router as ROCrateRouter
from fairscape_mds.routers.computation import router as ComputationRouter
from fairscape_mds.routers.project import router as ProjectRouter
from fairscape_mds.routers.organization import router as OrganizationRouter
from fairscape_mds.routers.evidencegraph import router as EvidenceGraphRouter
from fairscape_mds.routers.transfer import router as TransferRouter
from fairscape_mds.routers.resolver import ResolverRouter


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
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
    openapi_tags=tags_metadata
)


#static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

# mounting templates
app.mount("/api/static", StaticFiles(directory='fairscape_mds/static'), name="static")
templates = Jinja2Templates(directory="fairscape_mds/templates")


@app.get('/api', response_class=HTMLResponse, tags=["Root"])
async def get_root(request: Request):
    context = {
        "request": request
    }
    return templates.TemplateResponse("page/index.html", context=context)

@app.get('/api/healthz')
async def healthcheck():
    return JSONResponse(
        status_code=200,
        content={"status": "server is healthy"}
    )

# Routes for the API
#app.include_router(UserRouter, prefix="/api" tags=["user"])
#app.include_router(GroupRouter, prefix="/api", tags=["group"])
#app.include_router(ProjectRouter, prefix="/api", tags=["project"])
#app.include_router(TransferRouter, prefix="/api",tags=["transfer"])

app.include_router(AuthRouter, prefix="/api", tags=["auth"])
app.include_router(SoftwareRouter, prefix="/api", tags=["software"])
app.include_router(DatasetRouter,prefix="/api", tags=["dataset"])
app.include_router(ROCrateRouter, prefix="/api",tags=["rocrate"])
app.include_router(ComputationRouter, prefix="/api", tags=["computation"])
app.include_router(OrganizationRouter, prefix="/api", tags=["organization"])
app.include_router(EvidenceGraphRouter,prefix="/api", tags=["evidencegraph"])
app.include_router(ResolverRouter, prefix="/api",tags=["resolver"])
app.include_router(SchemaRouter, prefix="/api", tags=["schema"])

# Routes for Web pages
#app.include_router(WebIndexRouter, tags=["webindex"])
#app.include_router(WebSigninRouter, tags=["websignin"])
#app.include_router(WebSignupRouter, tags=["websignup"])
#app.include_router(WebHomeRouter, tags=["webhome"])

#@app.get("/page/{page_name}", response_class=HTMLResponse)
#def show_page(request: Request, page_name: str):
#    return templates.TemplateResponse("page/" + page_name + ".html", {"request": request})


