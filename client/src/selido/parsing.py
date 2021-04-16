import re
import hashlib
import json

from selido.options import Options

import selido.config as config

from pathlib import Path
from typing import List
from dataclasses import dataclass, field

# Classes


@dataclass
class Tag:
    key: str
    value: str = None

    def __str__(self):
        if self.value:
            return self.key + ":" + self.value
        else:
            return self.key


@dataclass
class Resource:
    id: str  # ID as returned from the server
    tags: List[Tag]  # Tags associated with this ID, a list of type "Tag"


@dataclass
class SearchTerm:
    search_term: str

    # Parses a search term in the +-{ID} format, setting the appropriate values
    def parse(self):
        self._keys = []
        self._tags = []
        self._not_keys = []
        self._not_tags = []
        if not self.search_term:
            print("No search fields specified")
            exit(1)

        values = self.search_term.split(',')

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
# Search parsing


def parse_ids(search_term):  # Parses multiple ids, checking if its a regular ID or something else, in which case it looks for it in the cache
    ids = []
    values = search_term.split(',')
    oc = Options()

    for value in values:
        # Regular id
        if len(value) == 24:
            ids.append(value)
        else:
            ids.append(oc.find_cached(value))

    return ids

###########################
# Response parsing

# Parse response from json to dict


# Creates Resource types from a list of dictionaries, with each dictionary being one resource in the format returned from server, e.g. {'id': '2309f001FA0023123', 'tags': [{'key': 'test', 'value':'true'}]}


@dataclass
class SelidoParser:
    response_text: str  # r.text as returned by requests
    # keys_to_ignore: List[str] = field()

    # Parse response and return the entire object

    def parse(self, print_message=False, check_code=True):
        self._parse()
        if check_code and self.parsed['code'] != 200:
            print("{code}: {message}".format(
                code=self.parsed['code'], message=self.parsed['message']))
            exit(0)
        elif print_message:
            print(self.parsed['message'])

        return self.parsed

    # Parse response and return objects as list filled with Tag objects
    def parse_resources(self, keys_to_ignore=[], sort=False):
        self._parse()
        self.resources = []
        if 'objects' in self.parsed:
            for item in self.parsed['objects']:
                tags = []
                for tag in item['tags']:
                    if not tag['key'] in keys_to_ignore:
                        if 'value' in tag:
                            tags.append(Tag(tag['key'], tag['value']))
                        else:
                            tags.append(Tag(tag['key']))
                self.resources.append(Resource(item['id'], tags))
                if sort:
                    # Forcing sort to use string representation of tag
                    tags.sort(key=lambda x: str(x))

        return self.resources

    def _parse(self):
        self.parsed = json.loads(self.response_text)
