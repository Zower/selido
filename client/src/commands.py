import requests
import subprocess
import os
import platform
import json

import helpers
import tag

from enum import Enum, auto


#############################################
# Online commands


def add(args):
    args = helpers.check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(
        split_tags(args.tags)))

    r = send_request(args, Method.POST, '/resource/', body)

    parsed = parse_response(r.text, True)


def delete(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    r = send_request(args, Method.DELETE, '/resource/' + parsed_ids[0])

    parsed = parse_response(r.text, True)


def find(args):
    args = helpers.check_defaults(args)

    body = {}

    if args.all:
        body = add_to_body(body, 'all', args.all)
        r = send_request(args, Method.POST, '/find/', body)
    else:
        parsed_search = helpers.parse_search_tags(args.searchterm)

        tags = make_tags(parsed_search.tags)
        body = add_to_body(body, 'keys', parsed_search.keys)
        body = add_to_body(body, 'tags', tags)
        body = add_to_body(body, 'and_search', not args.or_search)

        r = send_request(args, Method.POST, '/find/', body)

    parsed = parse_response(r.text)

    exclude = []
    # if args.auto_exclude and args.tags:
    #     for t in args.tags.split(','):
    #         exclude.append(t.split(':', 1)[0])
    if args.exclude:
        for t in args.exclude.split(','):
            exclude.append(t)

    items = tag.items_from_list_of_dict(parsed['objects'], exclude, args.sort)

    columns = None
    if args.columns:
        columns = args.columns.split(",")

    printer = tag.TagPrinter(
        items, with_id=not args.no_id, key_columns=columns)
    printer.print()


def get(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    r = send_request(args, Method.GET, '/get/' + parsed_ids[0])

    parsed = parse_response(r.text)
    items = tag.items_from_list_of_dict(parsed['objects'])

    printer = tag.TagPrinter(items, with_id=not args.no_id)
    printer.print()


def open_file(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    r = send_request(args, Method.GET, '/get/' + parsed_ids[0])

    parsed = parse_response(r.text)
    item = tag.items_from_list_of_dict(parsed['objects'])[0]
    for t in item.tags:
        if t.key == 'path':
            if platform.system() == 'Darwin':
                subprocess.call(('open', t.value))
            elif platform.system() == 'Windows':
                os.startfile(t.value)
            else:
                subprocess.call(('xdg-open', t.value))


def add_tags(args):
    args = helpers.check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(split_tags(args.tags)))

    parsed_ids = helpers.parse_ids(args.searchterm)

    r = send_request(args, Method.POST, '/tag/' + parsed_ids[0], body)

    parse_response(r.text, True)


def del_tags(args):
    args = helpers.check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(split_tags(args.tags)))

    parsed_ids = helpers.parse_ids(args.searchterm)

    r = send_request(args, Method.DELETE, '/tag/' + parsed_ids[0], body)

    parse_response(r.text, True)


#############################################
# Helpers

def send_request(args, method, url, body=None):  # Mother send command
    s = requests.Session()
    s.verify = args.ca_file
    s.cert = args.cert
    url = args.url + url
    try:
        if method == Method.GET:
            r = s.get(url)
        elif method == Method.POST and body:
            r = s.post(url, json=body)
        elif method == Method.DELETE and not body:
            r = s.delete(url)
        elif method == Method.DELETE and body:
            r = s.delete(url, json=body)
    except requests.ConnectionError as e:
        # TODO: Check for more types of error and print appropriate message
        print("Something went wrong connecting to selido:")
        print(e)
        exit(1)
    return r


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


def add_to_body(body, name, item):  # Returns the body with the new item appended
    body[name] = item
    return body


# Parse response as JSON, exit if code is not equal 200
def parse_response(response, check_code=True):
    parsed = json.loads(response)

    if check_code and parsed['code'] != 200:
        print("{code}: {message}".format(
            code=parsed['code'], message=parsed['message']))
        exit(0)

    return parsed


#############################################
# Classes
class Method(Enum):  # Maybe more to be added later
    GET = auto()
    POST = auto()
    DELETE = auto()
