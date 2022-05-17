from fastapi import APIRouter, Response

from mds.database import mongo
from mds.models.project import Project, list_project

router = APIRouter()


@router.post("/project")
def project_create(project: Project, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    create_status = project.create(mongo_collection)

    mongo_client.close()

    if create_status.success:
        return {"created": {"@id": project.id, "@type": "project"}}
    else:
        response.status_code = create_status.status_code
        return {"error": create_status.message}


@router.get("/project")
def project_list(response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client["test"]
    mongo_collection = mongo_db["testcol"]

    project = list_project(mongo_collection)

    mongo_client.close()

    return project


@router.get("/project/ark:{NAAN}/{postfix}")
def project_get(NAAN: str, postfix: str, response: Response):
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
        response.status_code = read_status.status_code
        return {"error": read_status.message}


@router.put("/project")
def project_update(project: Project, response: Response):
    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    update_status = project.update(mongo_collection)

    mongo_client.close()

    if update_status.success:
        return {"updated": {"@id": project.id, "@type": "project"}}
    else:
        response.status_code = update_status.status_code
        return {"error": update_status.message}


@router.delete("/project/ark:{NAAN}/{postfix}")
def project_delete(NAAN: str, postfix: str):
    project_id = f"ark:{NAAN}/{postfix}"

    mongo_client = mongo.GetConfig()
    mongo_db = mongo_client['test']
    mongo_collection = mongo_db['testcol']

    project = Project.construct(id=project_id)

    delete_status = project.delete(mongo_collection)

    mongo_client.close()

    if delete_status.success:
        return {"deleted": {"@id": project_id}}
    else:
        return {"error": f"{str(delete_status.message)}"}
