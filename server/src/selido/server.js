'use strict';
const express = require('express');
const SelidoDB = require('../db/db.js');
var app = express();

module.exports = class SelidoServer {
    constructor(args) {
        this.db = new SelidoDB(args.uri)
        this.port = args.port
    }

    start() {
        return new Promise((resolve, reject) => {
            this.connectToDB()
                .then((message) => {
                    process.on('uncaughtException', function (err) {
                        if (err.code === 'EADDRINUSE')
                            reject('Port already in use, perhaps another instance is running? Try another port with -p PORT');
                        else
                            reject('Unexpected problem. Error:\n' + err);
                    });

                    app.get('/', function (req, res) {
                        res.send('Hello World!');
                    });

                    app.listen(this.port, () => {
                        resolve(message + '\nSelido server listening on port ' + this.port)
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
                .then((message) => {
                    resolve(message)
                })
                .catch(err => {
                    reject(err)
                })
        })
    }

    query() {

    }

}