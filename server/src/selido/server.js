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
    constructor(port, dbhost, options = {}) {
        this.port = port
        this.db = new SelidoDB(dbhost, {
            use_password: options.use_dbauth,
            debug: options.debug,
            quiet: options.quiet,
            verbose: options.verbose,
        })
        this.verbosity = options.verbose || false
        this.quiet = options.quiet || false
        this.debug = options.debug || false
        this.auth = new SelidoAuth(options.auth_port || 3913, {
            verbose: options.verbose,
            quiet: options.quiet,
            debug: options.debug,
            code_timeout: options.code_timeout
        })
        this.start_authserver = options.authserver || true
    }

    async start() {
        try {
            let options = await this.auth.getOrGenerateMainOptions()
            this.verbose("Attempting to connect to db..")
            let message = await this.connectToDB()
            this.info(message)

            this.setHandlers()

            var httpsServer = https.createServer(options, app)

            httpsServer.listen(this.port, "0.0.0.0", () => {
                this.verbose('Selido server listening on port ' + this.port)
            });

            if (this.start_authserver) {
                this.auth.start()
            }
            else {
                this.verbose("--no-authserver used, not starting auth server")
            }
        }
        catch (e) {
            this.error(e)
            process.exit(1)
        }
    }

    async connectToDB() {
        return this.db.init()
    }

    setHandlers() {
        // Get some resources from db with id
        app.get('/get/:id', async (req, res) => {
            let answer = await this.db.get(req.params.id)

            this.verbose_print_answer(answer)
            res.status(answer.code).send(answer)
        })

        // Search for tags
        app.post('/find/', async (req, res) => {
            let tags = req.body.tags
            let answer = await this.db.find(tags, req.body.and_search, req.body.all)

            this.verbose_print_answer(answer)
            res.status(answer.code).send(answer)
        })

        // Add resources to db
        app.post('/resource/', async (req, res) => {
            let tags = req.body.tags
            let answer = await this.db.add(tags)

            this.verbose_print_answer(answer)
            res.status(answer.code).send(answer)
        });

        // Delete a resource
        app.delete('/resource/:id', async (req, res) => {
            let answer = await this.db.delete(req.params.id)

            this.verbose_print_answer(answer)
            res.status(answer.code).send(answer)
        })

        // Tag resource
        app.post('/tag/:id', async (req, res) => {
            let tags = req.body.tags
            let answer = await this.db.addTags(req.params.id, tags)

            this.verbose_print_answer(answer)
            res.status(answer.code).send(answer)
        })

        // Delete tag from resource
        app.delete('/tag/:id', async (req, res) => {
            let tags = req.body.tags
            let answer = await this.db.delTags(req.params.id, tags)

            this.verbose_print_answer(answer)
            res.status(answer.code).send(answer)
        })

        this.setAuxHandlers()
    }

    setAuxHandlers() {

        app.get('/authenticate/', async (req, res) => {
            const action = 'getAuthVerify'
            let codes = this.auth.getOpenCodes()
            if (codes) {
                var response = new SelidoResponse(action, 'success', 'Got open authentication codes', 200, codes)
            }
            else {
                var response = new SelidoResponse(action, 'failed', "No authentication codes currently active", 404)
            }
            res.status(response.code).send(response)
        })

        app.post('/authenticate/', async (req, res) => {
            const action = 'authVerify'
            let codes = this.auth.getOpenCodes()
            var resp = res
            if (codes) {
                let verify = req.body.code
                this.auth.verifyCode(verify).then(ver => {
                    if (ver) {
                        this.verbose('Verified new connection: ')
                        this.verbose(JSON.stringify(ver))
                        var response = new SelidoResponse(action, 'success', 'Verified code', 200)
                        resp.status(response.code).send(response)

                    }
                    else {
                        var response = new SelidoResponse(action, 'failed', 'No code matches', 400)
                        resp.status(response.code).send(response)
                    }
                }).catch(error => {
                    this.error(error)
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

    verbose_print_answer(answer) {
        this.verbose("Action " + answer.action + " gave results: ")
        let string_objects = ''
        if (typeof answer.objects !== 'undefined') {
            answer.objects.forEach(object => {
                string_objects += JSON.stringify(object)
            })
            this.verbose(string_objects)
        }
    }

    error(err) {
        if (!this.quiet) {
            if (!this.debug) {
                log.error(err.message)
            }
            else {
                log.error(err.stack)
            }
        }
    }

    verbose(message) {
        if (this.verbose && !this.quiet) {
            log.info(message)
        }
    }

    warn(message) {
        if (!this.quiet) {
            log.warn(message)
        }
    }

    info(message) {
        if (!this.quiet) {
            log.info(message)
        }
    }
}