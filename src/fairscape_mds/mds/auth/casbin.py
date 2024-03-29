import casbin

def createUser(
    casbinEnforcer: casbin.Enforcer, 
    userEmail: str, 
    userId: str
)->None:
    """ Create a fairscape user

    The following policies are inserted into the policy database of casbin
    ```
    p, email, /user/:userid, (GET)|(PUT)|(DELETE)
    p, email, /group, (POST) 
    p, email, /project, (POST)
    p, email, /organization, (POST) 
    p, email, /computation, (POST)
    p, email, /software, (POST)
    p, email, /dataset, (POST)
    ```
    """
 
    casbinEnforcer.add_policies([
        (userEmail, f"/user/{userId}", "(GET)|(PUT)|(DELETE)"), 
        (userEmail, "/group", "(POST)"),
        (userEmail, "/project", "(POST)"),
        (userEmail, "/organization", "(POST)"),
        (userEmail, "/computation", "(POST)"),
        (userEmail, "/software", "(POST)"),
        (userEmail, "/dataset", "(POST)")
    ])
    
    return None


    

def createSuperUser():
    """ Create a fairscape superuser
    """
    # TODO enable super user 
    pass

# GROUP

def createGroup(enforcer, userEmail, groupId)-> None:

    enforcer.add_policies([
        (userEmail, f"/group/{groupId}", "(GET)|(PUT)|(DELETE)"),
    ])

    # add the user to the policy
    enforcer.add_grouping_policy(userEmail, groupId)

    enforcer.add_policies([
        (groupId, f"/group/{groupId}", "(GET)")
    ])
    
    return None


def addUserToGroup(enforcer, userEmail, groupId):
    # add the user to the policy
    enforcer.add_grouping_policy(userEmail, groupId)
    
    return None


def removeUserFromGroup(enforcer, userEmail, groupId):
    # TODO check if this is the owner
    
    # if the only member of the group remains raise exception
    if len(enforcer.get_filtered_grouping_policy(groupId))==1:
        raise Exception("Can't Remove Last Memeber of Group")
    
    enforcer.remove_grouping_policy(userEmail, groupId)
    
    return None


def deleteGroup(enforcer, groupId)-> None:
    enforcer.delete_role(groupId)
    
    return None


# ORGANIZATION

def createOrganization(casbinEnforcer: casbin.Enforcer, userEmail: str, organizationID: str) -> None:
    casbinEnforcer.add_policies([
        (userEmail, f"/organization/{organizationID}", "(GET)|(PUT)|(DELETE)"),
    ])
    
    return None


def deleteOrganization(casbinEnforcer: casbin.Enforcer, organizationID: str) -> None:
    deleted_policy = casbinEnforcer.remove_filtered_policy(1, f"/organization/{organizationID}")
    if not deleted_policy:
        raise PolicyNotFoundException()


def addUserToOrganization(casbinEnforcer: casbin.Enforcer, userEmail: str, organizationID: str) -> None:
    casbinEnforcer.add_policies([
        (userEmail, f"/organization/{organizationID}", "(GET)|(PUT)"),
    ])
    
    return None


def removeUserFromOrganization(casbinEnforcer: casbin.Enforcer, userEmail: str, organizationID: str) -> None:
    
    # if it is the owner raise exception
    is_user_admin = casbinEnforcer.enforce(
        userEmail, 
        f"/organization/{organizationID}", 
        "DELETE"
    )

    # can't remove admins from their own group
    if is_user_admin:
       raise Exception(f"User: {userEmail} is an admin of organization {organizationID}")
    
    # otherwise remove member from organization
    casbinEnforcer.remove_filtered_policy(
        0, userEmail, f"/organization/{organizationID}", "(GET)|(PUT)"
    )
    return None


def addGroupToOrganization(casbinEnforcer: casbin.Enforcer, groupID: str, organizationID: str) -> None:
    casbinEnforcer.add_policies([
        (groupID, f"/organization/{organizationID}", "(GET)|(PUT)"),
    ])
    
    return None


def removeGroupFromOrganization(casbinEnforcer: casbin.Enforcer, groupID: str, organizationID: str) -> None:
    casbinEnforcer.remove_filtered_policy(
        0, groupID, f"/organization/{organizationID}", "(GET)|(PUT)"
    )
    return None


class PolicyNotFoundException(Exception):

    def __init__(
        self, 
        message="No Casbin Policy Found", 
        sub: str = "", 
        obj: str = "", 
        act: str = ""
    ):
        self.message = message
        self.sub = sub
        self.obj = obj
        self.act = act
        super().__init__(self.message)


class ObjectPermission():

    def __init__(objectId: str)-> None:
        self.objectId = objectId

    
    def create(
        casbinEnforcer: casbin.Enforcer, 
        userEmail:str, 
        action: str = "(GET)|(PUT)|(DELETE)"
    )-> None:
        casbinEnforcer.add_policy(userEmail, self.objectId, action)
        return None

    def delete(
        casbinEnforcer: casbin.Enforcer,
        objectURL: str
    )-> None:
        deleted_policy = casbinEnforcer.remove_filtered_policy(1, objectURL)
        if not deleted_policy:
            raise PolicyNotFoundException()
        return None
    
    def addPermission(
        casbinEnforcer: casbin.Enforcer, 
        userEmail: str, 
        action: str = "(GET)|(PUT)"
    )-> None:
        casbinEnforcer.add_policy(userEmail, self.objectId, action)
        return None

    
    def removePermission(
        casbinEnforcer: casbin.Enforcer, 
        subjectId: str, 
        action: str = "(GET)|(PUT)"
    )-> None:
         # otherwise remove member from organization
        removed_policy = casbinEnforcer.remove_filtered_policy(0, subjectId, self.objectId, action)
        if not removed_policy:
            raise PolicyNotFoundException()
        return None

def createProject():
    pass

def addUserToProject():
    pass

def addGroupToProject():
    pass

def removeGroupFromProject():
    pass


