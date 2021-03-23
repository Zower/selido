'use strict'
const { ArgumentParser } = require('argparse')
const log = require('./logger/log.js')
const SelidoServer = require('./selido/server.js')

const parser = new ArgumentParser({
  prog: 'Selido server',
  description: 'Holds information about various objects, with tagging-based search'
})

parser.add_argument('-p', '--port', { help: 'Which port to run the API on', default: '3912' })
parser.add_argument('-d', '--db-url', { help: 'Where to connect to the database', default: 'mongo' })
parser.add_argument('-v', '--verbose', { help: 'Print all info messages', action: 'store_true' })
parser.add_argument('-q', '--quiet', { help: 'Suppress all regular messages', action: 'store_true' })
parser.add_argument('-t', '--auth-timeout', { help: 'How long to keep code verifications open, in seconds', default: 180 })
parser.add_argument('--no-authserver', { help: 'Dont launch the authentication server for new connections, auth is still enabled.', action: 'store_true' })
parser.add_argument('--no-dbauth', { help: 'Dont try to provide a username/password to mongo', action: 'store_true' })

console.log(process.cwd())


var args = parser.parse_args()

main(args)

async function main(args) {
  info('Starting selido server..')
  var server = new SelidoServer(args.db_url, args.port, args.verbose, args.quiet, args.no_authserver, args.auth_timeout * 1000, args.no_dbauth)
  server.start().then(message => {
    info(message)
  }).catch(err => {
    error(err)
    process.exit(1)
  })
}

function error(message) {
  if (!args.quiet) {
    log.error(JSON.stringify(message))
  }
}

function verbose(message) {
  if (args.verbose && !args.quiet) {
    log.info(JSON.stringify(message))
  }
}

function info(message) {
  if (!args.quiet) {
    log.info(JSON.stringify(message))
  }
}