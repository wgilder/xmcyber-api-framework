
import logging
import xmapi


_log = logging.getLogger('xmcyber')


def log_on_error(error_response):
    _log.error(f"API returned error status code {error_response.status_code}")


def fail_on_error(error_response):
    raise Exception(f"API returned error status code {error_response.status_code}")


def default_on_error(error_response):
    if xmapi.get_config().fail_on_error:
        fail_on_error(error_response)
    else:
        log_on_error(error_response)