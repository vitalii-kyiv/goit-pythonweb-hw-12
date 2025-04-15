from unittest.mock import patch, AsyncMock
from json import dumps
from tests.conftest import test_user

def test_get_me(client, get_token):
    cached_user_json = dumps({
        "id": 1,
        "username": test_user["username"],
        "email": test_user["email"],
        "hash_password": "fake_hashed_password",
        "avatar": "https://twitter.com/gravatar",
        "confirmed": True,
        "role": "admin"
    })

    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists = AsyncMock(side_effect=lambda key: False if key.startswith("bl:") else True)
        redis_mock.get = AsyncMock(return_value=cached_user_json)

        headers = {"Authorization": f"Bearer {get_token}"}
        response = client.get("api/users/me", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert "avatar" in data



@patch("src.services.upload_file_service.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):
    cached_user_json = dumps({
        "id": 1,
        "username": test_user["username"],
        "email": test_user["email"],
        "hash_password": "fake_hashed_password",
         "avatar": "http://example.com/old_avatar.jpg",
        "confirmed": True,
        "role": "admin"
    })

    with patch("src.services.auth.redis_client") as redis_mock:
        redis_mock.exists = AsyncMock(side_effect=lambda key: False if key.startswith("bl:") else True)
        redis_mock.get = AsyncMock(return_value=cached_user_json)

        fake_url = "http://example.com/avatar.jpg"
        mock_upload_file.return_value = fake_url

        headers = {"Authorization": f"Bearer {get_token}"}
        file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

        response = client.patch("/api/users/avatar", headers=headers, files=file_data)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["username"] == test_user["username"]
        assert data["email"] == test_user["email"]
        assert data["avatar"] == fake_url

        mock_upload_file.assert_called_once()



# Run this test with:
