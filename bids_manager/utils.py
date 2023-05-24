"""Useful functions for Bids Manager."""
# Authors: Christian Ferreyra, chrisferreyra13@gmail.com
# Date: 2022

import os
import json
import requests


def get_api_endpoint(api_config):
    # creating api endpoint
    server_url = f'http://{api_config["ip"]}:{api_config["port"]}/'
    databases_url = server_url+api_config["databases_endpoint"]+'/'

    return server_url, databases_url


def get_parsing(api_config, bidsdb_name, user='user', timeout=60):
    """Fetch for lastes parsing file."""
    # creating api endpoint
    server_url, databases_url = get_api_endpoint(api_config)
    db_endpoint = databases_url+bidsdb_name

    # send user
    payload = {"user": user}
    access_endpoint = db_endpoint+'/access'
    parsing = False
    try:
        r = requests.post(url=access_endpoint, params=payload, timeout=timeout)
    except Exception as ex:
        print(ex)
        return None, parsing

    if not r.ok:
        return None, parsing

    try:
        r = requests.get(url=db_endpoint, timeout=timeout)
    except Exception as ex:
        print(ex)
        return None, parsing

    if r.ok:
        # extracting data in json format
        last_parsing = r.json()
        # check if it is not empty
        if last_parsing:
            return last_parsing, parsing
    else:
        try:
            content = r.json()
        except Exception as ex:
            print(ex)
            return None, parsing

        if (r.status_code == 503
                and content['detail'] == (f"Parsing {bidsdb_name}.")):
            parsing = True
            return None, parsing

    return None, parsing


def get_app_paths():
    """Return important paths like config."""
    cwd = os.getcwd()
    # app_path = os.path.join(cwd, 'bids_manager')
    config_path = os.path.join(cwd, 'config')

    return config_path


def get_api_config(config_path):
    """Return api configuration."""
    filepath = os.path.join(config_path, 'bids_manager_server.json')
    if not os.path.exists(filepath):
        # missing is interpreted as not unwanted
        return None

    try:
        with open(filepath, 'r') as f:
            api_config = json.load(f)
    except Exception as ex:
        raise ex

    if not api_config:
        # empty is interpreted as not unwanted
        return None

    if "ip" not in api_config.keys():
        raise ValueError(
            "Missing 'ip' in bids manager server configuration")

    if "port" not in api_config.keys():
        raise ValueError(
            "Missing 'port' in bids manager server configuration")

    if "databases_endpoint" not in api_config.keys():
        raise ValueError(
            "Missing 'databases_endpoint' in bids manager server configuration"
        )

    return api_config


def get_remote_config(config_path):
    """Return remote databases configuration."""
    filepath = os.path.join(config_path, 'remote_bids_db.json')
    if not os.path.exists(filepath):
        # missing is interpreted as not unwanted
        return dict(), list()

    try:
        with open(filepath, 'r') as f:
            remote_config = json.load(f)
    except Exception as ex:
        raise ex

    if not remote_config:
        # empty is interpreted as not unwanted
        return dict(), list()

    if "bids_databases" not in remote_config.keys():
        raise ValueError("Missing 'bids_databases' in remote configuration")

    keys = ['db_name', 'db_path']
    valid_config = {'bids_databases': list()}
    # list of bad configurations
    bad_config = list()
    if isinstance(remote_config["bids_databases"], list):
        for config in remote_config["bids_databases"]:
            if any(k not in config.keys() for k in keys):
                raise ValueError(
                    "Missing 'db_name' or 'db_path' in remote configuration")

            # this is to check the access of the user because if the user
            # cannot enter in the folder, os.path.exists will be false
            # but the path is correct technically
            try:
                _ = os.stat(config["db_path"])
            except PermissionError:
                continue
            except FileNotFoundError:
                bad_config.append(config)
                continue

            valid_config["bids_databases"].append(config)
    else:
        raise TypeError('Expecting a list of database configurations')

    return valid_config, bad_config
