import hashlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.api_key import ApiKeyCreate
from app.schemas.workspace import WorkspaceCreate
from app.services.api_key_service import (
    authenticate_api_key,
    create_api_key,
    list_api_keys,
    revoke_api_key,
)
from app.services.workspace_service import create_workspace


@pytest.mark.asyncio
async def test_create_api_key(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(
        db_session, WorkspaceCreate(name="Test WS", slug="test-ws"), test_user_id
    )
    data = ApiKeyCreate(name="Test Key")
    key_obj, raw_key = await create_api_key(db_session, data, test_user_id, ws.id)
    assert key_obj.name == "Test Key"
    assert raw_key.startswith("uf_")
    assert key_obj.prefix == raw_key[:8]
    expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    assert key_obj.key_hash == expected_hash


@pytest.mark.asyncio
async def test_authenticate_valid_key(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(
        db_session, WorkspaceCreate(name="Auth WS", slug="auth-ws"), test_user_id
    )
    key_obj, raw_key = await create_api_key(
        db_session, ApiKeyCreate(name="Auth Test"), test_user_id, ws.id
    )
    result = await authenticate_api_key(db_session, raw_key)
    assert result is not None
    assert result.id == key_obj.id


@pytest.mark.asyncio
async def test_authenticate_invalid_key(db_session: AsyncSession):
    result = await authenticate_api_key(db_session, "uf_badkey")
    assert result is None


@pytest.mark.asyncio
async def test_revoke_api_key(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(
        db_session, WorkspaceCreate(name="Revoke WS", slug="revoke-ws"), test_user_id
    )
    key_obj, raw_key = await create_api_key(
        db_session, ApiKeyCreate(name="Revoke Me"), test_user_id, ws.id
    )
    revoked = await revoke_api_key(db_session, key_obj.id)
    assert revoked is not None
    assert revoked.is_active is False
    result = await authenticate_api_key(db_session, raw_key)
    assert result is None


@pytest.mark.asyncio
async def test_list_api_keys(db_session: AsyncSession, test_user_id: str):
    ws = await create_workspace(
        db_session, WorkspaceCreate(name="List WS", slug="list-ws"), test_user_id
    )
    await create_api_key(db_session, ApiKeyCreate(name="Key 1"), test_user_id, ws.id)
    await create_api_key(db_session, ApiKeyCreate(name="Key 2"), test_user_id, ws.id)
    keys = await list_api_keys(db_session, ws.id)
    assert len(keys) == 2
