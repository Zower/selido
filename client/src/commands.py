import requests
import json

from config_file import ConfigFile, ParsingError
from pathlib import Path

configLocation = Path(str(Path.home()) + '/.selido/')
configName = 'conf.toml'

##############################################
# Local commands


def init(args):
    try:
        Path(configLocation).mkdir(parents=True, exist_ok=True)
        f = open(configLocation / configName, "x")
    except FileExistsError:
        print('Config file already exists')
        exit(1)

    config = get_config()

    config.set('Endpoint.url', 'http://localhost')
    config.set('Endpoint.port', '3912')
    config.save()


def set_endpoint(args):
    config = get_config()

    url = args.url.split(':')

    try:
        config.set('Endpoint.url', url[0])
        config.set('Endpoint.port', url[1])
    except:
        print("Invalid url, Should be: Domain:port or IP:Port")
        exit()
    config.save()

#############################################
# Online commands


def add(args):
    args = set_url(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(args.tags))

    r = requests.post(args.url + '/resource/',
                      json=body)
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def get(args):
    args = set_url(args)

    r = requests.get(args.url + '/get/' + args.id)
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def find(args):
    args = set_url(args)

    body = {}
    body = add_to_body(body, 'tags',  make_tags(args.tags))
    body = add_to_body(body, 'and_search', not args.or_search)
    body = add_to_body(body, 'all', args.all)
    print(args.url)
    r = requests.post(args.url + '/find/', json=body)
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def add_tags(args):
    args = set_url(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(args.tags))

    r = requests.post(args.url + '/tag/' + args.id,
                      json=body)
    parsed = parse_response(r.text)
    print_parsed_response(parsed)


def del_tags(args):
    args = set_url(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(args.tags))

    r = requests.delete(args.url + '/tag/' + args.id,
                        json=body)
    parsed = parse_response(r.text)
    print_parsed_response(parsed)

#############################################
# Helpers


def make_tags(tags):  # Make tags into json
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


def add_to_body(body, name, item):  # Returns a copy of the body with the new item appended
    copy = body
    body[name] = item
    return copy


def parse_response(response):  # Parse response as JSON
    parsed = json.loads(response)
    return parsed


def set_url(args):
    copy = args
    config = get_config()
    copy.url = config.get('Endpoint.url') + ':' + config.get(
        'Endpoint.port')
    return copy


def get_config():
    try:
        config = ConfigFile(configLocation / configName)
        return config
    except ParsingError:
        print("Could not parse the config file, check that it hasn't been modified. Location: " +
              configLocation + configName)
        exit(1)
    except ValueError:
        print(
            "Config file extension that isn't supported was used or is a directory"
        )
        exit(1)
    except FileNotFoundError:
        print('Configuration file wasnt found at location ' +
              str(configLocation) + ', maybe run selido init?')
        exit(1)

#############################################
# Printers, should be its own file?


def print_parsed_response(parsed):
    if parsed['action'] == 'get' or parsed['action'] == 'find':
        print_tags(parsed)


# def print_columned_response(parsed, indent=30):
    # if indent <= 5:
    #     print("Indent on pretty print was set to 5 or less, exiting")
    #     exit(1)

    # if parsed['action'] == 'get':
    #     print_get(parsed, indent)
    # elif parsed['action'] == 'tag':
    #     print_tag(parsed, indent)


def print_tags(parsed):
    # print(parsed)
    if parsed['code'] == 200:
        # if len(object['name']) > indent - 5:
        #     print(object['name'][0:indent - 5] + '..   ', end='')
        # else:
        #     indent_length = indent - len(object['name'])
        #     print(object['name'] + ' ' * indent_length, end='')
        for el in parsed['objects']:
            print(el['id'], end='\t')
            list_tags = []
            for tag in el['tags']:
                tag_str = tag['key']
                if 'value' in tag:
                    tag_str += ':' + tag['value']
                list_tags.append(tag_str)
            print(", ".join(list_tags))
    else:
        print(parsed['message'])
        print('------')
        print(parsed)


def print_tag(parsed, indent):
    print(parsed['message'])
    exit(0)
