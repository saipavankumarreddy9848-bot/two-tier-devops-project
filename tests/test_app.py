
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}


def test_create_employee_requires_name(client):
    response = client.post(
        "/employees",
        json={"email": "test@example.com"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Name is required"


def test_create_employee_requires_email(client):
    response = client.post(
        "/employees",
        json={"name": "Test Employee"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email is required"
