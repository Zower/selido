import argparse

from selido import config
from selido.core import auth, client
from selido.parsing import get_default_ca, get_default_certs, get_default_url

config_parser = config.SelidoConfig(config.get_config())

default_ca = get_default_ca()
default_certs = get_default_certs()
default_url = get_default_url()

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
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_add.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_add.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)


parser_add.set_defaults(func=client.add)

#################
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
    '-u', '--url', help="URL:port to connect to", default=get_default_url(True))


parser_authenticate_request.set_defaults(func=auth.request)


parser_authenticate_verify = parser_authenticate_sub.add_parser(
    'verify', aliases=['v'], help='Verify an authentication code (Requires previous authentication)')
parser_authenticate_verify.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_authenticate_verify.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_authenticate_verify.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_authenticate_verify.set_defaults(func=auth.verify)


parser_authenticate_hash = parser_authenticate_sub.add_parser(
    'hash', aliases=['h'], help='Get the hash of current ca file')

parser_authenticate_hash.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_authenticate_hash.set_defaults(func=auth.hash)

##################
# Delete command
parser_delete = subparsers.add_parser('delete',
                                      aliases=['d', 'del'],
                                      help='delete resources from selido')
parser_delete.add_argument(
    'searchterm', help='The ids to delete, in comma-separated format. Also accepts previously cached indices.')
parser_delete.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_delete.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_delete.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_delete.set_defaults(func=client.delete)

##################
# Get command
parser_get = subparsers.add_parser('get',
                                   aliases=['g'],
                                   help='Get one resource from Selido server by id')
parser_get.add_argument(
    'searchterm', help='The ids to get, in comma-separated format. Also accepts previously cached indices.')
parser_get.add_argument(
    '-N', '--no-columns', help="Dont print top level columns in output", action='store_true'
)
parser_get.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_get.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_get.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_get.set_defaults(func=client.get)

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
    '-i', '--indent', help="# Indents between tag columns", default=15, type=int
)
parser_find.add_argument(
    '-s', '--sort', help="Sort the tags of the resources based on keys", action='store_true')
parser_find.add_argument(
    '-N', '--no-columns', help="Dont print top level columns in output", action='store_true'
)
parser_find.add_argument(
    '--count', help="Count the number of instances returned", action='store_true'
)
parser_find.add_argument(
    '--mcount', help="Count the number of instances returned, nothing else is printed", action='store_true'
)
parser_find.add_argument(
    '-w', '--with-id', help="Print IDs of the resources", action='store_true')
parser_find.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_find.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_find.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_find.set_defaults(func=client.find)

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
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_tag_add.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_tag_add.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_tag_add.set_defaults(func=client.add_tags)


parser_tag_del = parser_tag_sub.add_parser(
    'delete', aliases=['d', 'del'], help='Delete tags from resource')
parser_tag_del.add_argument(
    'searchterm', help='The ids to delete the tags from, in comma-separated format. Also accepts previously cached indices.')
parser_tag_del.add_argument('tags', help='The tags to delete')
parser_tag_del.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_tag_del.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_tag_del.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_tag_del.set_defaults(func=client.del_tags)

parser_tag_copy = parser_tag_sub.add_parser(
    'copy', aliases=['c'], help='Copy tags from one set of resources to another')
parser_tag_copy.add_argument(
    'from_ids', help='The ids to copy tags from, in comma-separated format. Also accepts previously cached indices.')
parser_tag_copy.add_argument(
    'to_ids', help='The ids to copy tags to, in comma-separated format. Also accepts previously cached indices.')
parser_tag_copy.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_tag_copy.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_tag_copy.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_tag_copy.set_defaults(func=client.copy_tags)

##################
# Open command
parser_open = subparsers.add_parser(
    'open', aliases=['o'], help="Open a resource with a 'path:<PATH>' tag in the default application.")
parser_open.add_argument(
    'searchterm', help='The id to open. Also accepts previously cached indices.'
)
parser_open.add_argument(
    '-u', '--url', help="URL:port to connect to", default=default_url)
parser_open.add_argument(
    '-U', '--user-certs', help="Key and certificate to use for authentication, in the format: full cert path,full key path", default=default_certs)
parser_open.add_argument(
    '-C', '--ca-file', help="Full path of the CA.crt file to use", default=default_ca
)

parser_open.set_defaults(func=client.open_file)


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
parser_conf_endpoint.set_defaults(func=config_parser.endpoint)

parser_conf_username = parser_conf_sub.add_parser('username', aliases=[
    'u', 'un', 'user'], help='Which pre-fix filename the client certs have in /.selido/certs')
parser_conf_username.add_argument(
    'username', help='The username that was specified when creating this client key, if filename is ~/.selido/certs/foo.crt, this setting should be \'foo\'')
parser_conf_username.set_defaults(func=config_parser.username)

args = parser.parse_args()

print(args)

args.func(args)
