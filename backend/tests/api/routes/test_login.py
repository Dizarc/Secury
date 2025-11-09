#TODO: Change all status codes to constants

def test_get_access_token_invalid(client, user):
    login_data = {
        "username": user["email"],
        "password": user["password"],
    }

    response = client.post("/api/login/access-token", data=login_data)
    
    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]


def test_get_access_token_invalid(client, user):
    login_data = {
        "username": user["email"],
        "password": "WRONG PASSWORD",
    }

    response = client.post("/api/login/access-token", data=login_data)
    
    assert response.status_code == 401
