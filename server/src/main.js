'use strict'
const { ArgumentParser } = require('argparse')
const log = require('./logger/log.js')
const SelidoServer = require('./selido/server.js')

process.on('uncaughtException', err => {
  error(err)
  process.exit(1)
});

const parser = new ArgumentParser({
  prog: 'Selido server',
  description: 'Holds information about various objects, with tagging-based search'
})

parser.add_argument('-p', '--port', { help: 'Which port to run the API on', default: '3912' })
parser.add_argument('-P', '--auth-port', { help: "Which port to run the Auth server on", default: '3913' })
parser.add_argument('-d', '--db-host', { help: 'Where to connect to the database', default: 'mongo' })
parser.add_argument('-v', '--verbose', { help: 'Print all info messages', action: 'store_true' })
parser.add_argument('-q', '--quiet', { help: 'Suppress all regular messages', action: 'store_true' })
parser.add_argument('--debug', { help: 'Print debug messages', action: 'store_true' })
parser.add_argument('-t', '--auth-timeout', { help: 'How long to keep code verifications open, in seconds', default: 180 })
parser.add_argument('--no-authserver', { help: 'Dont launch the authentication server for new connections, auth is still enabled.', action: 'store_true' })
parser.add_argument('--no-dbauth', { help: 'Dont try to provide a username/password to mongo', action: 'store_true' })

var args = parser.parse_args()

main(args)

async function main(args) {
  info('Starting selido server..')
  let server = new SelidoServer(args.port, args.db_host, {
    verbose: args.verbose,
    quiet: args.quiet,
    debug: args.debug,
    authserver: !args.no_authserver,
    use_dbauth: !args.no_dbauth
  })

  server.start()

}

function error(err) {
  if (!args.quiet) {
    if (!args.debug) {
      log.error(err.message)
    }
    else {
      log.error(err.stack)
    }
  }
}

function verbose(message) {
  if (args.verbose && !args.quiet) {
    log.info(message)
  }
}

function warn(message) {
  if (!args.quiet) {
    log.warn(message)
  }
}

function info(message) {
  if (!args.quiet) {
    log.info(message)
  }
}