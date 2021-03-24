const winston = require('winston')

winston.addColors({
  error: 'red',
  warn: 'yellow',
  info: 'cyan',
  debug: 'green'
})

log = winston.createLogger({
  transports: [
    new winston.transports.File({
      filename: 'error.log', level: 'error', format: winston.format.combine(
        winston.format.errors({ stack: true }),
        winston.format.timestamp({ format: 'YYYY-MM-DD hh:mm:ss' }),
        winston.format.json()
      )
    }),
    new winston.transports.Console({
      level: 'info',
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
      prettyPrint: true
    })
  ],
})

module.exports = log