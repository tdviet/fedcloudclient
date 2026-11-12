"""
Testing unit for sites.py
"""

from click.testing import CliRunner

from fedcloudclient import endpoint, sites


def invoke_site_env(monkeypatch, region, with_region):
    """
    Run "site env" with the site configuration and Keystone mocked out
    """
    monkeypatch.setattr(
        sites,
        "find_endpoint_and_project_id",
        lambda site, vo: (
            "https://keystone.example.org:5000/v3",
            "project-id",
            "openid",
        ),
    )
    monkeypatch.setattr(
        endpoint, "get_scoped_token", lambda *args: ("token", "openid", region)
    )
    args = ["env", "--site", "SITE", "--vo", "VO", "--oidc-access-token", "token"]
    if with_region:
        args.append("--with-region")
    return CliRunner().invoke(sites.site, args)


def test_site_env_without_region_makes_no_keystone_call(monkeypatch):
    """
    Without --with-region, "site env" must not call Keystone: it has to keep
    working when the token is expired
    """

    def fail(*args):
        raise AssertionError("site env must not call Keystone without --with-region")

    monkeypatch.setattr(endpoint, "get_region_from_site", fail)
    result = invoke_site_env(monkeypatch, None, with_region=False)
    assert result.exit_code == 0
    assert "OS_REGION_NAME" not in result.output


def test_site_env_with_region_prints_region(monkeypatch):
    """
    With --with-region, OS_REGION_NAME is printed after OS_PROJECT_ID
    """
    result = invoke_site_env(monkeypatch, "IPHC", with_region=True)
    assert result.exit_code == 0
    lines = result.output.splitlines()
    assert lines.index('export OS_REGION_NAME="IPHC";') == (
        lines.index('export OS_PROJECT_ID="project-id";') + 1
    )


def test_site_env_with_region_warns_when_region_is_unknown(monkeypatch):
    """
    An unknown region is a warning, the rest of the environment is still printed
    """
    result = invoke_site_env(monkeypatch, None, with_region=True)
    assert result.exit_code == 0
    assert "OS_REGION_NAME" not in result.output
    assert 'export OS_ACCESS_TOKEN="token";' in result.output
    assert "No region found in the service catalog" in result.stderr
