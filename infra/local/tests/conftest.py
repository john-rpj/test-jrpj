# templates/infra/local/tests/conftest.py
"""Test infrastructure for the local target stack."""
import copy
import importlib.util
import json
import os
import sys
import types

import pulumi
import pulumi.runtime

PROJECT = "testproject"
STACK = "teststack"

INFRA_MAIN = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "__main__.py"))
INFRA_DIR = os.path.dirname(INFRA_MAIN)
SHARED_DIR = os.path.abspath(os.path.join(INFRA_DIR, "..", "shared"))

# Secrets that stay in Pulumi config
BASE_CONFIG = {
    "cloudflare:apiToken": "test-cf-token",
    "accountId": "test-account-id",
    "zoneId": "test-zone-id",
    "googleIdpId": "test-idp-id",
    "cfTeamName": "myteam",
    "tunnelSecret": "dGVzdHNlY3JldA==",
}

# Base richmond.yaml content for tests.
# auth is intentionally absent so TestAuthGuard (load_main({})) raises an exception.
BASE_RICHMOND_CONFIG = {
    "app": {"slug": "myapp", "org": "my-org", "type": "nextjs", "port": 3000},
    "domain": "example.com",
    "env": {},
    "targets": {
        "local": {"branches": ["main"]},
    },
}

# Map from Pulumi config key (without PROJECT: prefix) to a callable that
# applies the value into a richmond config dict.
# This allows test_stack.py to keep passing PROJECT:allowedDomain etc.
_RICHMOND_KEY_MAP = {
    "allowedDomain": lambda cfg, v: cfg.setdefault("auth", {}).update({"allowed_domain": v}) or cfg,
    "allowedEmails": lambda cfg, v: cfg.setdefault("auth", {}).update({"allowed_emails": v}) or cfg,
    "branches": lambda cfg, v: cfg.setdefault("targets", {}).setdefault("local", {}).update({"branches": v}) or cfg,
    "appPort": lambda cfg, v: cfg["app"].update({"port": int(v)}) or cfg,
}


class LocalMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        if args.token == "cloudflare:index/getZeroTrustTunnelCloudflaredToken:getZeroTrustTunnelCloudflaredToken":
            return {"token": "mock-tunnel-token", "id": "mock-id"}
        return {}


def load_main(extra_config: dict | None = None, richmond_overrides: dict | None = None) -> types.ModuleType:
    """Set up Pulumi mocks and load the local __main__.py.

    Accepts the same extra_config dict as the old conftest (with PROJECT: prefixed
    keys like ``{PROJECT}:allowedDomain``), and automatically translates known
    keys into richmond config overrides so that test_stack.py works unchanged.

    Args:
        extra_config: Keys to merge. Keys with PROJECT: prefix and known names
                      (allowedDomain, allowedEmails, branches, appPort) are
                      translated into richmond.yaml config. Other keys are passed
                      as-is into Pulumi config.
        richmond_overrides: Additional richmond config dict to deep-merge on top.

    Returns:
        The loaded __main__ module with all resource attributes accessible.
    """
    # Build Pulumi config (secrets only)
    full_config: dict[str, str] = {}
    for k, v in BASE_CONFIG.items():
        key = k if ":" in k else f"{PROJECT}:{k}"
        full_config[key] = json.dumps(v) if isinstance(v, (list, dict)) else v

    # Build richmond config, starting from base
    richmond_cfg = copy.deepcopy(BASE_RICHMOND_CONFIG)

    # Translate known extra_config keys into richmond config
    project_prefix = f"{PROJECT}:"
    for k, v in (extra_config or {}).items():
        # Strip project prefix if present
        bare_key = k[len(project_prefix):] if k.startswith(project_prefix) else k
        # Deserialize JSON-encoded values (lists, dicts)
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except (json.JSONDecodeError, ValueError):
                pass  # keep as string

        if bare_key in _RICHMOND_KEY_MAP:
            _RICHMOND_KEY_MAP[bare_key](richmond_cfg, v)
        else:
            # Unknown key: pass through to Pulumi config
            key = k if ":" in k else f"{PROJECT}:{k}"
            full_config[key] = json.dumps(v) if isinstance(v, (list, dict)) else str(v)

    # Apply any explicit richmond_overrides
    if richmond_overrides:
        _deep_merge(richmond_cfg, richmond_overrides)

    pulumi.runtime.set_mocks(LocalMocks(), project=PROJECT, stack=STACK, preview=False)
    pulumi.runtime.set_all_config(full_config)

    # Monkey-patch load_richmond_config so __main__.py reads our test config
    if os.path.join(SHARED_DIR, "..") not in sys.path:
        sys.path.insert(0, os.path.join(SHARED_DIR, ".."))
    import shared.config as config_mod
    config_mod.load_richmond_config = lambda path=None: richmond_cfg

    if INFRA_DIR not in sys.path:
        sys.path.insert(0, INFRA_DIR)

    spec = importlib.util.spec_from_file_location("infra_local", INFRA_MAIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _deep_merge(base: dict, updates: dict) -> dict:
    """Recursively merge updates into base dict."""
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
