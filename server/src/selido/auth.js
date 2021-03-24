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
    constructor(port, options = {}) {
        this.port = port
        this.cert = new SelidoCert({
            verbose: options.verbose || false,
            debug: options.debug || false
        })
        this.verbosity = options.verbose || false
        this.debug = options.debug || false
        this.quiet = options.quiet || false
        this.code_timeout = options.code_timeout || 180000

        this.open_codes = []
        this.unclaimed_codes = []
    }

    async start() {
        try {
            let options = await this.cert.getAuthOptions()

            this.setHandlers()

            var httpsServer = https.createServer(options, app)
            httpsServer.listen(this.port, "0.0.0.0", () => {
                this.verbose("Selido auth listening on port " + this.port)
            })
        }
        catch (e) {
            this.error(e)
            process.exit(1)
        }

    }

    async getOrGenerateMainOptions() {
        return this.cert.getOrGenerateMainOptions()
    }

    getOpenCodes() {
        if (this.open_codes.length > 0) {
            return this.open_codes
        }
        else {
            return false
        }
    }

    setHandlers() {

        app.get('/authenticate/ca/', async (req, res) => {
            try {
                let ca = fs.readFileSync(process.cwd() + '/certs/' + 'ca.crt', { encoding: 'utf-8' })
                // When reading on windows, file will include \r\n
                // As far as I can tell, .crt file cannot contain \ as a character, so replacing is okay
                ca = ca.replace(/\r/g, "");
                res.status(200).send(new SelidoResponse('getCA', 'success', 'Got CA file', 200, ca))
            }
            catch (e) {
                res.status(500).send(new SelidoResponse('getCA', 'failed', 'An internal server error occured, check server logs', 500))
                this.error(e)
            }

        })

        app.get('/authenticate/:name', async (req, res) => {
            const action = 'authRequest'
            const pass = generator.generatePassphrase(6)
            //TODO: Add timeout on challenges
            let code = { name: req.params.name, code: pass }
            this.open_codes.push(code)
            try {
                await this.cert.genClientKey(req.params.name)
                await this.cert.genClientCSR(req.params.name)
                let cli_name_path = process.cwd() + '/certs/' + req.params.name
                let key = fs.readFileSync(cli_name_path + '.key')
                let auth = { name: req.params.name, code: pass, key: key.toString() }

                res.status(200).send(new SelidoResponse(action, 'success', 'Got authentication code and unsigned key', 200, auth))

                setTimeout(() =>
                    this.deleteCode(code), this.code_timeout
                )
            }
            catch (e) {
                res.status(500).send(new SelidoResponse(action, 'failed', 'An internal server error occured, check server logs', 500))
                this.error(e)
            }

        })

        app.post('/authenticated/', async (req, res) => {
            const action = 'authConfirm'
            let check_auth = req.body.code
            let exists = await this.existsCode(check_auth)
            let verified = await this.isVerified(check_auth)

            try {
                if (verified) {
                    let cli_name_path = process.cwd() + '/certs/' + check_auth.name
                    let cert = fs.readFileSync(cli_name_path + '.crt')
                    res.status(200).send(new SelidoResponse(action, 'success', 'Got signed certificate', 200, cert.toString()))
                    this.cert.deleteClientCerts(check_auth.name)
                }
                else if (exists && !verified) {
                    res.status(401).send(new SelidoResponse(action, 'failed', 'This code has not been verified by an authenticated client yet', 401))
                }
                else {
                    res.status(403).send(new SelidoResponse(action, 'failed', 'This code doesnt exist, or has timed out', 403))
                }

            }
            catch (e) {
                res.status(500).send(new SelidoResponse(action, 'failed', 'An internal server error occured, check server logs', 500))
                this.error(e)
            }
        })
    }

    // This should *never* be called from a non-authorized request
    async verifyCode(code) {
        if (this.open_codes.length > 0) {
            for (var i = this.open_codes.length - 1; i >= 0; i--) {
                let open_code = this.open_codes[i]
                if (
                    code.name == open_code.name && code.code.length == open_code.code.length
                    && open_code.code.every(function (u, i) {
                        return u == code.code[i]
                    })
                ) {
                    await this.cert.genClientCert(code.name)
                    this.unclaimed_codes.push(this.open_codes[i])
                    this.open_codes.splice(i, 1)
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
        try {
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
        catch (e) {
            this.error(e)
        }
    }

    async existsCode(code) {
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