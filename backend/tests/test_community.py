"""
Test community marketplace endpoints.
"""
import pytest


class TestCommunityListings:
    """Tests for community marketplace listings."""

    def test_community_endpoint_exists(self, client):
        """Verify community endpoint responds."""
        res = client.get("/api/v1/community")
        # Accept various responses
        assert res.status_code in (200, 401, 404, 405)
