import os
import tempfile

# Use a separate SQLite database for tests.
# This must be set BEFORE importing main.py.
TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB.close()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.name}"

from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app


client = TestClient(app)


def setup_function():
    """Create a clean database before every test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module():
    """Close database connections after the test module."""
    engine.dispose()

    try:
        os.remove(TEST_DB.name)
    except FileNotFoundError:
        pass


def register_user():
    response = client.post(
        "/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_user():
    response = client.post(
        "/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_duplicate_registration():
    register_user()

    response = client.post(
        "/register",
        json={
            "name": "Another User",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login():
    register_user()

    response = client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_login():
    register_user()

    response = client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_create_expense_requires_authentication():
    response = client.post(
        "/expenses",
        json={
            "title": "Internet",
            "amount": 100,
            "category": "Bills",
        },
    )

    assert response.status_code == 401


def test_create_expense():
    token = register_user()

    response = client.post(
        "/expenses",
        json={
            "title": "Internet",
            "amount": 100,
            "category": "Bills",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Internet"
    assert data["amount"] == 100
    assert data["category"] == "Bills"
    assert "id" in data


def test_list_expenses():
    token = register_user()

    client.post(
        "/expenses",
        json={
            "title": "Internet",
            "amount": 100,
            "category": "Bills",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/expenses",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Internet"


def test_get_expense():
    token = register_user()

    create_response = client.post(
        "/expenses",
        json={
            "title": "Transport",
            "amount": 50,
            "category": "Travel",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    expense_id = create_response.json()["id"]

    response = client.get(
        f"/expenses/{expense_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Transport"


def test_update_expense():
    token = register_user()

    create_response = client.post(
        "/expenses",
        json={
            "title": "Food",
            "amount": 50,
            "category": "Meals",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    expense_id = create_response.json()["id"]

    response = client.put(
        f"/expenses/{expense_id}",
        json={
            "title": "Dinner",
            "amount": 75,
            "category": "Restaurant",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Dinner"
    assert data["amount"] == 75
    assert data["category"] == "Restaurant"


def test_delete_expense():
    token = register_user()

    create_response = client.post(
        "/expenses",
        json={
            "title": "Shopping",
            "amount": 200,
            "category": "Personal",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    expense_id = create_response.json()["id"]

    response = client.delete(
        f"/expenses/{expense_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Expense deleted"

    get_response = client.get(
        f"/expenses/{expense_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert get_response.status_code == 404


def test_expense_not_found():
    token = register_user()

    response = client.get(
        "/expenses/9999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Expense not found"