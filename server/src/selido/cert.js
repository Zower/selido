'use strict'

const { spawn } = require("child_process");
const fs = require('fs');
const os = require('os')
var readline = require('readline');

module.exports = class SelidoCert {
    constructor(verbose) {
        this.verbose = verbose
        this.path = process.cwd() + '/certs/'
    }

    getMainOptions() {
        return {
            ca: fs.readFileSync(this.path + 'ca.crt'),
            cert: fs.readFileSync(this.path + 'server.crt'),
            key: fs.readFileSync(this.path + 'server.key'),
            requestCert: true,
            rejectUnathorized: false
        }
    }

    getAuthOptions() {
        if (fs.existsSync(this.path + 'ca.crt') && fs.existsSync(this.path + 'server.crt') && fs.existsSync(this.path + 'server.key')) {
            return {
                ca: fs.readFileSync(this.path + 'ca.crt'),
                cert: fs.readFileSync(this.path + 'server.crt'),
                key: fs.readFileSync(this.path + 'server.key'),
                requestCert: false,
                rejectUnathorized: false
            }
        }
        else {
            // Make better lmao
            console.error("Attempted to start selido auth before main certificates are set, exiting")
            process.exit(1)
        }
    }

    async getOrGenerateMainOptions() {
        return new Promise((resolve, reject) => {
            try {
                // TODO check for expire and refresh
                if (fs.existsSync(this.path + 'ca.crt') && fs.existsSync(this.path + 'server.crt') && fs.existsSync(this.path + 'server.key')) {
                    resolve(this.getMainOptions())
                }
                else {
                    console.log('Certificates are missing, performing first time setup. If this is a mistake, abort and check your certificates.')

                    var rl = readline.createInterface({
                        input: process.stdin,
                        output: process.stdout
                    });

                    var scert = this

                    rl.question("Continue? (y/n): ", function (cont) {
                        if (cont === 'y') {
                            rl.question("Provide comma separated DNS names for your server, e.g. example.com, www.example.com. If running locally type localhost: ", function (dns) {
                                rl.question("Provide comma separated IPs for your server, e.g. 203.0.113.254, 198.51.100.3. If running locally type 127.0.0.1: ", function (ips) {
                                    rl.question("Provide a client name, e.g. a username: ", function (un) {
                                        rl.question("Will this machine be the first client (automatically copy certificates to {user}/.selido/certs/)? (y/n): ", function (copy) {
                                            rl.close()
                                            //TODO: check for validity
                                            scert.dns = dns
                                            scert.ips = ips

                                            scert.genServerCerts()
                                                .then(() => {
                                                    scert.print_verbose("Finished making server certificates, creating initial client cert.")
                                                    scert.genClientCerts(un)
                                                        .then(() => {
                                                            if (copy == 'y') {
                                                                let throwErr = function (err) { if (err) throw err }
                                                                fs.unlink(scert.path + un + '.csr', throwErr)
                                                                var new_path = os.homedir() + '/.selido/certs/'
                                                                fs.copyFile(scert.path + 'ca.crt', new_path + 'ca.crt', throwErr)
                                                                fs.rename(scert.path + un + '.key', new_path + un + '.key', throwErr)
                                                                fs.rename(scert.path + un + '.crt', new_path + un + '.crt', throwErr)
                                                                resolve(scert.getMainOptions())
                                                            }

                                                            else {
                                                                let message = "\n---------------------------------------\n"
                                                                message += "*copy* ca.crt and *move* client.key and client.crt from certs/ folder to your .selido/certs/ folder where you have your client.\nAfter this you can authenticate new machines from an authenticated client.\n"
                                                                message += "---------------------------------------"
                                                                console.log(message)
                                                                resolve(scert.getMainOptions())
                                                            }
                                                        })
                                                        .catch(err => {
                                                            reject(err)
                                                        })
                                                })
                                                .catch(err => {
                                                    reject(err)
                                                })
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
            }
            catch (error) {
                console.error("An error occured generating certificates:")
                console.error(error)
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
        catch (error) {
            console.error("Couldn't generate server certificates")
            console.error(error)
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
            console.error("Couldn't generate client certificates")
            console.error(error)
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
        this.print_verbose("Generating Certificate Authority..")
        const subjectAltName = 'subjectAltName=DNS:' + this.dns
        return openssl(["req", "-new", "-x509", "-nodes", "-days", "365", "-addext", subjectAltName, "-subj", "/CN=selido", "-keyout", this.path + "ca.key", "-out", this.path + "ca.crt"], this.verbose)
    }

    // Creates the server key.
    genServerKey() {
        this.print_verbose("Generating Server Key..")
        return openssl(["genrsa", "-out", this.path + "server.key", "2048"])
    }

    // Creates the Certificate Signing Request.
    genCSR() {
        this.print_verbose("Generating Certificate Signing Request..")
        const host_str = '/CN=' + this.dns
        const subjName = 'subjectAltName=DNS:' + this.dns
        return openssl(["req", "-new", "-key", this.path + "server.key", "-subj", host_str, "-addext", subjName, "-out", this.path + "server.csr"], this.verbose)
    }

    // Generates the server certificate
    // This one is different due to the need to write to the v3.ext file, I haven't found a way to include the extension via cmd
    async genServerCert() {
        this.print_verbose("Generating Server Certificate..")
        await this.write_extfile()
        return openssl(["x509", "-req", "-in", this.path + "server.csr", "-extfile", this.path + "v3.ext", "-CA", this.path + "ca.crt", "-CAkey", this.path + "ca.key", "-CAcreateserial", "-days", "365", "-out", this.path + "server.crt"], this.verbose)
    }

    // Could do with not passing name to every function

    // Genereates a key for a new client
    genClientKey(client_name) {
        this.print_verbose("Generating Client Key..")
        const key_name = client_name + ".key"
        return openssl(["genrsa", "-out", this.path + key_name, "2048"], this.verbose)
    }

    // Generates a client Certificate Signing Request
    genClientCSR(client_name) {
        this.print_verbose("Generating Client Certificate Signing Request")
        const key_name = client_name + ".key"
        const csr_name = client_name + ".csr"
        const un = '/CN=' + client_name
        return openssl(["req", "-new", "-key", this.path + key_name, "-subj", un, "-out", this.path + csr_name], this.verbose)
    }

    // Generates a client Certificate
    genClientCert(client_name) {
        this.print_verbose("Generating Client Certificate..")
        const csr_name = client_name + ".csr"
        const crt_name = client_name + ".crt"
        return openssl(["x509", "-req", "-in", this.path + csr_name, "-CA", this.path + "ca.crt", "-CAkey", this.path + "ca.key", "-CAcreateserial", "-days", "365", "-out", this.path + crt_name], this.verbose)
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
        catch (error) {
            console.error("An error occured writing to v3.ext file")
        }
    }

    print_verbose(message) {
        if (this.verbose) {
            console.log(message)
        }
    }
}

function openssl(args, verbose = false) {
    return new Promise((resolve, reject) => {
        const openssl = spawn("openssl", args)

        openssl.stdout.on("data", data => {
            if (verbose) {
                process.stdout.write(data)
            }
        })

        openssl.stderr.on("data", data => {
            if (verbose) {
                process.stderr.write(data)
            }
        })

        openssl.on('error', error => {
            console.error("Failed to create all certificates, maybe openssl is not installed? Error:")
            reject(error)
        })

        openssl.on("close", () => {
            resolve()
        })

    })

}