import pytest
from faker import Faker
from unittest.mock import patch

# Ініціалізація Faker для генерації унікальних даних
fake = Faker()

# Генеруємо унікальні дані для тестів
def generate_contact_data():
    """Генерация тестовых данных для контакта"""
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "phone_number": fake.phone_number()[:15],
        "birthday": str(fake.date_of_birth(minimum_age=18, maximum_age=80)),
        "additional_info": fake.sentence(nb_words=5)
    }

@pytest.fixture
def auth_headers(get_token):
    """Фикстура для получения заголовков авторизации"""
    return {"Authorization": f"Bearer {get_token}"}

def test_create_contact(client, auth_headers):
    """Тест создания нового контакта"""
    # Мокуємо redis_client і функцію cache_user
    # Шлях "src.services.cache_user.cache_user" відповідає імпорту:
    # from src.services.cache_user import cache_user
    with patch("src.services.auth.redis_client") as redis_mock, patch("src.services.cache_user.cache_user") as cache_mock:
        redis_mock.exists.return_value = False
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        cache_mock.return_value = None
        contact_data = generate_contact_data()
        response = client.post("/api/contacts/", json=contact_data, headers=auth_headers)
        assert response.status_code == 201, response.text
        result = response.json()
        assert result["first_name"] == contact_data["first_name"]
        assert result["email"] == contact_data["email"]
        assert "id" in result

def test_get_contacts(client, auth_headers):
    """Тест получения списка контактов"""
    # Аналогічно мокуємо redis_client і cache_user
    with patch("src.services.auth.redis_client") as redis_mock, patch("src.services.cache_user.cache_user") as cache_mock:
        redis_mock.exists.return_value = False
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        cache_mock.return_value = None
        # Створюємо тестовий контакт
        contact_data = generate_contact_data()
        client.post("/api/contacts/", json=contact_data, headers=auth_headers)

        response = client.get("/api/contacts/", headers=auth_headers)
        assert response.status_code == 200, response.text
        contacts = response.json()
        assert isinstance(contacts, list)
        assert len(contacts) >= 1

def test_get_contact_by_id(client, auth_headers):
    """Тест получения контакта по ID"""
    # Аналогічно мокуємо redis_client і cache_user
    with patch("src.services.auth.redis_client") as redis_mock, patch("src.services.cache_user.cache_user") as cache_mock:
        redis_mock.exists.return_value = False
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        cache_mock.return_value = None
        contact_data = generate_contact_data()
        created = client.post("/api/contacts/", json=contact_data, headers=auth_headers).json()
        contact_id = created["id"]

        response = client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
        assert response.status_code == 200, response.text
        fetched = response.json()
        assert fetched["id"] == contact_id
        assert fetched["email"] == contact_data["email"]

def test_update_contact(client, auth_headers):
    """Тест обновления контакта"""
    # Создаем тестовый контакт
    contact_data = generate_contact_data()
    created = client.post("/api/contacts/", json=contact_data, headers=auth_headers).json()
    contact_id = created["id"]
    
    # Обновляем контакт
    updated_data = generate_contact_data()
    response = client.put(f"/api/contacts/{contact_id}", json=updated_data, headers=auth_headers)
    assert response.status_code == 200
    updated = response.json()
    assert updated["first_name"] == updated_data["first_name"]
    assert updated["email"] == updated_data["email"]

def test_delete_contact(client, auth_headers):
    """Тест удаления контакта"""
    # Создаем тестовый контакт
    contact_data = generate_contact_data()
    created = client.post("/api/contacts/", json=contact_data, headers=auth_headers).json()
    contact_id = created["id"]
    
    # Удаляем контакт
    response = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Проверяем, что контакт удален
    get_response = client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert get_response.status_code == 404

# Run this test with:
# pytest tests/routes/test_contacts_routes.py