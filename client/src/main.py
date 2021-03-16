import argparse
import commands

parser = argparse.ArgumentParser(
    prog='Selido client',
    description='Client to interact with selido server',
    usage='selido [flags] [options]')

subparsers = parser.add_subparsers(dest='Initial command')
subparsers.required = True

#############################################
# Online commands

##################
# Add command
parser_add = subparsers.add_parser('add',
                                   aliases=['a'],
                                   help='Add a resource to selido')
parser_add.add_argument('tags', help='The tags to add')
parser_add.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_add.set_defaults(func=commands.add)


##################
# Get command
parser_get = subparsers.add_parser('get',
                                   aliases=['g'],
                                   help='Get one resource from Selido server by id')
parser_get.add_argument('id', help='The id to get')
parser_get.add_argument(
    '-u', '--url', help="URL:port to connect to")

parser_get.set_defaults(func=commands.get)

##################
# Find command
parser_find = subparsers.add_parser('find',
                                    aliases=['f'],
                                    help='Find a resource in selido based on tags')
parser_find.add_argument('tags', help='The tags to find', nargs='?')
parser_find.add_argument(
    '-a', '--all', help='Find all resources', action='store_true')
parser_find.add_argument('-o', '--or-search',
                         help='Only one tag has to match', action='store_true')
parser_find.add_argument(
    '-u', '--url', help="URL:port to connect to")

parser_find.set_defaults(func=commands.find)

##################
# Tag command
parser_tag = subparsers.add_parser(
    'tag', aliases=['t'], help='Modify tags on resources')
parser_tag_sub = parser_tag.add_subparsers(dest='action')
parser_tag_sub.required = True

parser_tag_add = parser_tag_sub.add_parser(
    'add', aliases=['a'], help='Add tags to resource')
parser_tag_add.add_argument('id', help='The id to tag')
parser_tag_add.add_argument('tags', help='The tags to apply')
parser_tag_add.add_argument(
    '-u', '--url', help="URL:port to connect to")

parser_tag_add.set_defaults(func=commands.add_tags)


parser_tag_del = parser_tag_sub.add_parser(
    'delete', aliases=['d', 'del'], help='Delete tags from resource')
parser_tag_del.add_argument(
    'id', help='The id to delete tags from')
parser_tag_del.add_argument('tags', help='The tags to delete')
parser_tag_del.add_argument(
    '-u', '--url', help="URL:port to connect to")

parser_tag_del.set_defaults(func=commands.del_tags)


##################
# Delete command
parser_delete = subparsers.add_parser('delete',
                                      aliases=['d', 'del'],
                                      help='delete resources from selido')


#############################################
# Config commands

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

args.func(args)
