from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from mds.database import mongo
from mds.models.project import Project, list_project

router = APIRouter()


@router.post("/project",
             summary="Create a project",
             response_description="The created project")
def project_create(project: Project, response: Response):
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

    create_status = project.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
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
def project_get(NAAN: str, postfix: str, response: Response):
    """
    Retrieves a project based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    project_id = f"ark:{NAAN}/{postfix}"

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
def project_update(project: Project, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

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
def project_delete(NAAN: str, postfix: str):
    """
    Deletes a project based on a given identifier:

    - **NAAN**: Name Assigning Authority Number which uniquely identifies an organization e.g. 12345
    - **postfix**: a unique string
    """
    project_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

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
