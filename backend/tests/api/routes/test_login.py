from fastapi import status


def test_get_access_token_valid(client, user):
    login_data = {
        "username": user["email"],
        "password": user["password"],
    }

    response = client.post("/api/login/access-token", data=login_data)
    
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]


def test_get_access_token_invalid(client, user):
    login_data = {
        "username": user["email"],
        "password": "WRONG PASSWORD",
    }

    response = client.post("/api/login/access-token", data=login_data)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
