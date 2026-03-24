"""Contract tests for the Vercel target stack."""
import os
import sys
import unittest

import pulumi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from conftest import load_main, PROJECT


class TestVercelProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infra = load_main()

    @pulumi.runtime.test
    def test_vercel_project_name(self):
        def check(name):
            self.assertEqual(name, "myapp")
        return self.infra.vercel_project.name.apply(check)

    @pulumi.runtime.test
    def test_vercel_project_framework(self):
        def check(framework):
            self.assertEqual(framework, "nextjs")
        return self.infra.vercel_project.framework.apply(check)

    @pulumi.runtime.test
    def test_vercel_project_git_repo(self):
        def check(git_repo):
            self.assertEqual(git_repo.get("repo"), "my-org/myapp")
            self.assertEqual(git_repo.get("type"), "github")
        return self.infra.vercel_project.git_repository.apply(check)


class TestVercelDomain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infra = load_main()

    @pulumi.runtime.test
    def test_custom_domain(self):
        def check(domain):
            self.assertEqual(domain, "myapp.example.com")
        return self.infra.vercel_domain.domain.apply(check)


class TestCfAccessCreated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infra = load_main()

    @pulumi.runtime.test
    def test_access_app_exists(self):
        self.assertIsNotNone(self.infra.access_resources["access_app"])
        return pulumi.Output.from_input(True).apply(lambda _: None)
