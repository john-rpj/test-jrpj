import unittest
import pulumi
import pulumi.runtime


class MocksForAccess(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        return [args.name + "_id", args.inputs]

    def call(self, args: pulumi.runtime.MockCallArgs):
        return {}


class TestCreateCfAccess(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pulumi.runtime.set_mocks(
            MocksForAccess(), project="test", stack="test", preview=False
        )
        from shared.cloudflare_access import create_cf_access

        cls.result = create_cf_access(
            account_id="test-account",
            app_slug="myapp",
            app_domain="myapp.example.com",
            google_idp_id="idp-123",
            allowed_domain="myorg.com",
            allowed_emails=None,
        )

    @pulumi.runtime.test
    def test_returns_access_app(self):
        self.assertIn("access_app", self.result)
        return pulumi.Output.from_input(True).apply(lambda _: None)

    @pulumi.runtime.test
    def test_returns_access_policy(self):
        self.assertIn("access_policy", self.result)
        return pulumi.Output.from_input(True).apply(lambda _: None)

    @pulumi.runtime.test
    def test_wildcard_domains(self):
        def check(domains):
            self.assertIn("myapp.example.com", domains)
            self.assertIn("*.myapp.example.com", domains)
        return self.result["access_app"].self_hosted_domains.apply(check)
