def test_websocket_connection(client):
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        # Verify that the first message has the expected fields
        assert data["type"] == "initial_state"
        assert "devices" in data
        assert "events" in data

        # Simulate sending a message so it waits for the ack message
        websocket.send_text("Hello from pytest")
        ack = websocket.receive_json()
        assert ack["type"] == "ack"
        assert ack["message"] == "Message received"