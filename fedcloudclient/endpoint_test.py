"""
Testing unit for endpoint.py
"""

from fedcloudclient import endpoint


class FakeResponse:
    """
    Minimal stand-in for a requests response
    """

    def __init__(self, status_code, headers=None, body=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body or {}

    def json(self):
        """
        Return the response body
        """
        return self._body


def test_region_from_single_region_catalog():
    """
    A catalog with one region gives that region
    """
    token_body = {
        "token": {
            "catalog": [
                {
                    "type": "compute",
                    "name": "nova",
                    "endpoints": [
                        {
                            "interface": "public",
                            "region_id": "IPHC",
                            "url": "https://sbgcloud.in2p3.fr:8774/v2.1",
                        }
                    ],
                }
            ]
        }
    }
    assert endpoint.get_region_from_token(token_body) == "IPHC"


def test_region_from_multiple_regions_returns_first():
    """
    A catalog with several regions gives the first one
    """
    token_body = {
        "token": {
            "catalog": [
                {
                    "type": "compute",
                    "name": "nova",
                    "endpoints": [
                        {"interface": "public", "region_id": "RegionOne"},
                        {"interface": "public", "region_id": "RegionTwo"},
                    ],
                }
            ]
        }
    }
    assert endpoint.get_region_from_token(token_body) == "RegionOne"


def test_region_from_region_field():
    """
    The region may be in the "region" field instead of "region_id"
    """
    token_body = {
        "token": {
            "catalog": [
                {
                    "type": "compute",
                    "name": "nova",
                    "endpoints": [{"interface": "public", "region": "IPHC"}],
                }
            ]
        }
    }
    assert endpoint.get_region_from_token(token_body) == "IPHC"


def test_region_from_empty_catalog():
    """
    An empty catalog gives None
    """
    assert endpoint.get_region_from_token({"token": {"catalog": []}}) is None


def test_region_from_catalog_without_endpoints():
    """
    A catalog entry without endpoints gives None
    """
    token_body = {"token": {"catalog": [{"type": "compute", "name": "nova"}]}}
    assert endpoint.get_region_from_token(token_body) is None


def test_region_from_token_without_catalog():
    """
    A token body without catalog gives None
    """
    assert endpoint.get_region_from_token({"token": {"expires_at": "never"}}) is None
    assert endpoint.get_region_from_token({}) is None


def test_get_scoped_token_returns_region(monkeypatch):
    """
    get_scoped_token returns the token, the protocol and the region
    """
    token_body = {
        "token": {
            "catalog": [
                {
                    "type": "compute",
                    "name": "nova",
                    "endpoints": [{"interface": "public", "region_id": "IPHC"}],
                }
            ]
        }
    }

    def fake_post(url, **kwargs):
        return FakeResponse(201, {"X-Subject-Token": "scoped-token"}, token_body)

    monkeypatch.setattr(endpoint.requests, "post", fake_post)
    scoped_token, protocol, region = endpoint.get_scoped_token(
        "https://sbgcloud.in2p3.fr:5000/v3", "access-token", "project-id"
    )
    assert scoped_token == "scoped-token"
    assert protocol == "openid"
    assert region == "IPHC"


def test_region_from_site_warns_on_token_error(monkeypatch, capsys):
    """
    A failing Keystone call is a warning, not an error: the environment
    must still be generated without the region
    """

    def fake_get_scoped_token(*args, **kwargs):
        raise endpoint.TokenException(endpoint.SCOPED_TOKEN_ERROR_MSG)

    monkeypatch.setattr(endpoint, "get_scoped_token", fake_get_scoped_token)
    region = endpoint.get_region_from_site(
        "https://sbgcloud.in2p3.fr:5000/v3", "access-token", "project-id"
    )
    assert region is None
    assert "Unable to get region" in capsys.readouterr().err
