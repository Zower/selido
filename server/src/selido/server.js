'use strict';
const log = require('../logger/log.js');
const express = require('express');
const https = require('https');
var bodyParser = require('body-parser')
var jsonParser = bodyParser.json()

const SelidoDB = require('./db.js');
const SelidoAuth = require('./auth.js');
const SelidoResponse = require('./response.js');

var app = express();
app.use(jsonParser)

module.exports = class SelidoServer {
    constructor(dburl, port, verbose, quiet, no_authserver, auth_code_timeout, no_dbauth) {
        this.db = new SelidoDB(dburl, no_dbauth)
        this.port = port
        this.verbosity = verbose
        this.quiet = quiet
        this.auth = new SelidoAuth(parseInt(port, 10) + 1, verbose, quiet, auth_code_timeout)
        this.no_authserver = no_authserver
    }

    start() {
        var serv = this
        process.on('uncaughtException', function (err) {
            if (err.code === 'EADDRINUSE') {
                serv.error('Port already in use, perhaps another instance is running? Try another port with -p PORT. Error: ' + err);
                process.exit(1)
            }
            else {
                serv.error(err.toString())
                process.exit(1)
            }
        });
        return new Promise((resolve, reject) => {
            var options = {}
            this.auth.getOrGenerateMainOptions()
                .then(result => {
                    options = result
                    this.verbose('Attempting to connect to db..')
                    this.connectToDB()
                        .then(message => {
                            this.info(message)

                            this.setHandlers()

                            var httpsServer = https.createServer(options, app)

                            httpsServer.listen(this.port, "0.0.0.0", () => {
                                resolve('Selido server listening on port ' + this.port)
                            });

                            if (!this.no_authserver) {
                                this.auth.start()
                            }
                            else {
                                this.verbose("--no-authserver used, not starting auth server")
                            }
                        })
                        .catch(err => {
                            reject(err)
                        })
                })
                .catch(err => {
                    serv.error(err)
                    process.exit(1)
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

        // Get some resources from db with id
        app.get('/get/:id', function (req, res) {
            serv.db.get(req.params.id)
                .then(response => {
                    serv.verbose(response)
                    res.status(response.code).send(response)
                })
                .catch(err => {
                    serv.error(err)
                    res.status(500).send(err)
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
                    res.status(500).send(err)
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
                res.status(500).send(err)
            })
        });

        // Delete a resource
        app.delete('/resource/:id', function (req, res) {
            serv.db.delete(req.params.id).then(response => {
                serv.verbose(response)
                res.status(response.code).send(response)
            }).catch(err => {
                serv.error(err)
                res.status(500).send(err)
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
                res.status(500).send(err)
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
                res.status(500).send(err)
            })
        })

        this.setAuxHandlers()

    }

    setAuxHandlers() {
        var serv = this

        app.get('/authenticate/', function (req, res) {
            const action = 'getAuthVerify'
            let codes = serv.auth.checkOpenCodes()
            if (codes) {
                var response = new SelidoResponse(action, 'success', 'Got open authentication codes', 200, codes)
            }
            else {
                var response = new SelidoResponse(action, 'failed', "No authentication codes currently active", 404)
            }
            res.status(response.code).send(response)
        })

        app.post('/authenticate/', function (req, res) {
            const action = 'authVerify'
            let codes = serv.auth.checkOpenCodes()
            var resp = res
            if (codes) {
                let verify = req.body.code
                serv.auth.verifyCode(verify).then(ver => {
                    if (ver) {
                        serv.verbose('Verified new connection: ')
                        serv.verbose(ver)
                        var response = new SelidoResponse(action, 'success', 'Verified code', 200)
                        resp.status(response.code).send(response)

                    }
                    else {
                        var response = new SelidoResponse(action, 'failed', 'No code matches', 400)
                        resp.status(response.code).send(response)
                    }
                }).catch(error => {
                    serv.error(error)
                    var response = new SelidoResponse(action, 'failed', "Failed to verify", 500, error)
                    resp.status(response.code).send(response)
                })
            }
            else {
                var response = new SelidoResponse(action, 'failed', "No authentication codes currently active", 404)
                res.status(response.code).send(response)
            }

        })

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