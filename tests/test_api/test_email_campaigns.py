import pytest
from httpx import AsyncClient


def _slug():
    import uuid
    return uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_list_contacts_empty(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "EC Empty", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/contacts")
    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_create_contact(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "EC Create", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    email = f"{_slug()}@test.com"
    response = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/contacts",
        json={"email": email},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["workspace_id"] == ws_id
    assert "id" in data
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_contact_duplicate_email(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "EC Dup", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    email = f"{_slug()}@test.com"
    r1 = await auth_client.post(f"/api/v1/workspaces/{ws_id}/email/contacts", json={"email": email})
    assert r1.status_code == 201
    r2 = await auth_client.post(f"/api/v1/workspaces/{ws_id}/email/contacts", json={"email": email})
    assert r2.status_code == 201


@pytest.mark.asyncio
async def test_delete_contact(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "EC Del", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    email = f"{_slug()}@test.com"
    create_resp = await auth_client.post(f"/api/v1/workspaces/{ws_id}/email/contacts", json={"email": email})
    contact_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/workspaces/{ws_id}/email/contacts/{contact_id}")
    assert response.status_code == 204
    list_resp = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/contacts")
    assert list_resp.json()["items"] == []


@pytest.mark.asyncio
async def test_delete_contact_not_found(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "EC NF", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.delete(
        f"/api/v1/workspaces/{ws_id}/email/contacts/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_template(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECT Create", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    name = f"tmpl-{_slug()}"
    response = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/templates",
        json={"name": name, "subject": "Hello", "html_body": "<p>World</p>"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["subject"] == "Hello"
    assert data["html_body"] == "<p>World</p>"
    assert data["is_default"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_list_templates(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECT List", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/templates",
        json={"name": f"tmpl-{_slug()}", "subject": "S1", "html_body": "<p>A</p>"},
    )
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/templates")
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_template(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECT Get", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    name = f"tmpl-{_slug()}"
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/templates",
        json={"name": name, "subject": "Subj", "html_body": "<p>Body</p>"},
    )
    tmpl_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/templates/{tmpl_id}")
    assert response.status_code == 200
    assert response.json()["name"] == name


@pytest.mark.asyncio
async def test_get_template_not_found(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECT NF", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    response = await auth_client.get(
        f"/api/v1/workspaces/{ws_id}/email/templates/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_template(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECT Upd", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/templates",
        json={"name": f"tmpl-{_slug()}", "subject": "Old", "html_body": "<p>Old</p>"},
    )
    tmpl_id = create_resp.json()["id"]
    response = await auth_client.put(
        f"/api/v1/workspaces/{ws_id}/email/templates/{tmpl_id}",
        json={"name": "updated-name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated-name"


@pytest.mark.asyncio
async def test_delete_template(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECT Del", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/templates",
        json={"name": f"tmpl-{_slug()}", "subject": "Del", "html_body": "<p>X</p>"},
    )
    tmpl_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/workspaces/{ws_id}/email/templates/{tmpl_id}")
    assert response.status_code == 204
    get_resp = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/templates/{tmpl_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_campaign(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC Create", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    name = f"camp-{_slug()}"
    response = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": name, "subject": "Campaign Subj", "html_body": "<p>Campaign</p>"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["subject"] == "Campaign Subj"
    assert data["html_body"] == "<p>Campaign</p>"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_campaigns(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC List", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": f"camp-{_slug()}", "subject": "S1", "html_body": "<p>A</p>"},
    )
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/campaigns")
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_campaign(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC Get", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    name = f"camp-{_slug()}"
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": name, "subject": "Subj", "html_body": "<p>Body</p>"},
    )
    camp_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/campaigns/{camp_id}")
    assert response.status_code == 200
    assert response.json()["name"] == name


@pytest.mark.asyncio
async def test_update_campaign(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC Upd", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": f"camp-{_slug()}", "subject": "Old", "html_body": "<p>Old</p>"},
    )
    camp_id = create_resp.json()["id"]
    response = await auth_client.put(
        f"/api/v1/workspaces/{ws_id}/email/campaigns/{camp_id}",
        json={"name": "updated-campaign"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "updated-campaign"


@pytest.mark.asyncio
async def test_delete_campaign(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC Del", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": f"camp-{_slug()}", "subject": "Del", "html_body": "<p>X</p>"},
    )
    camp_id = create_resp.json()["id"]
    response = await auth_client.delete(f"/api/v1/workspaces/{ws_id}/email/campaigns/{camp_id}")
    assert response.status_code == 204
    get_resp = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/campaigns/{camp_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_send_campaign(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC Send", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": f"camp-{_slug()}", "subject": "Send", "html_body": "<p>Send</p>"},
    )
    camp_id = create_resp.json()["id"]
    response = await auth_client.post(f"/api/v1/workspaces/{ws_id}/email/campaigns/{camp_id}/send")
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_campaign_stats(auth_client: AsyncClient):
    ws_resp = await auth_client.post("/api/v1/workspaces", json={"name": "ECC Stats", "slug": _slug()})
    ws_id = ws_resp.json()["id"]
    create_resp = await auth_client.post(
        f"/api/v1/workspaces/{ws_id}/email/campaigns",
        json={"name": f"camp-{_slug()}", "subject": "Stats", "html_body": "<p>Stats</p>"},
    )
    camp_id = create_resp.json()["id"]
    response = await auth_client.get(f"/api/v1/workspaces/{ws_id}/email/campaigns/{camp_id}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["sent"] == 0
    assert data["delivered"] == 0
    assert data["opened"] == 0
    assert data["clicked"] == 0
    assert data["bounced"] == 0
    assert data["unsubscribed"] == 0
