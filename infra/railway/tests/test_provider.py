"""Unit tests for the Railway Dynamic Provider (GraphQL client logic)."""
import unittest
from unittest.mock import patch, MagicMock


class TestRailwayGraphQLClient(unittest.TestCase):
    def test_create_project_sends_mutation(self):
        from railway_provider import RailwayClient

        client = RailwayClient(api_token="test-token")
        with patch("railway_provider.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": {"projectCreate": {"id": "proj-123", "name": "my-app"}}},
            )
            result = client.create_project("my-app")
            self.assertEqual(result["id"], "proj-123")
            mock_post.assert_called_once()
            call_body = mock_post.call_args[1]["json"]
            self.assertIn("projectCreate", call_body["query"])

    def test_delete_project_sends_mutation(self):
        from railway_provider import RailwayClient

        client = RailwayClient(api_token="test-token")
        with patch("railway_provider.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"data": {"projectDelete": True}},
            )
            client.delete_project("proj-123")
            mock_post.assert_called_once()
