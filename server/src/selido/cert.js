'use strict'

const { spawn } = require("child_process");
const fs = require('fs');
const os = require('os')
var readline = require('readline');

const log = require('../logger/log.js');

module.exports = class SelidoCert {
    constructor(options) {
        this.verbosity = options.verbose || false
        this.debug = options.debug || false
        this.path = process.cwd() + '/certs/'
    }

    checkOptions() {
        if (fs.existsSync(this.path + 'ca.crt') && fs.existsSync(this.path + 'server.crt') && fs.existsSync(this.path + 'server.key')) {
            return true
        }
        return false
    }

    getMainOptions() {
        return {
            ca: fs.readFileSync(this.path + 'ca.crt'),
            cert: fs.readFileSync(this.path + 'server.crt'),
            key: fs.readFileSync(this.path + 'server.key'),
            requestCert: true,
            rejectUnathorized: true
        }
    }

    getAuthOptions() {
        if (this.checkOptions()) {
            return {
                ca: fs.readFileSync(this.path + 'ca.crt'),
                cert: fs.readFileSync(this.path + 'server.crt'),
                key: fs.readFileSync(this.path + 'server.key'),
                requestCert: false,
                rejectUnathorized: false
            }
        }
        else {
            throw new Error("Attempted to start selido auth before main certificates are set, exiting")
        }
    }

    async getOrGenerateMainOptions() {
        return new Promise((resolve, reject) => {
            try {
                // TODO check for expire and refresh
                let check_options = this.checkOptions()
                if (!check_options) {

                    this.info('Certificates are missing')

                    var rl = readline.createInterface({
                        input: process.stdin,
                        output: process.stdout
                    });

                    rl.question("Performing first time setup. If this is a mistake, abort and check your certificates.') Continue? (y/n): ", cont => {
                        if (cont === 'y') {
                            rl.question("Provide comma separated DNS names for your server, e.g. example.com, www.example.com. If running locally type localhost: ", dns => {
                                rl.question("Provide comma separated IPs for your server, e.g. 203.0.113.254, 198.51.100.3. If running locally type 127.0.0.1: ", ips => {
                                    rl.question("Provide a client name, e.g. a username: ", un => {
                                        rl.question("Will this machine be the first client (automatically copy certificates to {user}/.selido/certs/)? (y/n): ", async copy => {
                                            rl.close()
                                            //TODO: check for validity
                                            this.dns = dns
                                            this.ips = ips

                                            await this.genServerCerts()
                                            this.verbose("Finished making server certificates, creating initial client cert.")
                                            await this.genClientCerts(un)
                                            this.verbose("Done.")
                                            if (copy == 'y') {
                                                let printErr = function (err) { if (err) this.error(err) }
                                                fs.unlink(this.path + un + '.csr', printErr)
                                                var new_path = os.homedir() + '/.selido/certs/'
                                                fs.mkdirSync(new_path, { recursive: true })
                                                fs.copyFile(this.path + 'ca.crt', new_path + 'ca.crt', printErr)
                                                fs.rename(this.path + un + '.key', new_path + un + '.key', printErr)
                                                fs.rename(this.path + un + '.crt', new_path + un + '.crt', printErr)
                                            }
                                            else {
                                                let message = "\n---------------------------------------\n"
                                                message += "*copy* ca.crt and *move* client.key and client.crt from certs/ folder to your .selido/certs/ folder where you have your client.\nAfter this you can authenticate new machines from an authenticated client.\n"
                                                message += "---------------------------------------"
                                                this.info(message)
                                            }
                                            resolve(this.getMainOptions())
                                        })
                                    })
                                })
                            })
                        }
                        else {
                            rl.close()
                            process.exit(0)
                        }
                    })
                }
                else {
                    resolve(this.getMainOptions())
                }
            }
            catch (e) {
                this.error("An error occured generating certificates.")
                reject(e)
                process.exit(1)
            }

        })
    }

    async genServerCerts() {
        try {
            await this.genCA()
            await this.genServerKey()
            await this.genCSR()
            await this.genServerCert()
        }
        catch (e) {
            this.error("An error occured generating server certificates.")
            this.error(e)
            process.exit(1)
        }

    }

    async genClientCerts(client_name) {
        try {
            await this.genClientKey(client_name)
            await this.genClientCSR(client_name)
            await this.genClientCert(client_name)
        }
        catch (error) {
            this.error("Couldn't generate client certificates")
            this.error(error)
            process.exit(1)
        }
    }

    deleteClientCerts(client_name) {
        let throwErr = function (err) { if (err) throw err }
        fs.unlink(this.path + client_name + '.crt', throwErr)
        fs.unlink(this.path + client_name + '.key', throwErr)
        fs.unlink(this.path + client_name + '.csr', throwErr)
    }

    // Creates the Certificate Authority.
    genCA() {
        this.verbose("Generating Certificate Authority..")
        const subjectAltName = 'subjectAltName=DNS:' + this.dns
        return this.openssl(["req", "-new", "-x509", "-nodes", "-days", "365", "-addext", subjectAltName, "-subj", "/CN=selido", "-keyout", this.path + "ca.key", "-out", this.path + "ca.crt"])
    }

    // Creates the server key.
    genServerKey() {
        this.verbose("Generating Server Key..")
        return this.openssl(["genrsa", "-out", this.path + "server.key", "2048"])
    }

    // Creates the Certificate Signing Request.
    genCSR() {
        this.verbose("Generating Certificate Signing Request..")
        const host_str = '/CN=' + this.dns
        const subjName = 'subjectAltName=DNS:' + this.dns
        return this.openssl(["req", "-new", "-key", this.path + "server.key", "-subj", host_str, "-addext", subjName, "-out", this.path + "server.csr"])
    }

    // Generates the server certificate
    // This one is different due to the need to write to the v3.ext file, I haven't found a way to include the extension via cmd
    async genServerCert() {
        this.verbose("Generating Server Certificate..")
        await this.write_extfile()
        return this.openssl(["x509", "-req", "-in", this.path + "server.csr", "-extfile", this.path + "v3.ext", "-CA", this.path + "ca.crt", "-CAkey", this.path + "ca.key", "-CAcreateserial", "-days", "365", "-out", this.path + "server.crt"])
    }

    // Could do with not passing name to every function

    // Genereates a key for a new client
    genClientKey(client_name) {
        this.verbose("Generating Client Key..")
        const key_name = client_name + ".key"
        return this.openssl(["genrsa", "-out", this.path + key_name, "2048"])
    }

    // Generates a client Certificate Signing Request
    genClientCSR(client_name) {
        this.verbose("Generating Client Certificate Signing Request")
        const key_name = client_name + ".key"
        const csr_name = client_name + ".csr"
        const un = '/CN=' + client_name
        return this.openssl(["req", "-new", "-key", this.path + key_name, "-subj", un, "-out", this.path + csr_name])
    }

    // Generates a client Certificate
    genClientCert(client_name) {
        this.verbose("Generating Client Certificate..")
        const csr_name = client_name + ".csr"
        const crt_name = client_name + ".crt"
        return this.openssl(["x509", "-req", "-in", this.path + csr_name, "-CA", this.path + "ca.crt", "-CAkey", this.path + "ca.key", "-CAcreateserial", "-days", "365", "-out", this.path + crt_name])
    }

    async write_extfile() {
        try {
            const open = fs.openSync(this.path + "v3.ext", 'w')

            let altName = 'authorityKeyIdentifier=keyid,issuer\n'
            altName += 'basicConstraints=CA:FALSE\n'
            altName += 'keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment\n'
            altName += 'subjectAltName = @alt_names\n\n\n'
            altName += '[alt_names]\n'
            altName += 'DNS = ' + this.dns + '\n'
            altName += 'IP = ' + this.ips

            fs.writeSync(open, altName)

            fs.closeSync(open)
        }
        catch (e) {
            this.error("An error occured writing to v3.ext file:")
            this.error(e)
            process.exit(1)
        }
    }
    async openssl(args) {
        return new Promise((resolve, reject) => {
            const openssl = spawn("openssl", args)

            openssl.stdout.on("data", data => {
                if (this.debug) {
                    process.stdout.write(data)
                }
            })

            openssl.stderr.on("data", data => {
                if (this.debug) {
                    process.stderr.write(data)
                }
            })

            openssl.on('error', error => {
                this.error("Failed to create all certificates, maybe openssl is not installed?")
                reject(error)
            })

            openssl.on("close", () => {
                resolve()
            })
        })
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
