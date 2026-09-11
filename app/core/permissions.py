PERMISSION_MATRIX: dict[str, list[str]] = {
    "owner": [
        "links:create", "links:update", "links:delete",
        "webhooks:manage",
        "api_keys:manage",
        "domains:manage",
        "tags:manage",
        "bio:manage",
        "members:manage",
        "workspace:delete",
        "workspace:update",
        "analytics:view",
        "audit:view",
        "campaigns:manage",
    ],
    "admin": [
        "links:create", "links:update", "links:delete",
        "webhooks:manage",
        "tags:manage",
        "bio:manage",
        "members:manage",
        "workspace:update",
        "analytics:view",
        "audit:view",
        "campaigns:manage",
    ],
    "editor": [
        "links:create", "links:update", "links:delete",
        "tags:manage",
        "bio:manage",
        "analytics:view",
    ],
    "viewer": [
        "analytics:view",
    ],
}

PERMISSION_ROLES = {
    # shorthand: role has permission X
    "links:create": {"owner", "admin", "editor"},
    "links:update": {"owner", "admin", "editor"},
    "links:delete": {"owner", "admin", "editor"},
    "webhooks:manage": {"owner", "admin"},
    "api_keys:manage": {"owner"},
    "domains:manage": {"owner"},
    "tags:manage": {"owner", "admin", "editor"},
    "bio:manage": {"owner", "admin", "editor"},
    "members:manage": {"owner", "admin"},
    "workspace:delete": {"owner"},
    "workspace:update": {"owner", "admin"},
    "analytics:view": {"owner", "admin", "editor", "viewer"},
    "audit:view": {"owner", "admin"},
    "campaigns:manage": {"owner", "admin"},
}


def role_has_permission(role: str, permission: str) -> bool:
    roles_with_perm = PERMISSION_ROLES.get(permission, set())
    return role in roles_with_perm
