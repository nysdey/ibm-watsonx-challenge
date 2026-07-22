import time


def wait_for_job(client, name: str, attempts: int = 300):
    for _ in range(attempts):
        status = client.get("/api/status").get_json()["_actions"][name]
        if not status["active"]:
            return status
        time.sleep(0.01)
    raise AssertionError(f"job {name} did not finish")


def sign_in(client):
    response = client.post(
        "/api/credentials/w3id",
        json={"email": "tim.zhou@ibm.com", "password": "demo"},
    )
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def build_book(client):
    sign_in(client)
    assert client.post("/api/get_my_accounts/run").get_json()["ok"]
    assert wait_for_job(client, "get_my_accounts")["done"]
    assert client.post("/api/strategize/run").get_json()["ok"]
    assert wait_for_job(client, "strategize")["done"]


def test_sign_in_import_and_strategize_flow(client):
    assert client.get("/api/credentials/status").get_json()["w3id"] is False
    sign_in(client)
    assert client.get("/api/credentials/status").get_json()["w3id"] is True

    assert client.post("/api/get_my_accounts/run").get_json()["ok"]
    imported = wait_for_job(client, "get_my_accounts")
    assert imported["done"] and imported["error"] is None
    accounts = client.get("/api/accounts/list").get_json()
    assert accounts["has_accounts"] and len(accounts["accounts"]) == 48
    assert accounts["strategized"] is False

    assert client.post("/api/strategize/run").get_json()["ok"]
    strategized = wait_for_job(client, "strategize")
    assert strategized["done"] and strategized["error"] is None
    accounts = client.get("/api/accounts/list").get_json()
    assert accounts["strategized"] is True
    assert sum(accounts["lists"]["cadences"].values()) > 0


def test_active_read_models_share_one_book(client):
    build_book(client)
    endpoints = (
        "/api/accounts/list", "/api/schedule", "/api/dashboard", "/api/today",
        "/api/dashboard/progress", "/api/book", "/api/territory", "/api/cadences",
    )
    payloads = {}
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        payloads[endpoint] = response.get_json()
    assert payloads["/api/accounts/list"]["lists"]["all"] == payloads["/api/book"]["total"]
    assert payloads["/api/schedule"]["has_schedule"] is True
    assert payloads["/api/dashboard"]["has_schedule"] is True
    assert payloads["/api/cadences"]["has_cadences"] is True
    assert [point["label"] for point in payloads["/api/dashboard/progress"]["series"]] == [
        "Mon", "Tue", "Wed", "Thu", "Fri"
    ]


def test_account_detail_batch_and_ai_fallback(client):
    build_book(client)
    names = [row["account"] for row in client.get("/api/accounts/list").get_json()["accounts"][:2]]
    detail = client.get("/api/accounts/detail", query_string={"name": names[0]}).get_json()
    assert detail["account"] == names[0]
    assert detail["zoominfo"]["contacts"]
    batch = client.get("/api/accounts/details", query_string={"names": "\x1f".join(names)}).get_json()
    assert set(batch["accounts"]) == set(names)
    brief = client.get("/api/call_brief", query_string={"name": names[0]}).get_json()
    assert brief["bullets"] and brief["source"] in {"deterministic", "watsonx"}


def test_loopback_and_cross_origin_guards(client):
    assert client.get("/", environ_overrides={"HTTP_HOST": "evil.example"}).status_code == 403
    response = client.post(
        "/api/demo/reset",
        environ_overrides={"HTTP_HOST": "127.0.0.1:5488"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
