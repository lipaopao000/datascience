import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models import schemas
from backend.models.database_models import Project # For type hinting if needed

# Assuming conftest.py provides 'client', 'db_session', 'test_user', 
# 'authorized_client', 'superuser_client' fixtures

PROJECT_ROUTER_PREFIX = f"{settings.API_V1_STR}/projects"

def test_create_project(authorized_client: TestClient, test_user):
    response = authorized_client.post(
        PROJECT_ROUTER_PREFIX + "/",
        json={"name": "Test Project", "description": "A test project description"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project description"
    assert data["owner_id"] == test_user.id
    assert "id" in data

def test_create_project_unauthenticated(client: TestClient):
    response = client.post(
        PROJECT_ROUTER_PREFIX + "/",
        json={"name": "Unauth Project", "description": "This should fail"},
    )
    assert response.status_code == 401 # Expecting 401 Unauthorized

def test_read_projects_as_owner(authorized_client: TestClient, test_user):
    # Create a project first
    project_data = {"name": "Owned Project", "description": "Project for owner to read"}
    response = authorized_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert response.status_code == 201
    created_project_id = response.json()["id"]
    
    response = authorized_client.get(PROJECT_ROUTER_PREFIX + "/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["id"] == created_project_id and p["name"] == project_data["name"] and p["owner_id"] == test_user.id for p in data)

def test_read_projects_as_superuser(superuser_client: TestClient, test_user, db_session: Session):
    # Regular user creates a project
    from backend.crud import crud_project 
    from backend.models.schemas import ProjectCreate
    
    user_project = crud_project.create_project(db_session, ProjectCreate(name="User's Project by Superuser Test", description="Desc"), owner_id=test_user.id)
    db_session.commit() # Ensure it's committed before superuser tries to read
    
    # Superuser creates a project
    superuser_project_data = {"name": "Superuser Project by Superuser Test", "description": "Superuser's own project"}
    response_su_create = superuser_client.post(PROJECT_ROUTER_PREFIX + "/", json=superuser_project_data)
    assert response_su_create.status_code == 201
    
    response = superuser_client.get(PROJECT_ROUTER_PREFIX + "/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    project_names = [p["name"] for p in data]
    assert user_project.name in project_names
    assert superuser_project_data["name"] in project_names

def test_read_specific_project_as_owner(authorized_client: TestClient, test_user):
    project_data = {"name": "Specific Project by Owner", "description": "Details here"}
    create_response = authorized_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = authorized_client.get(f"{PROJECT_ROUTER_PREFIX}/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["id"] == project_id
    assert data["owner_id"] == test_user.id

def test_read_specific_project_as_superuser(superuser_client: TestClient, test_user, db_session: Session):
    # Project created by a regular user
    from backend.crud import crud_project 
    from backend.models.schemas import ProjectCreate
    user_project = crud_project.create_project(db_session, ProjectCreate(name="User Project For Superuser Read Test", description="Desc"), owner_id=test_user.id)
    db_session.commit()

    response = superuser_client.get(f"{PROJECT_ROUTER_PREFIX}/{user_project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user_project.name
    assert data["id"] == user_project.id

def test_read_specific_project_unauthorized(authorized_client: TestClient, superuser_client: TestClient, test_superuser):
    # Project created by superuser
    project_data = {"name": "Superuser's Secret Project For Unauthorized Test", "description": "Only for superuser"}
    create_response = superuser_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Regular user tries to access it
    response = authorized_client.get(f"{PROJECT_ROUTER_PREFIX}/{project_id}")
    assert response.status_code == 403 # Forbidden

def test_read_nonexistent_project(authorized_client: TestClient):
    response = authorized_client.get(f"{PROJECT_ROUTER_PREFIX}/999999") # Assuming 999999 doesn't exist
    assert response.status_code == 404

def test_update_project_as_owner(authorized_client: TestClient, test_user):
    project_data = {"name": "Original Name For Update", "description": "Original Description"}
    create_response = authorized_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    update_data = {"name": "Updated Name by Owner", "description": "Updated Description"}
    response = authorized_client.put(
        f"{PROJECT_ROUTER_PREFIX}/{project_id}",
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["id"] == project_id
    assert data["owner_id"] == test_user.id

def test_update_project_unauthorized(authorized_client: TestClient, superuser_client: TestClient, test_superuser):
    # Project created by superuser
    project_data = {"name": "Superuser Project To Update Unauthorized", "description": "Initial"}
    create_response = superuser_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Regular user tries to update it
    update_data = {"name": "Attempted Update by User Unauthorized Test"}
    response = authorized_client.put(
        f"{PROJECT_ROUTER_PREFIX}/{project_id}",
        json=update_data,
    )
    assert response.status_code == 403 # Forbidden

def test_update_nonexistent_project(authorized_client: TestClient):
    update_data = {"name": "Nonexistent Update Test"}
    response = authorized_client.put(
        f"{PROJECT_ROUTER_PREFIX}/999999", 
        json=update_data,
    )
    assert response.status_code == 404

def test_delete_project_as_owner(authorized_client: TestClient):
    project_data = {"name": "Project To Delete by Owner", "description": "Will be removed"}
    create_response = authorized_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = authorized_client.delete(f"{PROJECT_ROUTER_PREFIX}/{project_id}")
    assert response.status_code == 200 
    
    get_response = authorized_client.get(f"{PROJECT_ROUTER_PREFIX}/{project_id}")
    assert get_response.status_code == 404

def test_delete_project_unauthorized(authorized_client: TestClient, superuser_client: TestClient, test_superuser):
    # Project created by superuser
    project_data = {"name": "Superuser Project To Delete Unauthorized", "description": "Safe from users"}
    create_response = superuser_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    response = authorized_client.delete(f"{PROJECT_ROUTER_PREFIX}/{project_id}")
    assert response.status_code == 403 

def test_delete_nonexistent_project(authorized_client: TestClient):
    response = authorized_client.delete(f"{PROJECT_ROUTER_PREFIX}/999999") 
    assert response.status_code == 404

def test_read_own_projects_only(authorized_client: TestClient, db_session: Session, test_user):
    project_data_user1 = {"name": "User1 Own Project Test", "description": "Belongs to user1"}
    response_user1 = authorized_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data_user1)
    assert response_user1.status_code == 201
    
    from backend.core.security import get_password_hash
    from backend.models.database_models import User
    from backend.crud import crud_project
    from backend.models.schemas import ProjectCreate

    other_user_username = "otheruser_own_projects_test"
    other_user = db_session.query(User).filter(User.username == other_user_username).first()
    if not other_user:
        other_user = User(username=other_user_username, email="other_own@example.com", hashed_password=get_password_hash("otherpass"), is_active=True)
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
    
    crud_project.create_project(db_session, ProjectCreate(name="OtherUser Project For Isolation Test", description="Belongs to otheruser"), owner_id=other_user.id)
    db_session.commit()

    response = authorized_client.get(PROJECT_ROUTER_PREFIX + "/")
    assert response.status_code == 200
    projects = response.json()
    
    assert any(p["name"] == project_data_user1["name"] and p["owner_id"] == test_user.id for p in projects)
    assert not any(p["name"] == "OtherUser Project For Isolation Test" for p in projects) 

def test_create_project_missing_name(authorized_client: TestClient):
    response = authorized_client.post(
        PROJECT_ROUTER_PREFIX + "/",
        json={"description": "Project with no name test"}, 
    )
    assert response.status_code == 422 

def test_create_project_description_optional(authorized_client: TestClient, test_user):
    # Assumes ProjectCreate schema allows description to be optional (e.g. `description: Optional[str] = None`)
    project_name = "Project with no description test"
    response = authorized_client.post(
        PROJECT_ROUTER_PREFIX + "/",
        json={"name": project_name},
    )
    assert response.status_code == 201 
    data = response.json()
    assert data["name"] == project_name
    assert data.get("description") is None # Or whatever default your model/DB sets
    assert data["owner_id"] == test_user.id

def test_update_project_partial(authorized_client: TestClient, test_user):
    project_data = {"name": "Partial Original Test", "description": "Partial Original Desc Test"}
    create_response = authorized_client.post(PROJECT_ROUTER_PREFIX + "/", json=project_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    update_partial_data = {"name": "Partial Updated Name Test"}
    response = authorized_client.put(
        f"{PROJECT_ROUTER_PREFIX}/{project_id}",
        json=update_partial_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_partial_data["name"]
    assert data["description"] == project_data["description"] 
    assert data["owner_id"] == test_user.id

    update_partial_data_desc = {"description": "Partial Updated Description Test"}
    response_desc = authorized_client.put(
        f"{PROJECT_ROUTER_PREFIX}/{project_id}",
        json=update_partial_data_desc,
    )
    assert response_desc.status_code == 200
    data_desc = response_desc.json()
    assert data_desc["name"] == update_partial_data["name"] 
    assert data_desc["description"] == update_partial_data_desc["description"]
    assert data_desc["owner_id"] == test_user.id

def test_read_projects_pagination(authorized_client: TestClient, test_user, db_session: Session):
    # Clean up projects for this user to ensure pagination test is consistent
    # This is a simple way; ideally, transactions or specific test user per test.
    user_projects = db_session.query(Project).filter(Project.owner_id == test_user.id).all()
    for p in user_projects:
        db_session.delete(p)
    db_session.commit()

    created_projects_names = []
    for i in range(5): # Create 5 new projects for pagination
        name = f"Paginated Project {test_user.id}-{i+1}"
        created_projects_names.append(name)
        response = authorized_client.post(
            PROJECT_ROUTER_PREFIX + "/",
            json={"name": name, "description": f"Desc {i+1}"},
        )
        assert response.status_code == 201

    # Test with limit
    response_limit = authorized_client.get(PROJECT_ROUTER_PREFIX + "/?limit=2")
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert len(data_limit) == 2
    assert data_limit[0]["name"] == created_projects_names[0]
    assert data_limit[1]["name"] == created_projects_names[1]

    # Test with skip and limit
    response_skip_limit = authorized_client.get(PROJECT_ROUTER_PREFIX + "/?skip=2&limit=2")
    assert response_skip_limit.status_code == 200
    data_skip_limit = response_skip_limit.json()
    assert len(data_skip_limit) == 2
    assert data_skip_limit[0]["name"] == created_projects_names[2]
    assert data_skip_limit[1]["name"] == created_projects_names[3]
    
    response_skip_limit_less_results = authorized_client.get(PROJECT_ROUTER_PREFIX + "/?skip=4&limit=2")
    assert response_skip_limit_less_results.status_code == 200
    data_skip_limit_less_results = response_skip_limit_less_results.json()
    assert len(data_skip_limit_less_results) == 1
    assert data_skip_limit_less_results[0]["name"] == created_projects_names[4]

    # Test with a large skip
    response_large_skip = authorized_client.get(PROJECT_ROUTER_PREFIX + "/?skip=10")
    assert response_large_skip.status_code == 200
    assert len(response_large_skip.json()) == 0

def test_update_project_as_superuser(superuser_client: TestClient, test_user, db_session: Session):
    from backend.crud import crud_project
    from backend.models.schemas import ProjectCreate
    user_project = crud_project.create_project(db_session, ProjectCreate(name="User Project For SU Update Test", description="Initial Desc"), owner_id=test_user.id)
    db_session.commit()

    update_data = {"name": "Updated by Superuser Test", "description": "Superuser was here"}
    response = superuser_client.put(
        f"{PROJECT_ROUTER_PREFIX}/{user_project.id}",
        json=update_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["id"] == user_project.id
    assert data["owner_id"] == test_user.id 

def test_delete_project_as_superuser(superuser_client: TestClient, test_user, db_session: Session):
    from backend.crud import crud_project
    from backend.models.schemas import ProjectCreate
    user_project = crud_project.create_project(db_session, ProjectCreate(name="User Project For SU Delete Test", description="Initial Desc"), owner_id=test_user.id)
    db_session.commit()

    response = superuser_client.delete(f"{PROJECT_ROUTER_PREFIX}/{user_project.id}")
    assert response.status_code == 200 

    get_response = superuser_client.get(f"{PROJECT_ROUTER_PREFIX}/{user_project.id}") 
    assert get_response.status_code == 404
