"""
Define custom exceptions for fedcloudclient
"""


class FedcloudError(Exception):
    """
    Master class for all custom exception in fedcloudclient
    """
    ...


class TokenError(FedcloudError):
    """
    Authentication error, token not initialized and so on
    """
    ...


class ServiceError(FedcloudError):
    """
    Connection timeout, service not available and so on
    """
    ...


class ConfigError(FedcloudError):
    """
    Configuration error, files not exists and so on
    """
    ...
