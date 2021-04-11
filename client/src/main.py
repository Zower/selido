import argparse
import commands
import auth
import config
import sys
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
parser_add.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_add.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_add.set_defaults(func=commands.add)

##################
# Authenticate command

parser_authenticate = subparsers.add_parser(
    'authenticate', aliases=['au', 'auth'], help='Request or verify authentication')
parser_authenticate_sub = parser_authenticate.add_subparsers(dest='action')
parser_authenticate_sub.required = True

parser_authenticate_request = parser_authenticate_sub.add_parser(
    'request', aliases=['r', 'req'], help='Request an authentication code (Does not require authentication)')
parser_authenticate_request.add_argument(
    'name', help="The username of this client")
parser_authenticate_request.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_authenticate_request.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_authenticate_request.set_defaults(func=auth.request)


parser_authenticate_verify = parser_authenticate_sub.add_parser(
    'verify', aliases=['v'], help='Verify an authentication code (Requires previous authentication)')
parser_authenticate_verify.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_authenticate_verify.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_authenticate_verify.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_authenticate_verify.set_defaults(func=auth.verify)


parser_authenticate_hash = parser_authenticate_sub.add_parser(
    'hash', aliases=['h'], help='Get the hash of current ca file')

parser_authenticate_hash.add_argument(
    '-C', '--ca-file', help='Ca file to use from ~/.selido/certs')

parser_authenticate_hash.set_defaults(func=auth.hash)

##################
# Delete command
parser_delete = subparsers.add_parser('delete',
                                      aliases=['d', 'del'],
                                      help='delete resources from selido')
parser_delete.add_argument(
    'searchterm', help='The ids to delete, in comma-separated format. Also accepts previously cached indices.')
parser_delete.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_delete.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_delete.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_delete.set_defaults(func=commands.delete)

##################
# Get command
parser_get = subparsers.add_parser('get',
                                   aliases=['g'],
                                   help='Get one resource from Selido server by id')
parser_get.add_argument(
    'searchterm', help='The ids to get, in comma-separated format. Also accepts previously cached indices.')
parser_get.add_argument(
    '-N', '--no-id', help="Dont include the IDs of the resource in output", action='store_true'
)
parser_get.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_get.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_get.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_get.set_defaults(func=commands.get)

##################
# Find command
parser_find = subparsers.add_parser('find',
                                    aliases=['f'],
                                    help='Find resources in selido')
parser_find.add_argument('searchterm', help='Comma separated keys to find, e.g. "selido find foo,bar" will look for anything with they keys foo and bar. Putting \'+\' in front of a tag indicates to search for a key:value, e.g. "+foo:true,bar,+baz:false".', nargs='?')
parser_find.add_argument(
    '-a', '--all', help='Find all resources', action='store_true')
parser_find.add_argument('-o', '--or-search',
                         help='Only one tag has to match', action='store_true')
parser_find.add_argument('-A', '--auto-exclude',
                         help="Exclude the search phrase keys from the printed output", action='store_true')
parser_find.add_argument(
    '-c', '--columns', help='Comma-separated keys to give a separate column')
parser_find.add_argument(
    '-e', '--exclude', help="Comma-separated keys from the returned tag search to exclude in the printed output, e.g. if resource is 'foo:bar, testing', then 'find foo:bar -e foo:bar' would return 'testing'")
parser_find.add_argument(
    '-s', '--sort', help="Sort the tags of the resources based on keys", action='store_true')
parser_find.add_argument(
    '-N', '--no-id', help="Dont include the IDs of the resource in output", action='store_true'
)
parser_find.add_argument(
    '--count', help="Count the number of instances returned, instead of outputting them", action='store_true'
)
parser_find.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_find.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_find.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)
parser_find.add_argument(
    '-i', '--indent', help="# Indents between tag columns"
)

parser_find.set_defaults(func=commands.find)

##################
# Tag command
parser_tag = subparsers.add_parser(
    'tag', aliases=['t'], help='Modify tags on resources')
parser_tag_sub = parser_tag.add_subparsers(dest='action')
parser_tag_sub.required = True

parser_tag_add = parser_tag_sub.add_parser(
    'add', aliases=['a'], help='Add tags to resource')
parser_tag_add.add_argument(
    'searchterm', help='The ids to add tags to, in comma-separated format. Also accepts previously cached indices.')
parser_tag_add.add_argument('tags', help='The tags to apply')
parser_tag_add.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_tag_add.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_tag_add.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_tag_add.set_defaults(func=commands.add_tags)


parser_tag_del = parser_tag_sub.add_parser(
    'delete', aliases=['d', 'del'], help='Delete tags from resource')
parser_tag_del.add_argument(
    'searchterm', help='The ids to delete the tags from, in comma-separated format. Also accepts previously cached indices.')
parser_tag_del.add_argument('tags', help='The tags to delete')
parser_tag_del.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_tag_del.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_tag_del.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_tag_del.set_defaults(func=commands.del_tags)

##################
# Open command
parser_open = subparsers.add_parser(
    'open', aliases=['o'], help="Open a resource with a 'path:<PATH>' tag in the default application.")
parser_open.add_argument(
    'searchterm', help='The id to open. Also accepts previously cached indices.'
)
parser_open.add_argument(
    '-u', '--url', help="URL:port to connect to")
parser_open.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path")
parser_open.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use"
)

parser_open.set_defaults(func=commands.open_file)


#############################################
# Config commands

parser_conf = subparsers.add_parser('configure',
                                    aliases=['c', 'conf'],
                                    help='Configure selido')
parser_conf_sub = parser_conf.add_subparsers(dest='action')
parser_conf_sub.required = True
parser_conf_endpoint = parser_conf_sub.add_parser(
    'endpoint', aliases=['e', 'end'], help='Which endpoint to connect to')
parser_conf_endpoint.add_argument(
    'url', help='The full URL to use as endpoint, e.g https://localhost:3912 or https://example.com:4023')
parser_conf_endpoint.set_defaults(func=config.endpoint)

parser_conf_username = parser_conf_sub.add_parser('username', aliases=[
    'u', 'un', 'user'], help='Which pre-fix filename the client certs have in /.selido/certs')
parser_conf_username.add_argument(
    'username', help='The username that was specified when creating this client key, if filename is ~/.selido/certs/foo.crt, this setting should be \'foo\'')
parser_conf_username.set_defaults(func=config.username)

parser_init = subparsers.add_parser('init', help='Initial config of selido')
parser_init.set_defaults(func=config.init)

args = parser.parse_args()

args.func(args)
