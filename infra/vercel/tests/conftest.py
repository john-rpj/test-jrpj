"""Test infrastructure for Vercel target stack."""
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
    "vercel:apiToken": "test-vercel-token",
    "accountId": "test-account-id",
    "zoneId": "test-zone-id",
    "googleIdpId": "test-idp-id",
}

# richmond.yaml content for tests
BASE_RICHMOND_CONFIG = {
    "app": {"slug": "myapp", "org": "my-org", "type": "nextjs", "port": 3000},
    "domain": "myapp.example.com",
    "auth": {"provider": "cloudflare-access", "allowed_domain": "myorg.com"},
    "env": {"NEXT_PUBLIC_APP_NAME": "myapp"},
    "targets": {
        "vercel": {
            "project_id": None,
            "build_command": "npm run build",
            "node_version": "20",
        }
    },
    "active_target": "vercel",
}


class VercelMocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}


def load_main(extra_config: dict | None = None, richmond_overrides: dict | None = None) -> types.ModuleType:
    """Set up Pulumi mocks and load the Vercel __main__.py."""
    full_config: dict[str, str] = {}
    for k, v in BASE_CONFIG.items():
        key = k if ":" in k else f"{PROJECT}:{k}"
        full_config[key] = json.dumps(v) if isinstance(v, (list, dict)) else v
    for k, v in (extra_config or {}).items():
        key = k if ":" in k else f"{PROJECT}:{k}"
        full_config[key] = json.dumps(v) if isinstance(v, (list, dict)) else v

    pulumi.runtime.set_mocks(VercelMocks(), project=PROJECT, stack=STACK, preview=False)
    pulumi.runtime.set_all_config(full_config)

    richmond_cfg = {**BASE_RICHMOND_CONFIG, **(richmond_overrides or {})}
    if SHARED_DIR not in sys.path:
        sys.path.insert(0, os.path.join(SHARED_DIR, ".."))
    import shared.config as config_mod
    config_mod.load_richmond_config = lambda path=None: richmond_cfg

    if INFRA_DIR not in sys.path:
        sys.path.insert(0, INFRA_DIR)

    spec = importlib.util.spec_from_file_location("infra_vercel", INFRA_MAIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
