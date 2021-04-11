import requests
import subprocess
import os
import platform
import json

import helpers
import core

from enum import Enum, auto


#############################################
# Online commands


def add(args):
    args = helpers.check_defaults(args)

    b = core.Body()
    b.add('tags', helpers.make_tags(helpers.split_tags(args.tags)))

    r = send_request(args, Method.POST, '/resource/', b.get())

    parse_response(r.text, True)


def delete(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    b = core.Body()
    b.add('ids', parsed_ids)

    r = send_request(args, Method.DELETE, '/resource/', b.get())

    parse_response(r.text, True)


def find(args):
    args = helpers.check_defaults(args)

    b = core.Body()

    if args.all:
        b.add('all', args.all)
        r = send_request(args, Method.POST, '/find/', b.get())
    else:
        parsed_search = helpers.parse_search_tags(args.searchterm)

        tags = helpers.make_tags(parsed_search.tags)
        b.add('keys', parsed_search.keys)
        b.add('tags', tags)
        b.add('and_search', not args.or_search)

        r = send_request(args, Method.POST, '/find/', b.get())

    parsed = parse_response(r.text)

    exclude = []
    # if args.auto_exclude and args.tags:
    #     for t in args.tags.split(','):
    #         exclude.append(t.split(':', 1)[0])
    if args.exclude:
        for t in args.exclude.split(','):
            exclude.append(t)

    items = helpers.items_from_list_of_dict(
        parsed['objects'], exclude, args.sort)

    columns = None
    if args.columns:
        columns = args.columns.split(",")

    if not args.indent:
        printer = core.TagPrinter(
            items, with_id=not args.no_id, key_columns=columns)

    else:
        printer = core.TagPrinter(
            items, with_id=not args.no_id, key_columns=columns, indent_tags=int(args.indent))
    printer.print()


def get(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    b = core.Body()
    b.add('ids', parsed_ids)

    r = send_request(args, Method.GET, '/get/', b.get())

    parsed = parse_response(r.text)
    items = helpers.items_from_list_of_dict(parsed['objects'])

    printer = core.TagPrinter(items, with_id=not args.no_id)
    printer.print()


def open_file(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    r = send_request(args, Method.GET, '/get/' + parsed_ids[0])

    parsed = parse_response(r.text)
    item = helpers.items_from_list_of_dict(parsed['objects'])[0]
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

    parsed_ids = helpers.parse_ids(args.searchterm)

    b = core.Body()
    b.add('tags', helpers.make_tags(helpers.split_tags(args.tags)))
    b.add('ids', parsed_ids)

    r = send_request(args, Method.POST, '/tag/', b.get())

    parse_response(r.text, True)


def del_tags(args):
    args = helpers.check_defaults(args)

    parsed_ids = helpers.parse_ids(args.searchterm)

    b = core.Body()
    b.add('tags', helpers.make_tags(helpers.split_tags(args.tags)))
    b.add('ids', parsed_ids)

    r = send_request(args, Method.DELETE, '/tag/', b.get())

    parse_response(r.text, True)


#############################################
# Helpers

def send_request(args, method, url, body=None):  # Mother send command
    s = requests.Session()
    s.verify = args.ca_file
    s.cert = args.cert
    url = args.url + url
    try:
        if method == Method.GET and body:
            r = s.get(url, json=body)
        elif method == Method.GET:
            r = s.get(url)
        elif method == Method.POST and body:
            r = s.post(url, json=body)
        elif method == Method.DELETE and body:
            r = s.delete(url, json=body)
        elif method == Method.DELETE:
            r = s.delete(url)
    except requests.ConnectionError as e:
        # TODO: Check for more types of error and print appropriate message
        print("Something went wrong connecting to selido:")
        print(e)
        exit(1)
    return r

# Parse response as JSON, exit if code is not equal 200


def parse_response(response, print_message=False, check_code=True):
    parsed = json.loads(response)

    if check_code and parsed['code'] != 200:
        print("{code}: {message}".format(
            code=parsed['code'], message=parsed['message']))
        exit(0)
    elif print_message:
        print(parsed['message'])

    return parsed


#############################################
# Classes
class Method(Enum):  # Maybe more to be added later
    GET = auto()
    POST = auto()
    DELETE = auto()
