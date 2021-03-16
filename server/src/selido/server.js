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
                else {
                    this.error(err)
                    reject('Unexpected problem. Error:\n' + err);
                }
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

        // Temporary fix
        app.get('/test', function (req, res) {
            serv.db.printAll()
        })

        // Get some resources from db with id
        app.get('/get/:id', function (req, res) {
            serv.db.get(req.params.id)
                .then(response => {
                    serv.verbose(response)
                    res.status(response.code).send(response)
                })
                .catch(err => {
                    serv.error(err)
                    res.status(err.code).send(err)
                })
        })

        // Search for tags
        app.post('/find/', function (req, res) {
            let tags = req.body.tags
            serv.db.find(tags, req.body.and_search, req.body.all)
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
        app.post('/resource/', function (req, res) {
            let tags = req.body.tags
            serv.db.add(tags).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(err.code).send(err)
            })
        });

        // Delete a resource
        app.delete('/resource/:id', function (req, res) {
            serv.db.delete(req.params.id).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(err.code).send(err)
            })
        })

        // Tag resource
        app.post('/tag/:id', function (req, res) {
            let tags = req.body.tags
            serv.db.addTags(req.params.id, tags).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(err.code).send(err)
            })
        })

        // Delete tag from resource
        app.delete('/tag/:id', function (req, res) {
            let tags = req.body.tags
            serv.db.delTags(req.params.id, tags).then(response => {
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