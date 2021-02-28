'use strict';
const { ArgumentParser } = require('argparse');
const log = require('./logger/log.js');
const SelidoServer = require('./selido/server.js');

const parser = new ArgumentParser({
  description: 'Selido server'
});

parser.add_argument('-p', '--port', { help: 'Which port to run the API on', default: '3912' })
parser.add_argument('-d', '--uri', { help: 'Where to connect to the database', default: 'mongo' })
parser.add_argument('-v', '--verbose', { help: 'Print all info messages', action: 'store_true' })

var args = parser.parse_args()

main(args)

async function main(args) {
  log.info('Attempting to connect to db..')
  var server = new SelidoServer(args);
  server.start().then(message => {
    verbose(message)
  }).catch(err => {
    log.error(err)
    process.exit(1);
  })
}

function verbose(message) {
  if (args.verbose) {
    log.info(message)
  }
}