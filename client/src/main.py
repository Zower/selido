import argparse
import commands

parser = argparse.ArgumentParser(
    prog='Selido client',
    description='Client to interact with selido server',
    usage='selido [flags] [options]')

subparsers = parser.add_subparsers(dest='Initial command')
subparsers.required = True


parser_add = subparsers.add_parser('add',
                                   aliases=['a'],
                                   help='Add a resource to selido')
parser_add.add_argument('resource')
parser_add.add_argument('-t', '--tags', help='Add tags alongside resource')
parser_add.set_defaults(func=commands.add)


parser_get = subparsers.add_parser('get',
                                   aliases=['g'],
                                   help='Get resources from Selido server')
parser_get.add_argument('resource')
parser_get.add_argument('-n', '--name', help='Name of the object to get')
parser_get.add_argument(
    '-t',
    '--tags',
    help='Filter on one or several tags')
parser_get.set_defaults(func=commands.get)


parser_tag = subparsers.add_parser(
    'tag', aliases=['t'], help='Modify tags on resources')
parser_tag_sub = parser_tag.add_subparsers(dest='action')
parser_tag_sub.required = True
parser_tag_add = parser_tag_sub.add_parser(
    'add', aliases=['a'], help='Add tags to resource')
parser_tag_add.add_argument('resource', help='The resource to tag')
parser_tag_add.add_argument('tags', help='The tags to apply')
parser_tag_add.set_defaults(func=commands.add_tags)

parser_tag_del = parser_tag_sub.add_parser(
    'delete', aliases=['d', 'del'], help='Delete tags from resource')
parser_tag_del.add_argument(
    'resource', help='The resource to delete tags from')
parser_tag_del.add_argument('tags', help='The tags to delete')
parser_tag_del.set_defaults(func=commands.del_tags)


parser_delete = subparsers.add_parser('delete',
                                      aliases=['d', 'del'],
                                      help='delete resources from selido')


parser_conf = subparsers.add_parser('configure',
                                    aliases=['c', 'conf'],
                                    help='Configure selido')
parser_conf_sub = parser_conf.add_subparsers(dest='action')
parser_conf_sub.required = True
parser_conf_action = parser_conf_sub.add_parser(
    'endpoint', aliases=['e', 'end'], help='Which endpoint to connect to')
parser_conf_action.add_argument('URL', help='The URL to use as endpoint')
parser_conf_action.set_defaults(func=commands.set_endpoint)


parser_init = subparsers.add_parser('init', help='Initial config of selido')
parser_init.set_defaults(func=commands.init)

args = parser.parse_args()

config = commands.get_config()

if not hasattr(args, 'URL'):
    args.URL = 'http://' + config.get('Endpoint.URL') + ':' + config.get(
        'Endpoint.Port')

args.func(args)
