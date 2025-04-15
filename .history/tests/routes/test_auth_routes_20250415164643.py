from unittest.mock import Mock, patch

import pytest
from sqlalchemy import select

from src.entity.models import User
from tests.conftest import TestingSessionLocal

user_data = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}

def test_register(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/api/auth/register", json=user_data) 
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data

def test_repeat_register_username(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    user_copy = user_data.copy()
    user_copy["email"] = "kot_leapold@gmail.com"
    response = client.post("/api/auth/register", json=user_copy)  
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "User already exists"

def test_repeat_register_email(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    user_copy = user_data.copy()
    user_copy["username"] = "kot_leapold"
    response = client.post("/api/auth/register", json=user_copy)  
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Email already exists"

def test_not_confirmed_login(client):
    response = client.post("/api/auth/login",  
                           data={"username": user_data.get("username"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email address not confirmed"

@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post("/api/auth/login",  
                           data={"username": user_data.get("username"), "password": user_data.get("password")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_wrong_password_login(client):
    response = client.post("/api/auth/login",  # Changed path
                           data={"username": user_data.get("username"), "password": "password"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_wrong_username_login(client):
    response = client.post("/api/auth/login",  # Changed path
                           data={"username": "username", "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Incorrect username or password"

def test_validation_error_login(client):
    response = client.post("/api/auth/login",  # Changed path
                           data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data

def test_refresh_token(client):
    response = client.post("/api/auth/login",  # Changed path
                           data={"username": user_data.get("username"), "password": user_data.get("password")})
    refresh_token = response.json().get("refresh_token")

    response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})  # Changed path
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != refresh_token

def test_logout(client):
    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        response = client.post("/api/auth/login",  # Changed path
                               data={"username": user_data.get("username"), "password": user_data.get("password")})
        assert response.status_code == 200, response.text
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        response = client.post("/api/auth/logout", json={"refresh_token": refresh_token},  # Changed path
                               headers={"Authorization": f"Bearer {access_token}"})
        assert response.status_code == 204, response.text

# Run this test with:
# pytest tests/routes/test_auth_routes.py
