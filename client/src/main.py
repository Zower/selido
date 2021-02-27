import requests
import argparse

parser = argparse.ArgumentParser(
    prog = 'selido',
    description = 'Client to interact with selido server'
    )

subparsers = parser.add_subparsers()
parser_add = subparsers.add_parser('add', aliases = ['a'], help = 'add items to selido')
parser_add.add_argument('book')
parser_get = subparsers.add_parser('get', aliases = ['g'], help = 'get items from selido')
parser_tag = subparsers.add_parser('tag', aliases = ['t'], help = 'tag items')
parser_delete = subparsers.add_parser('delete', aliases = ['d', 'del'], help = 'delete items from selido')

args = parser.parse_args()

print(args)