from fastapi import FastAPI
from mds.routers.user import router as UserRouter
from mds.routers.group import router as GroupRouter
from mds.routers.software import router as SoftwareRouter


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
    }
]

app = FastAPI(
    title="Fairscape Metadata Service (MDS)",
    description="[Write a description]",
    version="0.0.1",
    contact={
        "name": "ENTER CONTACT NAME",
        "email": "mal8ch@virginia.edu",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=tags_metadata)

# @app.get('/', tags=["Root"])
# async def root():
#    return {"message": "Welcome to FAIRSCAPE Metadata Service"}


app.include_router(UserRouter, tags=["user"])
app.include_router(GroupRouter, tags=["group"])
app.include_router(SoftwareRouter, tags=["software"])
# app.include_router(DatasetRouter, tags=["dataset"])
# app.include_router(ComputationRouter, tags=["computation"])
# app.include_router(ProjectRouter, tags=["project"])
