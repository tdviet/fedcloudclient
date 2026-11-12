"""
Testing unit for endpoint.py
"""

from click.testing import CliRunner
import pytest

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


def catalog(*regions, field="region_id"):
    """
    Build a Keystone token body with one endpoint per region
    """
    return {
        "token": {
            "catalog": [
                {
                    "type": "compute",
                    "name": "nova",
                    "endpoints": [{field: region} for region in regions],
                }
            ]
        }
    }


def test_region_from_single_region_catalog():
    """
    A catalog with one region gives that region
    """
    assert endpoint.get_region_from_token(catalog("IPHC")) == "IPHC"


def test_region_from_multiple_regions_returns_first():
    """
    A catalog with several regions gives the first one
    """
    assert (
        endpoint.get_region_from_token(catalog("RegionOne", "RegionTwo")) == "RegionOne"
    )


def test_region_from_region_field():
    """
    The region may be in the "region" field instead of "region_id"
    """
    assert endpoint.get_region_from_token(catalog("IPHC", field="region")) == "IPHC"


def test_region_from_token_without_region():
    """
    A token body without any region gives None
    """
    assert endpoint.get_region_from_token(catalog()) is None
    assert endpoint.get_region_from_token({"token": {"catalog": [{"name": "nova"}]}}) is None
    assert endpoint.get_region_from_token({"token": {}}) is None
    assert endpoint.get_region_from_token({}) is None


def test_get_scoped_token_returns_region(monkeypatch):
    """
    get_scoped_token returns the token, the protocol and the region
    """
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        return FakeResponse(201, {"X-Subject-Token": "scoped-token"}, catalog("IPHC"))

    monkeypatch.setattr(endpoint.requests, "post", fake_post)
    scoped_token, protocol, region = endpoint.get_scoped_token(
        "https://keystone.example.org:5000/v3", "access-token", "project-id"
    )
    assert (scoped_token, protocol, region) == ("scoped-token", "openid", "IPHC")
    # The scoped token request must not be able to hang forever
    assert calls[-1]["timeout"] == endpoint.TIMEOUT


def test_unscoped_token_falls_back_to_oidc(monkeypatch):
    """
    If the site does not support the openid protocol, oidc is tried
    """
    urls = []

    def fake_post(url, **kwargs):
        urls.append(url)
        if "/protocols/openid/auth" in url:
            return FakeResponse(401)
        return FakeResponse(201, {"X-Subject-Token": "unscoped-token"})

    monkeypatch.setattr(endpoint.requests, "post", fake_post)
    assert endpoint.get_unscoped_token("https://keystone/v3", "token") == (
        "unscoped-token",
        "oidc",
    )
    assert len(urls) == 2


def test_unscoped_token_raises_when_no_protocol_works(monkeypatch):
    """
    If no protocol works, the error is about the unscoped token
    """
    monkeypatch.setattr(
        endpoint.requests, "post", lambda url, **kwargs: FakeResponse(401)
    )
    with pytest.raises(endpoint.TokenException) as error:
        endpoint.get_unscoped_token("https://keystone/v3", "token")
    assert endpoint.UNSCOPED_TOKEN_ERROR_MSG in str(error.value)


def test_region_from_site_warns_on_token_error(monkeypatch, capsys):
    """
    A failing Keystone call is a warning, not an error: the environment
    must still be generated without the region
    """

    def fail(*args):
        raise endpoint.TokenException(endpoint.SCOPED_TOKEN_ERROR_MSG)

    monkeypatch.setattr(endpoint, "get_scoped_token", fail)
    assert endpoint.get_region_from_site("https://keystone/v3", "token", "project") is None
    assert "Unable to get region" in capsys.readouterr().err


def invoke_endpoint_env(monkeypatch, region, with_region):
    """
    Run "endpoint env" with GOCDB and Keystone mocked out
    """
    monkeypatch.setattr(
        endpoint,
        "find_endpoint",
        lambda *args, **kwargs: [
            ["SITE", "org.openstack.nova", "https://keystone.example.org:5000/v3"]
        ],
    )
    monkeypatch.setattr(
        endpoint, "get_scoped_token", lambda *args: ("token", "openid", region)
    )
    args = [
        "env",
        "--site",
        "SITE",
        "--project-id",
        "project-id",
        "--oidc-access-token",
        "token",
    ]
    if with_region:
        args.append("--with-region")
    return CliRunner().invoke(endpoint.endpoint, args)


def test_endpoint_env_with_region(monkeypatch):
    """
    "endpoint env --with-region" prints the region of the scoped token
    """
    result = invoke_endpoint_env(monkeypatch, "IPHC", with_region=True)
    assert result.exit_code == 0
    assert 'export OS_REGION_NAME="IPHC";' in result.output


def test_endpoint_env_without_region(monkeypatch):
    """
    Without --with-region, "endpoint env" does not print the region
    """
    result = invoke_endpoint_env(monkeypatch, "IPHC", with_region=False)
    assert result.exit_code == 0
    assert "OS_REGION_NAME" not in result.output
