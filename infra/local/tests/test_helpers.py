import sys
import os

# Make the infra directory importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helpers import sanitise_branch, make_branch_domain


class TestSanitiseBranch:
    def test_slash_replaced(self):
        assert sanitise_branch("feature/foo") == "feature-foo"

    def test_dot_replaced(self):
        assert sanitise_branch("v1.2.3") == "v1-2-3"

    def test_underscore_replaced(self):
        assert sanitise_branch("my_branch") == "my-branch"

    def test_any_disallowed_char_replaced(self):
        assert sanitise_branch("a!b@c#") == "a-b-c"

    def test_leading_hyphen_stripped(self):
        assert sanitise_branch("/leading") == "leading"

    def test_trailing_hyphen_stripped(self):
        assert sanitise_branch("trailing/") == "trailing"


class TestMakeBranchDomain:
    def test_main_returns_slug_dot_domain(self):
        assert make_branch_domain("main", "myapp", "example.com") == "myapp.example.com"

    def test_non_main_returns_flat_subdomain(self):
        assert make_branch_domain("feature/x", "myapp", "example.com") == "myapp--feature-x.example.com"

    def test_feature_branch_with_hyphen(self):
        assert make_branch_domain("feature-theme", "rpj-dummy", "rpjlabs.com") == "rpj-dummy--feature-theme.rpjlabs.com"
