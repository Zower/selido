const { spawn } = require("child_process");
const fs = require('fs')

// TODO: This whole things is extremely jank and needs to be fixed, I'm just trying to get https to work.
module.exports = class SelidoCert {
    constructor(host = 'localhost', client_name) {
        this.host = host
        this.path = './certs/'
        this.client_name = client_name
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
                    console.log('All certificates were not found, performing first time setup. If this is a mistake, abort and check your certificates.')
                    this.genCerts()
                        .then(res => {
                            this.genClientKey().then(() => {
                                console.log("---------------------------------------")
                                console.log("Copy ca.crt, client.key and client.crt from certs/ folder to your .selido/certs/ folder where you have your client.\nAfter this you can authenticate new machines from an authenticated client.")
                                resolve(res)
                            })
                                .catch(err => {
                                    reject(err)
                                })
                        })
                        .catch(err => {
                            reject(err)
                        })
                }
            }
            catch {
                reject("An error occured reading certificates.")
            }
        })
    }

    genCerts() {
        return new Promise((resolve, reject) => {
            this.genCA().then(result => {
                resolve(result)
            })
                .catch(err => {
                    reject(err)
                })
        })
    }

    genCA() {
        return new Promise((resolve, reject) => {
            const subjName = 'subjectAltName=DNS:' + this.host
            const ca_create = spawn("openssl", ["req", "-new", "-x509", "-nodes", "-days", "365", "-addext", subjName, "-subj", "/CN=selido", "-keyout", "./certs/ca.key", "-out", "./certs/ca.crt"])

            // ca_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            ca_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            ca_create.on('error', (error) => {
                console.error("Failed to create certificates, maybe openssl is not installed? Error:")
                reject(error)
            })

            ca_create.on("close", () => {
                this.genServerKey()
                    .then(res => {
                        resolve(res)
                    })
                    .catch(err => {
                        reject(err)
                    })
            })
        })
    }

    genServerKey() {
        return new Promise((resolve, reject) => {
            const skey_create = spawn("openssl", ["genrsa", "-out", "./certs/server.key", "2048"])

            // skey_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            skey_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            skey_create.on('error', err => {
                reject(err)
            })
            skey_create.on("close", () => {
                this.genCSR()
                    .then(res => {
                        resolve(res)
                    })
                    .catch(err => {
                        reject(err)
                    })
            })
        })
    }

    genCSR() {
        return new Promise((resolve, reject) => {
            //TODO: allow other subj than localhost
            const host_str = '/CN=' + this.host
            const subjName = 'subjectAltName=DNS:' + this.host
            const csr_create = spawn("openssl", ["req", "-new", "-key", "./certs/server.key", "-subj", host_str, "-addext", subjName, "-out", "./certs/server.csr"])

            // csr_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            csr_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            csr_create.on('error', err => {
                reject(err)
            })

            csr_create.on("close", () => {
                this.genServerCert()
                    .then(res => {
                        resolve(res)
                    })
                    .catch(err => {
                        reject(err)
                    })
            })
        })
    }

    genServerCert() {
        return new Promise((resolve, reject) => {
            const subjName = 'subjectAltName=DNS:' + this.host
            const scert_create = spawn("openssl", ["x509", "-req", "-in", "./certs/server.csr", "-extfile", "./v3.ext", "-CA", "./certs/ca.crt", "-CAkey", "./certs/ca.key", "-CAcreateserial", "-days", "365", "-out", "./certs/server.crt"])

            // scert_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            scert_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            scert_create.on('error', err => {
                reject(err)
            })
            scert_create.on("close", () => {
                resolve(this.getOptions())
            })
        })
    }

    genClientKey() {
        return new Promise((resolve, reject) => {
            const ckey_create = spawn("openssl", ["genrsa", "-out", "./certs/client.key", "2048"])

            // scert_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            ckey_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            ckey_create.on('error', err => {
                reject(err)
            })
            ckey_create.on("close", () => {
                this.genClientCSR().then(() => {
                    resolve()
                })
                    .catch(err => {
                        reject(err)
                    })
            })

        })
    }

    genClientCSR() {
        return new Promise((resolve, reject) => {
            const client_str = '/CN=' + this.client_name
            const ccsr_create = spawn("openssl", ["req", "-new", "-key", "./certs/client.key", "-subj", client_str, "-out", "./certs/client.csr"])

            // scert_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            ccsr_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            ccsr_create.on('error', err => {
                reject(err)
            })
            ccsr_create.on("close", () => {
                this.genClientCert()
                    .then(() => {
                        resolve()
                    })
                    .catch(err => {
                        reject(err)
                    })
            })
        })
    }

    genClientCert() {
        return new Promise((resolve, reject) => {
            const ccert_create = spawn("openssl", ["x509", "-req", "-in", "./certs/client.csr", "-CA", "./certs/ca.crt", "-CAkey", "./certs/ca.key", "-CAcreateserial", "-days", "365", "-out", "./certs/client.crt"])

            // scert_create.stdout.on("data", data => {
            //     process.stdout.write("stdout:" + data)
            // })

            ccert_create.stderr.on("data", data => {
                process.stderr.write(data)
            })

            ccert_create.on('error', err => {
                reject(err)
            })
            ccert_create.on("close", () => {
                resolve()
            })
        })

    }

}