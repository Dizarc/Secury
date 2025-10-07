def test_get_events_default(client):
    response = client.get("/api/events")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert isinstance(data["events"], list)
    assert "count" in data

def test_get_events_limit(client):
    response = client.get("/api/events?limit=5")
    assert response.status_code == 200

    data = response.json()
    assert len(data["events"]) <= 5