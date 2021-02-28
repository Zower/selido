import requests
import argparse
from config_file import ConfigFile
from pathlib import Path

URI = ''
configLocation = str(Path.home()) + '/.selido/conf.toml'

parser = argparse.ArgumentParser(
    prog='selido',
    description='Client to interact with selido server',
    usage='selido [flags] [options]')

subparsers = parser.add_subparsers(dest='Initial command')
subparsers.required = True


def get_config():
    try:
        config = ConfigFile(configLocation)
        return config
    except ParsingError:
        print("Could not parse the config file")
        exit()
    except ValueError:
        print(
            "Config file extension that isn't supported was used or is a directory"
        )
    except FileNotFoundError:
        print("Config file does not exist")


def init(args):
    try:
        f = open(configLocation, "x")
    except FileExistsError:
        print('Config file already exists')
        exit()

    print(configLocation)

    config = get_config()

    config.set('Endpoint.URL', '')
    config.set('Endpoint.Port', '')
    config.save()


def set_endpoint(args):
    config = get_config()

    URI = args.URI.split(':')

    try:
        config.set('Endpoint.URL', URI[0])
        config.set('Endpoint.Port', URI[1])
    except:
        print("Invalid URI, Should be: URL:Port")
    config.save()


def get(args):
    config = get_config()
    r = requests.get('http://' + config.get('Endpoint.URL') + ':' +
                     config.get('Endpoint.Port'))
    print(r.text)


parser_add = subparsers.add_parser('add',
                                   aliases=['a'],
                                   help='add items to selido')
parser_add.add_argument('book')

parser_get = subparsers.add_parser('get',
                                   aliases=['g'],
                                   help='get items from selido')
parser_get.add_argument('object')
parser_get.add_argument('-n', '--name', help='Name of the object to get')
parser_get.add_argument('-l',
                        '--label',
                        help='Get all objects with a certain label')
parser_get.set_defaults(func=get)

parser_tag = subparsers.add_parser('tag', aliases=['t'], help='tag items')

parser_delete = subparsers.add_parser('delete',
                                      aliases=['d', 'del'],
                                      help='delete items from selido')

parser_conf = subparsers.add_parser('configure',
                                    aliases=['c', 'conf'],
                                    help='Configure selido')
parser_conf_sub = parser_conf.add_subparsers()
parser_conf_settings = parser_conf_sub.add_parser(
    'endpoint', aliases=['e', 'end'], help='Which endpoint to connect to')
parser_conf_settings.add_argument('URI', help='The URI to use as endpoint')
parser_conf_settings.set_defaults(func=set_endpoint)

parser_init = subparsers.add_parser('init', help='Initial config of selido')
parser_init.set_defaults(func=init)

args = parser.parse_args()

args.func(args)

# URI = args.URI

# r = requests.post()

# print(URI)