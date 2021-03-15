'use strict'
const { ArgumentParser } = require('argparse')
const log = require('./logger/log.js')
const SelidoServer = require('./selido/server.js')

const parser = new ArgumentParser({
  prog: 'Selido server',
  description: 'Holds information about various objects, with tagging-based search'
})

parser.add_argument('-p', '--port', { help: 'Which port to run the API on', default: '3912' })
parser.add_argument('-d', '--dburl', { help: 'Where to connect to the database', default: 'mongo' })
parser.add_argument('-v', '--verbose', { help: 'Print all info messages', action: 'store_true' })
parser.add_argument('-q', '--quiet', { help: 'Suppress all messages', action: 'store_true' })

var args = parser.parse_args()

main(args)

async function main(args) {
  info('Starting selido server..')
  var server = new SelidoServer(args)
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