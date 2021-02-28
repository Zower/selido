'use strict';
const mongoose = require('mongoose');
const log = require('../logger/log.js');


module.exports = class SelidoDB {
    constructor(url) {
        this.url = 'mongodb://' + url + '/selido'
    }
    init() {
        return new Promise((resolve, reject) => {
            mongoose.connect(this.url, { useNewUrlParser: true, useUnifiedTopology: true }).catch(err => { reject('Failed to connect to mongodb, is mongod started? Error:\n' + err) });
            this.db = mongoose.connection;

            this.db.on('error', () => {
                log.error('Lost connection to db..');
            });

            this.db.once('open', () => {
                resolve('Connected to db!')
            });
        })

    }
}