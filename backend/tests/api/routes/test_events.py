#TODO: Change all status codes to constants

def test_get_events_default(auth_client):
    response = auth_client.get("/api/events")
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    # default limit = 10
    assert len(data) <= 10

def test_get_events_limit(auth_client):
    response = auth_client.get("/api/events?limit=5")
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 5