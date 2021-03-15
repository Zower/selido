'use strict';
const mongoose = require('mongoose');
const { verbose } = require('winston');
const log = require('../logger/log.js')
var Resource = require('../models/resource.js')

const failed = 'failed'
const success = 'success'


module.exports = class SelidoDB {
    constructor(url) {
        this.url = 'mongodb://' + url + '/selido'
    }


    // Startup
    init() {
        return new Promise((resolve, reject) => {
            mongoose.connect(this.url, { useNewUrlParser: true, useUnifiedTopology: true })
                .catch(err => {
                    reject('Failed to connect to mongodb, is mongod started and running on ' + this.url + '? You can specify location with -d (e.g. -d localhost) Error:\n' + err)
                });
            this.db = mongoose.connection;

            this.db.once('open', () => {
                resolve('Connected to db!')
            });
        })
    }


    // REQUESTS

    get(name, tags) {
        return new Promise((resolve, reject) => {
            const action = 'get'
            Resource.find({
                name
            }).exec()
                .then(resources => {
                    if (resources.length == 0) {
                        resolve(new SelidoResponse(action, failed, 'No resources with that name', 404))
                    }
                    if (tags.length == 0) {
                        resolve(new SelidoResponse(action, success, 'Got resources', 200, resources))
                    }
                    else {
                        let resourcesToSend = []
                        resources.forEach(function (resource) {
                            let total = false
                            // Check each sent tag against every found resource
                            tags.forEach(function (tag) {
                                // If the resource contains the tag
                                if (resource.tags.some(tag_check => tag_check.key === tag.key && tag_check.value === tag.value)) {
                                    total = true
                                }
                                else {
                                    total = false
                                }

                            })
                            if (total) {
                                resourcesToSend.push(resource)
                            }
                        })
                        resolve(new SelidoResponse(action, success, 'Got resources', 200, resourcesToSend))
                    }
                })
                .catch(err => {
                    reject(new SelidoResponse(action, failed, 'Couldnt execute query against database. Error:\n' + err, 500))
                });
        })
    }

    add(name, tags) {
        return new Promise((resolve, reject) => {
            const action = 'add'

            var res = new Resource({
                name,
                tags
            })
            res.save()
                .then(() => {
                    resolve(new SelidoResponse(action, success, 'Created entry ' + name, 200))
                })
                .catch(err => {
                    console.log(err)
                    reject(new SelidoResponse(action, failed, 'Couldn\'t save to database: Error\n' + err, 500, name))
                })
        })
    }

    addTags(name, tags) {
        return new Promise((resolve, reject) => {
            const action = 'tag'
            Resource.find({ name })
                .then(resources => {
                    if (resources.length == 0) {
                        reject(new SelidoResponse(action, failed, 'No resources with that name', 404, name))
                    }
                    var msg = ''
                    var promiseArr = resources.map(function (resource) {
                        tags.forEach(tag => {
                            resource.tags.push(tag)
                        })
                        msg += 'Tagged ' + resource.name + '\n'
                        return resource.save().then()
                    });

                    Promise.all(promiseArr)
                        .then(function () {
                            resolve(new SelidoResponse(action, success, msg, 200))
                        })
                        .catch(function (err) {
                            reject(new SelidoResponse(action, failed, 'Failed to tag ' + resource.name + ' Error:\n' + err, 500, tags))
                        })
                })
        })
    }

    delTags(name, tags) {
        return new Promise((resolve, reject) => {
            const action = 'delTags'
            Resource.find({ name })
                .then(resources => {
                    if (resources.length == 0) {
                        reject(new SelidoResponse(action, failed, 'No resources with that name', 404, name))
                    }
                    var msg = ''
                    var promiseArr = resources.map(function (resource) {
                        tags.forEach(tag => {
                            resource.tags = resource.tags.filter(function (tag_check) {
                                return !(tag_check.key === tag.key && tag_check.value === tag.value)
                            })
                        })
                        msg += 'Deleted tags from ' + resource.name + '\n'
                        return resource.save().then()
                    });

                    Promise.all(promiseArr)
                        .then(function () {
                            resolve(new SelidoResponse(action, success, msg, 200, tags))
                        })
                        .catch(function (err) {
                            reject(new SelidoResponse(action, failed, 'Failed to delete tags from' + resource.name + ' Error:\n' + err, 500, tags))
                        })
                })
        })
    }

}

class SelidoResponse {
    constructor(action, status, message, code = 200, objects = {}) {
        this.action = action
        this.status = status
        this.code = code
        this.message = message
        this.objects = objects
        this.time = Date.now()
    }
}