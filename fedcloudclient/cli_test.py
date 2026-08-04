from click.testing import CliRunner
from fedcloudclient.cli import cli


def test_config_show_default_setting():
    """Test config show with default setting"""
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'show', '-s', 'default_setting'])
    
    assert result.exit_code == 0
    print(result.output)  # See what was printed
    

def test_config_show_help():
    """Test config show help"""
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'show', '--help'])
    
    assert result.exit_code == 0
    assert 'Usage:' in result.output


def test_cli_help():
    """Test main CLI help"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    
    assert result.exit_code == 0
    assert 'config' in result.output


def test_multiple_commands():
    """Test various commands"""
    runner = CliRunner()
    
    # Test config command
    result = runner.invoke(cli, ['config', '--help'])
    assert result.exit_code == 0
    
    # Test site command
    result = runner.invoke(cli, ['site', '--help'])
    assert result.exit_code == 0
    

test_config_show_help()