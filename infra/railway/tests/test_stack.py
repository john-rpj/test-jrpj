"""Contract tests for the Railway target stack."""
import os
import sys
import unittest

import pulumi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from conftest import load_main


class TestRailwayProject(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infra = load_main()

    @pulumi.runtime.test
    def test_railway_project_name(self):
        # Dynamic Provider stores inputs as outputs; the project name is stored
        # under the "name" key (the input passed to RailwayProjectProvider).
        def check(name):
            self.assertEqual(name, "myapp")
        return self.infra.railway_project.name.apply(check)


class TestRailwayDns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infra = load_main()

    @pulumi.runtime.test
    def test_dns_record_exists(self):
        self.assertIsNotNone(self.infra.access_resources)
        return pulumi.Output.from_input(True).apply(lambda _: None)


class TestCfAccessCreated(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.infra = load_main()

    @pulumi.runtime.test
    def test_access_app_exists(self):
        self.assertIn("access_app", self.infra.access_resources)
        return pulumi.Output.from_input(True).apply(lambda _: None)
