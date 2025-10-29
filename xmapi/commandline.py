import argparse
import textwrap

# Automatically loaded and executed when this module is loaded.
# 
# Parses the command line. Arguments can be added by adding another parser#add_argument() call.
#
# See https://docs.python.org/3/library/argparse.html

def get_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
                                     description=textwrap.dedent(
"""XM Cyber Script Shell

This is a program shell to aid calling XM Cyber APIs. Use this shell to 
create more complex scripts that create, call and process API calls.

Using this shell program provides default command-line and configuration-file
entries useful for making XM Cyber API calls. Some of the command line 
arguments can appear in configuration files, thereby allowing them to be
specified across multiple script calls.

Configuration files are always named "xmapi.ini" and are searched for in
the following locations:

  * {working-directory}/xmapi.ini
  * {user-home}/.xmcyber/xmapi.ini
  * {global-home}/.xmcyber/xmapi.ini

The same keys may appear in multiple ini files, but the one "nearest" to the
script will be used. For instance, if the same key appears in the ini file
in the working-directory and the in the user-home, the one in the 
working-directory takes precedence.

Command line arguments take precedence over ini files. 

"""), epilog=textwrap.dedent(
"""***************************************************
Each ini file contains a default namespace that must be explicitly declared.
Within this namespace are zero or more key/value pairs, corresponding to the
command line arguments. Format is as follows:

    [DEFAULT]
    key1 = value1
    key2 = value2

The key names correspond to the command line parameters, without any hyphens.
So specifying the API key in a config file would look something like this:

    [DEFAULT]
    key = a123b45678c901d2e345f6789ab012c3
"""
))
    parser.add_argument("-s", "--subdomain", help="Subdomain of a SaaS tenant. Will be prepended to clients.xmcyber.com")
    parser.add_argument("-k", "--key", help="API Key to use when accessing the API")
    parser.add_argument("-c", "--chunk", help="The section of the INI file to use (default: DEFAULT)", default="DEFAULT")
    parser.add_argument("-q", "--quiet", help="Only output log messages indicating errors", action='store_true')
    parser.add_argument("-v", "--verbose", help="Output extended log information", action='store_true')
    parser.add_argument("--proxy_port", help="The proxy server port; required if --proxy_url specified", type=int, metavar="NUM")
    parser.add_argument("--proxy_url", help="The proxy server URL, if present", metavar="URL")
    return parser