import requests
import json

from config_file import ConfigFile
from pathlib import Path

configLocation = str(Path.home()) + '/.selido/conf.toml'

##############################################
# Local commands


def get_config():
    try:
        config = ConfigFile(configLocation)
        return config
    except ParsingError:
        print("Could not parse the config file")
        exit(1)
    except ValueError:
        print(
            "Config file extension that isn't supported was used or is a directory"
        )
        exit(1)
    except FileNotFoundError:
        print("Config file does not exist")
        exit(1)


def init(args):
    try:
        f = open(configLocation, "x")
    except FileExistsError:
        print('Config file already exists')
        exit(1)

    config = get_config()

    config.set('Endpoint.URL', 'localhost')
    config.set('Endpoint.Port', '3912')
    config.save()


def set_endpoint(args):
    config = get_config()

    URL = args.URL.split(':')

    try:
        config.set('Endpoint.URL', URL[0])
        config.set('Endpoint.Port', URL[1])
    except:
        print("Invalid URL, Should be: Domain:port or IP:Port")
        exit()
    config.save()

#############################################
# Online commands


def get(args):
    r = requests.get(args.URL + '/get/' + args.resource,
                     json=make_tags(args.tags))
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def add(args):
    r = requests.post(args.URL + '/add/' + args.resource,
                      json=make_tags(args.tags))
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def add_tags(args):
    r = requests.post(args.URL + '/tag/' + args.resource,
                      json=make_tags(args.tags))
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def del_tags(args):
    r = requests.delete(args.URL + '/tag/' + args.resource,
                        json=make_tags(args.tags))
    parsed = parse_response(r.text)
    print_parsed_response(parsed)

#############################################
# Helpers


def print_parsed_response(parsed, indent=30):
    if indent <= 5:
        print("Indent on pretty print was set to 5 or less, exiting")
        exit(1)

    if len(parsed['objects']) == 0:
        print(parsed['message'])
        exit(0)

    if parsed['action'] == 'get':
        print_get(parsed, indent)


def print_get(parsed, indent):
    indent_length = indent - 4  # 4 for the letters in name
    print("Name" + ' ' * indent_length + "Tags")

    for object in parsed['objects']:

        if len(object['name']) > indent - 5:
            print(object['name'][0:indent - 5] + '..   ', end='')
        else:
            indent_length = indent - len(object['name'])
            print(object['name'] + ' ' * indent_length, end='')
        list_tags = []
        for tag in object['tags']:
            tag_str = tag['key']
            if 'value' in tag:
                tag_str += ':' + tag['value']
            list_tags.append(tag_str)
        print(", ".join(list_tags))


def make_tags(tags):
    tags_list = []
    if tags:
        tags = tags.split(',')
        for tag in tags:
            tag = tag.split(':')
            if len(tag) == 1:
                tags_list.append({'key': tag[0]})
            else:
                tags_list.append({'key': tag[0], 'value': tag[1]})
    return tags_list


def parse_response(response):
    parsed = json.loads(response)
    return parsed
