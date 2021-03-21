import requests
import json
from enum import Enum, auto
import hashlib
from threading import Timer

from config_file import ConfigFile, ParsingError
from pathlib import Path

configLocation = Path(str(Path.home()) + '/.selido/')
certsLocation = Path(str(Path.home()) + '/.selido/certs/')
configName = 'conf.toml'

##############################################
# Local commands


def init(args):  # Should be more robust
    try:
        Path(configLocation).mkdir(parents=True, exist_ok=True)
        Path(certsLocation).mkdir(parents=True, exist_ok=True)
        f = open(configLocation / configName, "x")
    except FileExistsError:
        print('Config file directory or certs directory already exists')
        exit(1)

    e = input(
        "Where to connect to selido? If running locally it is likely \"https://localhost:3912\": ")

    set_endpoint(e)


def endpoint(args):
    set_endpoint(args.url)


def username(args):
    set_username(args.username)

#############################################
# Online commands


def add(args):
    args = check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(
        args.tags))

    r = send_request(args, Method.POST, '/resource/', body)

    parsed = parse_response(r.text)


def auth_request(args):
    args = check_url(args, True)

    r = requests.get(args.url + '/authenticate/ca/', verify=False)

    parsed = parse_response(r.text, False)

    print(parsed)

    print_sha3_hex_hash(parsed['objects'])

    ans = input(
        "Type 'selido auth hash' on an authenticated machine, then make absolutely sure the two hashes match, if not, ABORT. Continue? (y/n): ")

    if ans == 'y':
        try:
            with open(certsLocation / 'ca.crt', "w") as f:
                f.write(parsed['objects'])
        except OSError as e:
            print(e)
            exit(1)

        a = requests.get(args.url + '/authenticate/' + args.name,
                         verify=certsLocation / 'ca.crt')
        parsed = parse_response(a.text)

        try:
            with open(certsLocation / (args.name + '.key'), "w") as f:
                f.write(parsed['objects']['key'])
        except OSError as e:
            print(e)
            exit(1)

        print("Type selido auth verify on an authenticated client.")
        print("Waiting for verification from authenticated client..")

        body = {}
        obj = {'name': args.name, 'code': parsed['objects']['code']}
        body = add_to_body(body, 'code', obj)

        Timer(0.5, auth_authenticated_yet, [
            args, body]).start()


def auth_authenticated_yet(args, body):
    print("Yay")
    print(body)
    r = requests.post(args.url + '/authenticated/',
                      json=body,
                      verify=certsLocation / 'ca.crt')
    if r.status_code == 200:
        parsed = parse_response(r.text)
        print(parsed)
        try:
            with open(certsLocation / (args.name + '.crt'), "w") as f:
                f.write(parsed['objects'])
            print("You are now verified!")
            exit(0)
        except OSError as e:
            print(e)
            exit(1)
        print('yay')
    elif r.status_code == 403:
        # Still waiting
        Timer(0.5, auth_authenticated_yet, [args, body]).start()
    else:
        print("Something went wrong, exiting")
        print(parse_response(r.text))
        exit(1)


def auth_hash(args):
    args = check_ca_cert(args)

    with open(args.ca_file, "r") as f:
        print_sha3_hex_hash(str(f.read()))


def auth_verify(args):
    args = check_defaults(args)

    r = send_request(args, Method.GET, '/authenticate/')
    parsed = parse_response(r.text)

    body = {}
    body = add_to_body(body, "code", parsed['objects'][0])

    p = send_request(args, Method.POST, '/authenticate/', body)
    print(p.text)


def delete(args):
    args = check_defaults(args)

    r = send_request(args, Method.DELETE, '/resource/' + args.id)

    parsed = parse_response(r.text)


def find(args):
    args = check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags',  make_tags(args.tags))
    body = add_to_body(body, 'and_search', not args.or_search)
    body = add_to_body(body, 'all', args.all)

    r = send_request(args, Method.POST, '/find/', body)
    parse_response(r.text)


def get(args):
    args = check_defaults(args)

    r = send_request(args, Method.GET, '/get/' + args.id)

    parsed = parse_response(r.text)


def add_tags(args):
    args = check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(args.tags))

    r = send_request(args, Method.POST, '/tag/' + args.id, body)

    parse_response(r.text)


def del_tags(args):
    args = check_defaults(args)

    body = {}
    body = add_to_body(body, 'tags', make_tags(args.tags))

    r = send_request(args, Method.DELETE, '/tag/' + args.id, body)

    parse_response(r.text)


def send_request(args, method, url, body=None):  # Mother command
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
        print("Something went wrong connecting to selido")
        print(e)
        # exit(1)
    return r

#############################################
# Helpers


def check_defaults(args):
    args = check_url(args)
    args = check_user_cert(args)
    args = check_ca_cert(args)
    return args


def check_url(args, auth=False):
    if not args.url:
        copy = args
        config = get_config()
        copy.url = config.get('Endpoint.url')
        port = config.get('Endpoint.port')
        if port != '':
            if auth:
                copy.url += ':' + str(int(port) + 1)
            else:
                copy.url += ':' + port
        return copy
    else:
        return args


def check_user_cert(args):
    copy = args
    config = get_config()
    if not args.username:
        un = config.get('Cert.username')
        copy.username = un
    else:
        un = args.username
    copy.cert = (certsLocation / (un + '.crt'), certsLocation / (un + '.key'))
    return copy


def check_ca_cert(args):
    if not args.ca_file:
        copy = args
        config = get_config()
        copy.ca_file = certsLocation / 'ca.crt'
        return copy
    else:
        return args


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


def parse_response(response, print=True):  # Parse response as JSON
    parsed = json.loads(response)
    if print:
        print_parsed_response(parsed)
    return parsed


def set_username(username):
    config = get_config()
    try:
        config.set('Cert.username', username)
    except:
        print("Couldn't set username, make sure username is one word")
        exit(1)
    config.save()


def set_endpoint(url):
    config = get_config()

    url_split = url.split(':')

    # This is some jank shit, but https:// get split up so I'm merging them back together
    new_url = []
    new_url.append(url_split[0] + ':' + url_split[1])
    if len(url_split) == 3:
        new_url.append(url_split[2])
    try:
        config.set('Endpoint.url', new_url[0])
        if len(new_url) == 2:
            config.set('Endpoint.port', new_url[1])
        else:
            config.set('Endpoint.port', "")
    except:
        print("Invalid url, Should be: Domain:Port or IP:Port")
        exit(1)
    config.save()


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
    else:
        print(parsed)


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


def print_sha3_hex_hash(string):
    print(repr(string))
    s = hashlib.sha3_256()
    s.update(string.encode('utf-8'))

    print("Hash is:")
    print(s.hexdigest())


class Method(Enum):  # Maybe more to be added later
    GET = auto()
    POST = auto()
    DELETE = auto()
