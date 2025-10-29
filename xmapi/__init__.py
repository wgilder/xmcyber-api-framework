"""This module provides helper methods for parsing the command line and 
loading configuration files. Call --help on the command line to get detailed
information regarding which arguments are expected on the comand line and in
the configuration files.

Besides initial configuration, this module contains the sub-module "facade,"
which itself provides helper methods for calling the XM Cyber API.

The configuration values are contained in an object named "config," which is
imported by default. The base configuration contains raw command line and
configuration file parameters, plus the attribute "url," which contains the
full URL where the API is being accessed.
"""
import xmapi.commandline
import xmapi.configfile 
from xmapi.util import default_on_error
from urllib.parse import quote
import requests
import logging
import sys

class _HTTPBearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return self.token == getattr(other, 'token', None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r

__all__=["get_config", "get_commandline_parser", "initialize"]

_config_holder = [ None ]

_log = logging.getLogger('xmcyber')
_parser = xmapi.commandline.get_parser()


def get_commandline_parser():
    """This returns the instance of the argparse class used by this method. Use 
    this to add needed command line parameters prior to calling parse_arguments().
    """
    return _parser


def set_log_on_error():
    get_config().fail_on_error = False


def set_fail_on_error():
    get_config().fail_on_error = True


def get_config():
    if not _config_holder[0]:
        raise Exception("Configuration file not initialized. xmapi.parse_arguments() must be called first.")
    
    return _config_holder[0]


def initialize():
    """Parse the command line and load in any initialization files.
    """
    global _config_holder
    if _config_holder[0]:
        _log.info("xmapi.parse_arguments() called multiple times")
        return

    # We're first parsing the command line. This allows us to get startup vars not available
    # in the config file, like log level or config file chunk.
    _cli_args = _parser.parse_args()
    _config_holder[0] = _cli_args
    chunk = _cli_args.chunk
    
    if _cli_args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif _cli_args.quiet:
        logging.basicConfig(level=logging.ERROR)


    _log.debug(f"Using chunk '{chunk}' in the config file.")

    # Now let's parse the config file. If no config file is found, everything has to be on the command line
    _raw_config = xmapi.configfile.parse_config()
    
    if not len(sys.argv) > 1 and not _raw_config:
        _parser.print_help()
        exit(-1)

    if not _raw_config:
        _log.info("No configuration file (xmapi.ini) found in any of the locations.")
        _log.info("See help (--help) for more information.")
        _raw_config = { "DEFAULT":{}} # Creating a tiny, empty config file since no other was found
    elif "DEFAULT" in _raw_config:
        _log.info("Successfully parsed at least one configuration file")
    else:
        _log.warn("At least one configuration file was read in, but no [DEFAULT] section was found.")
        _log.info("All configurations in the file(s) will therefore be ignored. See help (--help)")
        _log.info("for further information")

    _log.info("Starting configuration initialization")

    # Now we can get the parameters with which to run the program, taking precedence as required.
    _cli_args.subdomain = _get_item(_raw_config, _cli_args.subdomain, "subdomain", chunk=chunk)
    if not _cli_args.subdomain:
        raise Exception("No client subdomain specified")

    _cli_args.key = _get_item(_raw_config, _cli_args.key, "key", chunk=chunk)
    if not _cli_args.key:
        raise Exception("No --key has specified")
    
    _cli_args.url = f"https://{_cli_args.subdomain}.clients.xmcyber.com"

    _cli_args.proxy_port = _get_item(_raw_config, _cli_args.proxy_port, "proxy_port", chunk=chunk)
    _cli_args.proxy_url = _get_item(_raw_config, _cli_args.proxy_url, "proxy_url", chunk=chunk)
    
    if _cli_args.proxy_url:
        if not _cli_args.proxy_port:
            raise Exception("Proxy URL was provided without a proxy port number")
    elif _cli_args.proxy_port:
        raise Exception("Proxy port number was provided without a proxy URL")
    
    set_fail_on_error()
    _authenticate()
    

def _get_item(config_file, value, key, default_value=None, chunk=None):
    if value:
        _log.debug(f"Found {key} on the command line. Will take precedence over config file")
        return value
    
    if chunk and chunk in config_file and key in config_file[chunk]:
        _log.debug(f"Found {key} in a configuration file subdomain section but not on the command line.")
        return config_file[chunk][key]
    
    if key in config_file["DEFAULT"]:
        _log.debug(f"Found {key} in a configuration file default section but not on the command line.")
        return config_file["DEFAULT"][key]
    
    _log.debug(f"Item {key} not found in configuration file or on the command line.")
    return default_value


def _build_path(path, encode_path):
    if type(path) is str:
        if encode_path:
            path = path.split("/")

    if encode_path:
        elements = []

        for element in path:
            elements.append(quote(element))

        path = elements

    if not type(path) is str:
        path = "/".join(path)

    return f"/api/{path}"



def api_get(path, encode_path=False, data=None, params=None, headers=None, on_error=default_on_error):
    """Wrapper to make a GET call to the API."""
    return api_request("get", path=path, encode_path=encode_path, data=data, params=params, headers=headers, on_error=on_error)


def api_put(path, encode_path=False, data=None, params=None, headers=None, on_error=default_on_error):
    """Wrapper to make a PUT call to the API."""
    return api_request("put", path=path, encode_path=encode_path, data=data, params=params, headers=headers, on_error=on_error)


def api_post(path, encode_path=False, data=None, params=None, headers=None, on_error=default_on_error):
    """Wrapper to make a POST call to the API."""
    return api_request("post", path=path, encode_path=encode_path, data=data, params=params, headers=headers, on_error=on_error)


def api_delete(path, encode_path=False, data=None, params=None, headers=None, on_error=default_on_error):
    """Wrapper to make a DELETE call to the API."""
    return api_request("delete", path=path, encode_path=encode_path, data=data, params=params, headers=headers, on_error=on_error)


def api_request(verb, path, encode_path=False, data=None, params=None, headers=None, on_error=default_on_error):
    """This is the generic entry-point for making HTTP calls to the API"""
    config = get_config()
    auth = _HTTPBearerAuth(config.access_token)
    url = f"{config.url}/{_build_path(path, encode_path)}"

    resp = requests.request(verb, url, data=data, params=params, headers=headers, auth=auth)

    if resp.status_code < 200 or resp.status_code > 299:
        on_error(resp)

    return resp


def _authenticate():
    config = get_config()

    headers = {
        "X-Api-Key": config.key
    }

    headers = {
        "X-Api-Key": config.key
    }

    r = requests.post(f"{config.url}/api/auth/", headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to authenticate (status code {r.status_code})")

    json = r.json()
    config.access_token = json["accessToken"]
    config.refresh_token = json["refreshToken"]
