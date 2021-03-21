'use strict'

const fs = require('fs')

const express = require('express');
const https = require('https');
var bodyParser = require('body-parser')
var jsonParser = bodyParser.json()

const log = require('../logger/log.js');
const SelidoResponse = require('./response.js')
const SelidoCert = require('./cert.js')

const generator = require('niceware')

var app = express()
app.use(jsonParser)

module.exports = class SelidoAuth {
    constructor(port, verbose, quiet, code_timeout) {
        this.cert = new SelidoCert(verbose)
        this.port = port
        this.verbosity = verbose
        this.quiet = quiet
        this.code_timeout = code_timeout

        this.options = {}
        this.open_codes = []
        this.unclaimed_codes = []
    }

    getOrGenerateMainOptions() {
        return this.cert.getOrGenerateMainOptions()
    }

    checkOpenCodes() {
        if (this.open_codes.length > 0) {
            return this.open_codes
        }
        else {
            return false
        }
    }

    start() {
        this.options = this.cert.getAuthOptions()

        this.setHandlers()

        var httpsServer = https.createServer(this.options, app)
        httpsServer.listen(this.port, "0.0.0.0", () => {
            this.verbose("Selido auth listening on port " + this.port)
        })
    }


    setHandlers() {
        var serv = this

        app.get('/authenticate/ca/', function (req, res) {
            let ca = fs.readFileSync(process.cwd() + '/certs/' + 'ca.crt', { encoding: 'utf-8' })
            // When reading on windows, file will include \r\n
            // As far as I can tell, .crt file cannot contain \ as a character, so replacing is okay
            ca = ca.replace(/\r/g, "");
            res.status(200).send(new SelidoResponse('getCA', 'success', 'Got CA file', 200, ca))
        })

        app.get('/authenticate/:name', async function (req, res) {
            const action = 'authRequest'
            const pass = generator.generatePassphrase(6)
            //TODO: Add timeout on challenges
            let code = { name: req.params.name, code: pass }
            serv.open_codes.push(code)
            await serv.cert.genClientKey(req.params.name)
            await serv.cert.genClientCSR(req.params.name)
            let cli_name_path = process.cwd() + '/certs/' + req.params.name
            let key = fs.readFileSync(cli_name_path + '.key')
            let auth = { name: req.params.name, code: pass, key: key.toString() }

            res.status(200).send(new SelidoResponse(action, 'success', 'Got authentication code and unsigned key', 200, auth))

            setTimeout(serv.deleteCode, serv.code_timeout, code)

        })

        // TODO: Return different code if timed out
        app.post('/authenticated/', function (req, res) {
            const action = 'authConfirm'
            let check_auth = req.body.code
            serv.existsOpenCode(check_auth).then(ex => {
                if (ex) {
                    serv.isVerified(check_auth).then(ver => {
                        if (ver) {
                            let cli_name_path = process.cwd() + '/certs/' + check_auth.name
                            let cert = fs.readFileSync(cli_name_path + '.crt')
                            res.status(200).send(new SelidoResponse(action, 'success', 'Got signed certificate', 200, cert.toString()))
                            serv.cert.deleteClientCerts(check_auth.name)
                        }
                        else {
                            res.status(401).send(new SelidoResponse(action, 'failed', 'This code has not been verified by an authenticated client yet.', 401))
                        }
                    })
                }
                else {
                    res.status(403).send(new SelidoResponse(action, 'failed', 'This code doesnt exist, or has timed out', 403))
                }
            })
        })
    }

    // This should *never* be called from a non-authorized request
    async verifyCode(code) {
        var serv = this
        if (this.open_codes.length > 0) {
            for (var i = this.open_codes.length - 1; i >= 0; i--) {
                let open_code = this.open_codes[i]
                if (
                    code.name == open_code.name && code.code.length == open_code.code.length
                    && open_code.code.every(function (u, i) {
                        return u == code.code[i]
                    })
                ) {
                    await serv.cert.genClientCert(code.name)
                    serv.unclaimed_codes.push(serv.open_codes[i])
                    serv.open_codes.splice(i, 1)
                    return code
                }
                else {
                    if (i == 0) {
                        return false
                    }
                }
            }
        }
        else {
            return false
        }
    }

    deleteCode(code) {
        if (this.open_codes.length > 0) {
            for (var i = this.open_codes.length - 1; i >= 0; i--) {
                let open_code = this.open_codes[i]
                if (
                    code.name == open_code.name && code.code.length == open_code.code.length
                    && open_code.code.every(function (u, i) {
                        return u == code.code[i]
                    })
                ) {
                    this.open_codes.splice(i, 1)
                }
            }
        }
    }

    async existsOpenCode(code) {
        if (this.open_codes.length > 0) {
            for (var i = this.open_codes.length - 1; i >= 0; i--) {
                let open_code = this.open_codes[i]
                if (
                    code.name == open_code.name && code.code.length == open_code.code.length
                    && open_code.code.every(function (u, i) {
                        return u == code.code[i]
                    })
                ) {
                    return true
                }
                else {
                    if (i == 0) {
                        return false
                    }
                }
            }
        }
        else {
            return false
        }
    }

    async isVerified(code) {
        if (this.unclaimed_codes.length > 0) {
            for (var i = this.unclaimed_codes.length - 1; i >= 0; i--) {
                let unclaimed_code = this.unclaimed_codes[i]
                if (
                    code.name == unclaimed_code.name && code.code.length == unclaimed_code.code.length
                    && unclaimed_code.code.every(function (u, i) {
                        return u == code.code[i]
                    })
                ) {
                    this.unclaimed_codes.splice(i, 1)
                    return true
                }
                else {
                    if (i == 0) {
                        return false
                    }
                }
            }
        }
        else {
            return false
        }
    }

    error(message) {
        if (!this.quiet) {
            log.error(message.toString())
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