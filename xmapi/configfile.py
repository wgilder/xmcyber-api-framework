from collections import OrderedDict
from enum import Enum
import configparser
import logging
import os
import platform

# Automatically loaded and executed when this module is loaded.
# 
# Provides hierarchical searching and loading of configuration files.
#
# See https://docs.python.org/3/library/configparser.html

# Mac:
#   - User: $HOME/.xmcyber/xmapi.ini
#   - Global: /usr/Shared/.xmcyber/xmapi.ini
#
# Win:
#   - User: %LocalAppDataFolder%/.xmcyber/xmapi.ini
#   - Global: %AppDataFolder%/.xmcyber/xmapi.ini
# 
# Linux:
#   - User: $HOME/.xmcyber/xmapi.ini
#   - Global: /etc/.xmcyber/xmapi.ini

_log = logging.getLogger("xmcyber")

class _ConfigScope(Enum):
    USER = 1
    GLOBAL = 2
    PROJECT = 3

def _get_for_darwin(which):
    if which == _ConfigScope.GLOBAL:
        return "/Users/Shared"
    elif which == _ConfigScope.USER:
        if "HOME" in os.environ:
            return os.environ["HOME"]
    
    return None

def _get_for_linux(which):
    if which == _ConfigScope.GLOBAL:
        return "/etc"
    elif which == _ConfigScope.USER:
        if "HOME" in os.environ:
            return os.environ["HOME"]

        return "~"
    
    return None

def _get_for_windows(which):
    if which == _ConfigScope.GLOBAL:
        if "AppDataFolder" in os.environ:
            return os.environ["AppDataFolder"]
    elif which == _ConfigScope.USER:
        if "LocalAppDataFolder" in os.environ:
            return os.environ["LocalAppDataFolder"]
        
        return "~"

    return None

def _get_for_java(which):
    return _default_get(which)

def _default_get(which):
    if which == _ConfigScope.USER:
        return "~"

    return None

paths = {
    'Darwin': _get_for_darwin,
    'Linux': _get_for_linux,
    'Windows': _get_for_windows,
    'Java': _get_for_java
}

def _add(locations, callback, scope):
    if scope == _ConfigScope.PROJECT:
        next = "xmapi.ini"
    else:
        next = callback(scope)
        if next:
            next = f"{next}/.xmcyber/xmapi.ini"

    if next:
        locations[scope] = next

def _get_locations():
    sys = platform.system()
    if sys in paths:
        _log.info(f"Getting system information for {sys}")
        _get_var = paths[sys]
    else:
        _log.warning("System not recognized: {sys}")
        _get_var = _default_get

    locations = OrderedDict()
    _add(locations, _get_var, _ConfigScope.GLOBAL)    
    _add(locations, _get_var, _ConfigScope.USER)
    _add(locations, _get_var, _ConfigScope.PROJECT)

    return locations

def parse_config():
    locations = _get_locations()

    _log.info(f"Looking for configuration files in {len(locations)}(s)")
    if len(locations) > 0 and _log.isEnabledFor(logging.DEBUG):
        _log.debug("Locations that will be tried (in this order):")
        for location in locations:
            _log.debug(f"  {location.name} ({locations[location]})")

    config = configparser.ConfigParser()
    files = config.read(locations.values())
    _log.info(f"Found a total of {len(files)} configuration file(s)")
    if len(files) == 0:
        return None
    
    if _log.isEnabledFor(logging.DEBUG):
        _log.debug("Configuration files actually found:")
        for file in files:
            _log.debug(f"  {file}")

    return config