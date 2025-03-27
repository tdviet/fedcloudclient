"""
Define custom exceptions for fedcloudclient
"""


class FedcloudError(Exception):
    """Master class for all custom exceptions in fedcloudclient."""
    def __init__(self, message="An unspecified Fedcloud error occurred"):
        super().__init__(message)


class TokenError(FedcloudError):
    """Authentication error, token not initialized or recognized"""
    def __init__(self, message="Authentication token error"):
        super().__init__(message)


class ServiceError(FedcloudError):
    """Connection timeout, service not available and so on."""
    def __init__(self, message="Service communication error"):
        super().__init__(message)


class ConfigError(FedcloudError):
    """Configuration error, file does not exist and so on."""
    def __init__(self, message="Configuration error"):
        super().__init__(message)
