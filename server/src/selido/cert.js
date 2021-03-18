const { spawn } = require("child_process");
const fs = require('fs')
var readline = require('readline');

// TODO: This whole things is extremely jank and needs to be fixed, I'm just trying to get https to work.
module.exports = class SelidoCert {
    constructor(verbose) {
        this.verbose = verbose
        this.path = process.cwd() + '/certs/'
    }

    getOptions() {
        return {
            ca: fs.readFileSync(this.path + 'ca.crt'),
            cert: fs.readFileSync(this.path + 'server.crt'),
            key: fs.readFileSync(this.path + 'server.key'),
            rejectUnathorized: false,
            requestCert: true
        }
    }

    getOrGenerateOptions() {
        return new Promise((resolve, reject) => {
            try {
                // TODO check for expire and refresh
                if (fs.existsSync(this.path + 'ca.crt') && fs.existsSync(this.path + 'server.crt') && fs.existsSync(this.path + 'server.key')) {
                    resolve(this.getOptions())
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
                                        rl.close()
                                        //TODO: check
                                        scert.dns = dns
                                        scert.ips = ips
                                        scert.un = un

                                        scert.genServerCerts()
                                            .then(() => {
                                                scert.print_verbose("Finished making server certificates, creating initial client cert.")
                                                scert.genClientCerts()
                                                    .then(() => {
                                                        let message = "\n---------------------------------------\n"
                                                        message += "Copy ca.crt, client.key and client.crt from certs/ folder to your .selido/certs/ folder where you have your client.\nAfter this you can authenticate new machines from an authenticated client.\n"
                                                        message += "---------------------------------------"
                                                        console.log(message)
                                                        resolve(scert.getOptions())
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
                        }
                        else {
                            rl.close()
                            process.exit(0)
                        }
                    })
                }
            }
            catch {
                reject("An error occured reading certificates.")
            }
        })
    }

    genServerCerts() {
        return new Promise((resolve, reject) => {
            this.genCA()
                .then(() => {
                    this.genServerKey()
                        .then(() => {
                            this.genCSR()
                                .then(() => {
                                    this.genServerCert()
                                        .then(() => {
                                            resolve()
                                        })
                                        .catch(err => {
                                            reject(err)
                                        })
                                })
                                .catch(err => {
                                    reject(err)
                                })
                        })
                        .catch(err => {
                            reject(err)
                        })
                })
                .catch(err => {
                    reject(err)
                })
        })
    }

    genClientCerts(client_name) {
        return new Promise((resolve, reject) => {
            this.genClientKey()
                .then(() => {
                    this.genClientCSR(client_name)
                        .then(() => {
                            this.genClientCert()
                                .then(() => {
                                    resolve()
                                })
                                .catch(err => {
                                    reject(err)
                                })
                        })
                        .catch(err => {
                            reject(err)
                        })
                })
                .catch(err => {
                    reject(err)
                })
        })
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
    genServerCert() {
        return new Promise((resolve, reject) => {
            this.print_verbose("Generating Server Certificate..")
            this.write_extfile()
                .then(() => {
                    openssl(["x509", "-req", "-in", this.path + "server.csr", "-extfile", this.path + "v3.ext", "-CA", this.path + "ca.crt", "-CAkey", this.path + "ca.key", "-CAcreateserial", "-days", "365", "-out", this.path + "server.crt"], this.verbose)
                        .then(() => {
                            resolve()
                        })
                        .catch(err => {
                            reject(err)
                        })
                })
                .catch(err => {
                    reject(err)
                })
        })
    }

    // Genereates a key for a new client
    genClientKey() {
        this.print_verbose("Generating Client Key..")
        return openssl(["genrsa", "-out", this.path + "client.key", "2048"], this.verbose)
    }
    1
    // Generates a client Certificate Signing Request
    genClientCSR(client_name) {
        this.print_verbose("Generating Client Certificate Signing Request")
        const un = '/CN=' + this.un
        return openssl(["req", "-new", "-key", this.path + "client.key", "-subj", un, "-out", this.path + "client.csr"], this.verbose)
    }

    // Generates a client Certificate
    genClientCert() {
        this.print_verbose("Generating Client Certificate..")
        return openssl(["x509", "-req", "-in", this.path + "client.csr", "-CA", this.path + "ca.crt", "-CAkey", this.path + "ca.key", "-CAcreateserial", "-days", "365", "-out", this.path + "client.crt"], this.verbose)
    }

    write_extfile() {
        return new Promise((resolve, reject) => {
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
                resolve()
            }
            catch {
                reject("An error occured writing to v3.ext file for certificate generation")
            }
        })
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