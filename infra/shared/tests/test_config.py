import os
import tempfile
import unittest
from pathlib import Path


class TestLoadRichmondConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.yaml_path = os.path.join(self.tmpdir, "richmond.yaml")

    def test_loads_valid_yaml(self):
        with open(self.yaml_path, "w") as f:
            f.write(
                "app:\n"
                "  slug: my-app\n"
                "  org: my-org\n"
                "  type: nextjs\n"
                "  port: 3000\n"
                "domain: my-app.example.com\n"
            )
        from shared.config import load_richmond_config

        cfg = load_richmond_config(self.yaml_path)
        self.assertEqual(cfg["app"]["slug"], "my-app")
        self.assertEqual(cfg["domain"], "my-app.example.com")

    def test_raises_on_missing_file(self):
        from shared.config import load_richmond_config

        with self.assertRaises(FileNotFoundError):
            load_richmond_config("/nonexistent/richmond.yaml")

    def test_returns_empty_targets_if_missing(self):
        with open(self.yaml_path, "w") as f:
            f.write("app:\n  slug: x\n")
        from shared.config import load_richmond_config

        cfg = load_richmond_config(self.yaml_path)
        self.assertEqual(cfg.get("targets", {}), {})


class TestUpdateRichmondConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.yaml_path = os.path.join(self.tmpdir, "richmond.yaml")

    def test_updates_nested_key(self):
        with open(self.yaml_path, "w") as f:
            f.write(
                "app:\n  slug: my-app\n"
                "targets:\n  vercel:\n    project_id: null\n"
            )
        from shared.config import update_richmond_config

        update_richmond_config(
            self.yaml_path, {"targets": {"vercel": {"project_id": "prj_123"}}}
        )
        import yaml

        with open(self.yaml_path) as f:
            result = yaml.safe_load(f)
        self.assertEqual(result["targets"]["vercel"]["project_id"], "prj_123")
        self.assertEqual(result["app"]["slug"], "my-app")

    def test_updates_active_target(self):
        with open(self.yaml_path, "w") as f:
            f.write("active_target: local\n")
        from shared.config import update_richmond_config

        update_richmond_config(self.yaml_path, {"active_target": "vercel"})
        import yaml

        with open(self.yaml_path) as f:
            result = yaml.safe_load(f)
        self.assertEqual(result["active_target"], "vercel")


class TestResolveConfigPath(unittest.TestCase):
    def test_resolves_relative_to_module(self):
        from shared.config import resolve_config_path

        path = resolve_config_path()
        self.assertEqual(path.name, "richmond.yaml")
