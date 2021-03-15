'use strict';
const log = require('../logger/log.js');
const express = require('express');
var bodyParser = require('body-parser')
var jsonParser = bodyParser.json()

const SelidoDB = require('./db.js');

var app = express();
app.use(jsonParser)

module.exports = class SelidoServer {
    constructor(args) {
        this.db = new SelidoDB(args.dburl)
        this.port = args.port
        this.verbosity = args.verbose
        this.quiet = args.quiet
    }

    start() {
        return new Promise((resolve, reject) => {
            process.on('uncaughtException', function (err) {
                if (err.code === 'EADDRINUSE')
                    reject('Port already in use, perhaps another instance is running? Try another port with -p PORT');
                else
                    reject('Unexpected problem. Error:\n' + err);
            });

            this.verbose('Attempting to connect to db..')
            this.connectToDB()
                .then(message => {


                    this.info(message)

                    this.setHandlers()

                    app.listen(this.port, () => {
                        resolve('Selido server listening on port ' + this.port)
                    });
                })
                .catch(err => {
                    reject(err)
                })

        })
    }

    connectToDB() {
        return new Promise((resolve, reject) => {
            this.db.init()
                .then(message => {
                    resolve(message)
                })
                .catch(err => {
                    reject(err)
                })
        })
    }

    setHandlers() {
        var serv = this

        // Get some resources from db
        app.get('/get/:resource', function (req, res) {
            let tags = req.body
            serv.db.get(req.params.resource, tags)
                .then(response => {
                    serv.verbose(response)
                    res.status(response.code).send(response)
                })
                .catch(err => {
                    serv.error(err)
                    res.status(err.code).send(err)
                })
        })

        // Add resources to db
        app.post('/add/:resource', function (req, res) {
            let tags = req.body
            serv.db.add(req.params.resource, tags).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(err.code).send(err)
            })
        });

        // Tag resource
        app.post('/tag/:resource', function (req, res) {
            let tags = req.body
            serv.db.addTags(req.params.resource, tags).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(err.code).send(err)
            })
        })

        // Delete tag from resource
        app.delete('/tag/:resource', function (req, res) {
            let tags = req.body
            serv.db.delTags(req.params.resource, tags).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(err.code).send(err)
            })
        })
    }

    tag(params) {
        return this.db.add(params.resource)
    }

    error(message) {
        if (!this.quiet) {
            log.error(JSON.stringify(message))
        }
    }

    verbose(message) {
        if (this.verbosity && !this.quiet) {
            log.info(JSON.stringify(message))
        }
    }

    info(message) {
        if (!this.quiet) {
            log.info(JSON.stringify(message))
        }
    }
}