import re
import hashlib
import json

import selido.config as config
import selido.printing as printing

from pathlib import Path

# Classes


class Search:
    def __init__(self):
        self._keys = []
        self._tags = []
        self._not_keys = []
        self._not_tags = []

    # Parses a search term in the +-{ID} format, setting the appropriate values
    def parse_and_set_search_tags(self, search_term):
        if not search_term:
            print("No search fields specified")
            exit(1)

        values = search_term.split(',')

        for value in values:
            # Finds everything that begins with +-, -+, + or -, then returns the matches
            special = re.findall("^\+-|^-\+|^-|^\+", value)

            # Just a key
            if len(special) == 0:
                self._keys.append(value)
            else:
                # We are only interested in the first match, as its the beginning of the string anyway
                special = special[0]

                # Contains + and -
                if len(special) == 2:
                    # Both a value and a not term
                    self._not_tags.append(value[2:])

                # Contains just - or +
                else:
                    # Just a value
                    if ('+' in special):
                        self._tags.append(value[1:])
                    # Regular not key
                    else:
                        self._not_keys.append(value[1:])

    def keys(self):
        return self._keys

    def tags(self):
        return self._tags

    def not_keys(self):
        return self._not_keys

    def not_tags(self):
        return self._not_tags


###########################
# Argument parsing

def get_default_url(auth=False):
    conf = config.SelidoConfig(config.get_config())
    if auth:
        increment = 1
    else:
        increment = 0
    return conf.get_endpoint(increment)


def get_default_ca():
    return config.CERTS_LOCATION / 'ca.crt'


def get_default_certs():
    conf = config.SelidoConfig(config.get_config())
    un = conf.get_username()
    return (config.CERTS_LOCATION / (un + '.crt'),
            config.CERTS_LOCATION / (un + '.key'))


###########################
# Text parsing

# Parse response from json to dict
def parse_response(response, print_message=False, check_code=True):
    parsed = json.loads(response)

    if check_code and parsed['code'] != 200:
        print("{code}: {message}".format(
            code=parsed['code'], message=parsed['message']))
        exit(0)
    elif print_message:
        print(parsed['message'])

    return parsed


def parse_ids(search_term):  # Parses multiple ids, checking if its a regular ID or something else, in which case it looks for it in the cache
    ids = []
    values = search_term.split(',')
    oc = printing.Option()

    for value in values:
        # Regular id
        if len(value) == 24:
            ids.append(value)
        else:
            ids.append(oc.find_cached(value))

    return ids
