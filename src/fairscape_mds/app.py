import os
from typing_extensions import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from fairscape_mds.routers.schema import router as SchemaRouter
from fairscape_mds.routers.auth import router as AuthRouter
from fairscape_mds.routers.software import router as SoftwareRouter
from fairscape_mds.routers.dataset import router as DatasetRouter
from fairscape_mds.routers.rocrate import router as ROCrateRouter
from fairscape_mds.routers.computation import router as ComputationRouter
from fairscape_mds.routers.evidencegraph import router as EvidenceGraphRouter
from fairscape_mds.routers.resolver import ResolverRouter
from fairscape_mds.routers.publish import router as PublishRouter


tags_metadata = [
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
        "name": "evidencegraph",
        "description": "Operations with evidencegraph.",
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
    version="1.0.0",
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


@app.get('/api/healthz')
def healthcheck():
    # TODO check that configured connections are working

    return JSONResponse(
        status_code=200,
        content={"status": "server is healthy"}
    )

app.include_router(AuthRouter, prefix="/api", tags=["auth"])
app.include_router(SoftwareRouter, prefix="/api", tags=["software"])
app.include_router(DatasetRouter,prefix="/api", tags=["dataset"])
app.include_router(ROCrateRouter, prefix="/api",tags=["rocrate"])
app.include_router(ComputationRouter, prefix="/api", tags=["computation"])
app.include_router(EvidenceGraphRouter,prefix="/api", tags=["evidencegraph"])
app.include_router(ResolverRouter, prefix="/api",tags=["resolver"])
app.include_router(SchemaRouter, prefix="/api", tags=["schema"])
app.include_router(PublishRouter, prefix="/api", tags=["publish"])
