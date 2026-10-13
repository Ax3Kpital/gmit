def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_providers_list(client):
    r = client.get("/api/providers")
    assert r.status_code == 200
    data = r.json()
    assert "providers" in data
    assert len(data["providers"]) > 0
    codes = [p["code"] for p in data["providers"]]
    assert "fred" in codes
    assert "cftc_cot" in codes
