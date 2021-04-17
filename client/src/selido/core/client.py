import requests
import subprocess
import os
import platform
import json

from enum import Enum, auto
from dataclasses import dataclass, field

from selido.parsing import SelidoParser, SearchTerm, parse_ids
from selido.printing import TagPrinter

#############################################
# Online commands


def add(args):
    b = Body()

    b.add('tags', _make_tags(_split_tags(args.tags)))

    r = send_request(args, Method.POST, '/resource/', b.get())

    parser = SelidoParser(r.text)

    parser.parse(r.text, True)


def delete(args):
    parsed_ids = parse_ids(args.searchterm)

    b = Body()
    b.add('ids', parsed_ids)

    r = send_request(args, Method.DELETE, '/resource/', b.get())

    parser = SelidoParser(r.text)

    parser.parse(True)


def find(args):
    b = Body()

    search = SearchTerm(args.searchterm)

    if args.all:
        b.add('all', args.all)
        r = send_request(args, Method.POST, '/find/', b.get())
    else:
        search.parse()

        tags = _make_tags(search.tags())

        b.add('keys', search.keys())
        b.add('tags', tags)
        b.add('and_search', not args.or_search)

        r = send_request(args, Method.POST, '/find/', b.get())

    exclude = []

    if args.auto_exclude:
        for key in search.keys():
            exclude.append(key)
        for tag in search.tags():
            exclude.append(tag.split(':', 1)[0])

    if args.exclude:
        for t in args.exclude.split(','):
            exclude.append(t)

    parser = SelidoParser(r.text)
    resources = parser.parse_resources(exclude, args.sort)

    columns = args.columns
    if columns:
        columns = args.columns.split(",")

    printer = TagPrinter(
        resources, no_columns=args.no_columns, indentation_level=args.indent, key_columns=columns, with_id=args.with_id)

    if args.mcount:
        printer.mcount()
    else:
        printer.print()

    if args.count:
        printer.count()


def get(args):
    parsed_ids = parse_ids(args.searchterm)

    b = Body()
    b.add('ids', parsed_ids)

    r = send_request(args, Method.GET, '/get/', b.get())

    parser = SelidoParser(r.text)
    resources = parser.parse_resources()

    printer = TagPrinter(resources, no_columns=args.no_columns, with_id=True)
    printer.print()


def open_file(args):
    parsed_ids = parse_ids(args.searchterm)

    b = Body()
    parsed_ids = [parsed_ids[0]]
    b.add('ids', parsed_ids)

    r = send_request(args, Method.GET, '/get/', b.get())

    parser = SelidoParser(r.text)
    resources = parser.parse_resources()

    item = resources[0]
    for t in item.tags:
        if t.key == 'path':
            if platform.system() == 'Darwin':
                subprocess.call(('open', t.value))
            elif platform.system() == 'Windows':
                os.startfile(t.value)
            else:
                subprocess.call(('xdg-open', t.value))


def add_tags(args):
    parsed_ids = parse_ids(args.searchterm)

    b = Body()
    b.add('tags', _make_tags(_split_tags(args.tags)))
    b.add('ids', parsed_ids)

    r = send_request(args, Method.POST, '/tag/', b.get())

    parser = SelidoParser(r.text)
    parser.parse(True)


def del_tags(args):
    parsed_ids = parse_ids(args.searchterm)

    b = Body()
    b.add('tags', _make_tags(_split_tags(args.tags)))
    b.add('ids', parsed_ids)

    r = send_request(args, Method.DELETE, '/tag/', b.get())

    parser = SelidoParser(r.text)
    parser.parse(True)


def copy_tags(args):
    from_ids = parse_ids(args.from_ids)
    to_ids = parse_ids(args.to_ids)

    b = Body()
    b.add('from', from_ids)
    b.add('to', to_ids)

    r = send_request(args, Method.PATCH, '/tag/', b.get())

    parser = SelidoParser(r.text)
    parser.parse(True)


#############################################

def send_request(args, method, url, body=None):  # Mother send command
    s = requests.Session()
    s.verify = args.ca_file
    s.cert = args.user_certs
    s.timeout = 15

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
        elif method == Method.PATCH and body:
            r = s.patch(url, json=body)
    except requests.ConnectionError as e:
        # TODO: Check for more types of error and print appropriate message
        print("Something went wrong connecting to selido:")
        print(e)
        exit(1)
    return r


class Method(Enum):  # Enum representing HTTP request type
    GET = auto()
    POST = auto()
    DELETE = auto()
    PATCH = auto()


@dataclass
class Body:  # Represents a body to be sent with HTTP requests.
    limbs: dict = field(default_factory=dict)

    def get(self):
        return self.limbs

    def add(self, name, value):
        self.limbs[name] = value

    def remove(self, name):
        return self.limbs.pop(name)


def _split_tags(tags):  # Split tags on comma
    if tags:
        copy = tags.split(',')
    return copy


def _make_tags(tags):  # Make tags into json
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
