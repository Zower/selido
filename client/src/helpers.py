import re
import hashlib

import config
import option
import core

from pathlib import Path


# Constants

# Classes


class Search:
    def __init__(self, keys=[], tags=[], not_keys=[], not_tags=[]):
        self.keys = keys
        self.tags = tags
        self.not_keys = not_keys
        self.not_tags = not_tags


# Functions


def check_defaults(args):
    args = check_url(args)
    args = check_user_cert(args)
    args = check_ca_cert(args)
    return args


def check_url(args, auth=False):
    if not args.url:
        conf = config.get_config()
        args.url = conf.get('Endpoint.url')
        port = conf.get('Endpoint.port')
        if port != '':
            if auth:
                args.url += ':' + str(int(port) + 1)
            else:
                args.url += ':' + port
        return args
    else:
        return args


def check_user_cert(args):
    conf = config.get_config()
    if not args.user_certs:
        un = conf.get('Cert.username')
        args.cert = (config.certs_location / (un + '.crt'),
                     config.certs_location / (un + '.key'))
        return args
    else:
        split = args.user_certs.split(',')
        if not len(split) == 2:
            print(
                "Please specify two locations for the certificate files, comma-separated")
            exit(1)

        args.cert = (Path(split[0]),
                     Path(split[1]))
        return args


def check_ca_cert(args):
    if not args.ca_file:
        args.ca_file = config.certs_location / 'ca.crt'
        return args
    else:
        return args


def parse_ids(search_term):  # Parses multiple ids, also checks cache if its just a basic number
    ids = []
    values = search_term.split(',')
    oc = option.Option()

    for value in values:
        # Regular id
        if len(value) == 24:
            ids.append(value)
        else:
            ids.append(oc.find_cached(value))

    return ids


# Returns a Search class with the different options set.
def parse_search_tags(search_term):
    keys = []
    tags = []
    not_keys = []
    not_tags = []

    if not search_term:
        print("No search fields specified")
        exit(1)

    values = search_term.split(',')

    for value in values:
        # Finds everything that begins with +-, -+, + or -, then returns the matches
        special = re.findall("^\+-|^-\+|^-|^\+", value)

        # Just a key
        if len(special) == 0:
            keys.append(value)
        else:
            # We are only interested in the first match, as its the beginning of the string anyway
            special = special[0]

            # Contains + and -
            if len(special) == 2:
                # Both a value and a not term
                not_tags.append(value[2:])

            # Contains just - or +
            else:
                # Just a value
                if ('+' in special):
                    tags.append(value[1:])
                # Regular not key
                else:
                    not_keys.append(value[1:])

    return Search(keys, tags, not_keys, not_tags)


def print_sha3_hex_hash(string):
    s = hashlib.sha3_256()
    s.update(string.encode('utf-8'))

    print("Hash is:")
    print(s.hexdigest())


def items_from_list_of_dict(dict_list, keys_to_ignore=[], sort=False):
    items = []
    for item in dict_list:
        tags = []
        for tag in item['tags']:
            if not tag['key'] in keys_to_ignore:
                if 'value' in tag:
                    tags.append(core.Tag(tag['key'], tag['value']))
                else:
                    tags.append(core.Tag(tag['key']))
        items.append(core.Item(item['id'], tags))
        if sort:
            # Forcing sort to use string representation of tag
            tags.sort(key=lambda x: str(x))
    return items


def split_tags(tags):
    if tags:
        copy = tags.split(',')
    return copy


def make_tags(tags):  # Make tags into json
    tags_list = []
    for tag in tags:
        tag = tag.split(':', 1)

        if len(tag) == 1:
            tags_list.append({'key': tag[0]})
        else:
            if tag[1] != '':
                tags_list.append({'key': tag[0], 'value': tag[1]})
            else:
                tags_list.append({'key': tag[0]})
    return tags_list
