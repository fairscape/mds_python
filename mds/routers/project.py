from typing import Union
from fastapi import APIRouter, Response, Header
from fastapi.responses import JSONResponse
from mds.database import mongo, casbin
from mds.models.project import Project, list_project
from mds.models.auth import ParseAuthHeader, UserNotFound, TokenError

router = APIRouter()


@router.post("/project",
             summary="Create a project",
             response_description="The created project"
            )
def project_create(
    project: Project, 
    Authorization: Union[str, None] = Header(default=None)
    ):
    """
    Create a project with the following properties:

    - **@id**: a unique identifier
    - **@type**: evi:Project
    - **name**: a name
    - **owner**: an existing user in its compact form with @id, @type, name, and email
    """

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    enforcer = casbin.GetEnforcer()
    enforcer.load_policy()

    # decode the credentials and find the user
    try:
        calling_user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )

    # check that user has permissions on the Organization
    # they are creating a project for
    org_id = project.memberOf.id

    if enforcer.Enforce(calling_user.id, "createProject", org_id) != True:
        return JSONResponse(
            status_code=401,
            content={
                "error": "User Missing Permission",
                "message": "user does not have permission to create project in this organization",
                "permission": {
                    "sub": calling_user.id,
                    "pred": "createProject",
                    "obj": org_id
                    }
                }
        )

  
    create_status = project.create(mongo_collection)
    mongo_client.close()

    if create_status.success:

        # add policies to casbin for owner user to mongo
        enforcer.add_policy(calling_user.id, "read", project.id)
        enforcer.add_policy(calling_user.id, "update", project.id)
        enforcer.add_policy(calling_user.id, "delete", project.id)
        enforcer.add_policy(calling_user.id, "createDataset", project.id)
        enforcer.add_policy(calling_user.id, "createSoftware", project.id)
        enforcer.add_policy(calling_user.id, "createComputation", project.id)
        enforcer.add_policy(calling_user.id, "manage", project.id)
        enforcer.save_policy()

        return JSONResponse(
            status_code=201,
            content={"created": {"@id": project.id, "@type": "Project"}}
        )
    else:
        return JSONResponse(
            status_code=create_status.status_code,
            content={"error": create_status.message}
        )


@router.get("/project",
            summary="List all projects",
            response_description="Retrieved list of projects")
def project_list(response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    project = list_project(mongo_collection)

    mongo_client.close()

    return project


@router.get("/project/ark:{NAAN}/{postfix}",
            summary="Retrieve a project",
            response_description="The retrieved project")
def project_get(
    NAAN: str, 
    postfix: str, 
    Authorization: Union[str, None] = Header(default=None)
    ):
    """
    Retrieves a project based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """

    project_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    enforcer = casbin.GetEnforcer()
    enforcer.load_policy()

    # decode the auth header and find the user 
    try:
        user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )
    

    if enforcer.Enforce(user.id, "read", project_id) != True:
        return JSONResponse(
            status_code=401,
            content={}
        ) 


    project = Project.construct(id=project_id)
    read_status = project.read(mongo_collection)

    mongo_client.close()

    if read_status.success:
        return project
    else:
        return JSONResponse(status_code=read_status.status_code,
                            content={"error": read_status.message})


@router.put("/project",
            summary="Update a project",
            response_description="The updated project")
def project_update(
    project: Project, 
    Authorization: Union[str, None] = Header(default=None)
    ):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    enforcer = casbin.GetEnforcer()
    enforcer.load_policy()

    # decode the auth header and find the user 
    try:
        user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )

    # enforce permissions on the project
    if enforcer.Enforce(user.id, "update", project.id) != True:
        return JSONResponse(
            status_code=401,
            content={"error": "user lacks permission to update project"}
        ) 

    update_status = project.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return JSONResponse(
            status_code=200,
            content={"updated": {"@id": project.id, "@type": "Project"}}
        )
    else:
        return JSONResponse(
            status_code=update_status.status_code,
            content={"error": update_status.message}
        )


@router.delete("/project/ark:{NAAN}/{postfix}",
               summary="Delete a project",
               response_description="The deleted project")
def project_delete(
    NAAN: str, 
    postfix: str,
    Authorization: Union[str, None] = Header(default=None)
    ):
    """
    Deletes a project based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    project_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    enforcer = casbin.GetEnforcer()
    enforcer.load_policy()

    # decode the auth header and find the user 
    try:
        user = ParseAuthHeader(mongo_collection, Authorization)
    except UserNotFound:
        return JSONResponse(
            status_code=401,
            content={"error": "user not found"}
        )
    except TokenError as token_error:
        return JSONResponse(
            status_code=401,
            content={"error": "session not active", "message": token_error.message}
        )

    # enforce permissions on the project
    if enforcer.Enforce(user.id, "delete", project_id) != True:
        return JSONResponse(
            status_code=401,
            content={"error": "user lacks permission to delete project"}
        ) 

    project = Project.construct(id=project_id)
    delete_status = project.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return JSONResponse(
            status_code=200,
            content={"deleted": {"@id": project_id, "@type": "Project", "name": project.name}}
        )
    else:
        return JSONResponse(
            status_code=delete_status.status_code,
            content={"error": f"{str(delete_status.message)}"}
        )
