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

    // Temporary fix
    printAll() {
        Resource.find().exec()
            .then(resources => {
                resources.forEach(resource => {
                    console.log(resource)
                })
            })
    }


    // Requests


    get(id, tags) {
        return new Promise((resolve, reject) => {
            const action = 'get'
            Resource.find(
                { "_id": id }
            ).exec()
                .then(resources => {
                    if (resources.length == 0) {
                        resolve(new SelidoResponse(action, failed, 'No resources with that id', 404, prettyId(id)))
                    }
                    else if (resources.length > 1) {
                        reject(new SelidoResponse(action, failed, 'More than one resource with same id', 404, prettyId(id)))
                    }
                    var resource = resources[0]
                    resolve(new SelidoResponse(action, success, 'Got resource', 200, prettyConvert(resource)))

                    // Saving this for search
                    // else {
                    //     let resourcesToSend = []

                    // resources.forEach(function (resource) {
                    //     let total = false
                    //     // Check each sent tag against every found resource
                    //     tags.forEach(function (tag) {
                    //         // If the resource contains the tag
                    //         if (resource.tags.some(tag_check => tag_check.key === tag.key && tag_check.value === tag.value)) {
                    //             total = true
                    //         }
                    //         else {
                    //             total = false
                    //         }

                    //     })
                    //     if (total) {
                    //         resourcesToSend.push(resource)
                    //     }
                    // })

                    // resolve(new SelidoResponse(action, success, 'Got resources', 200, resourcesToSend))

                })
                .catch(err => {
                    reject(new SelidoResponse(action, failed, 'Couldnt execute query against database. Error:\n' + err, 500))
                });
        })
    }

    add(tags) {
        return new Promise((resolve, reject) => {
            const action = 'add'

            var res = new Resource({
                tags
            })
            res.save()
                .then(() => {
                    resolve(new SelidoResponse(action, success, 'Created entry', 200, prettyId(res._id)))
                })
                .catch(err => {
                    reject(new SelidoResponse(action, failed, 'Couldn\'t save to database: Error\n' + err, 500))
                })
        })
    }

    addTags(id, tags) {
        return new Promise((resolve, reject) => {
            const action = 'tag'

            Resource.find({ "_id": id })
                .then(resources => {
                    if (resources.length == 0) {
                        reject(new SelidoResponse(action, failed, 'No resources with that id', 404, prettyId(id)))
                    }
                    else if (resources.length > 1) {
                        reject(new SelidoResponse(action, failed, 'More than one resource with same id', 404, prettyId(id)))
                    }
                    var resource = resources[0]

                    // Add tags to element
                    tags.forEach(tag => {
                        resource.tags.push(tag)
                    })

                    // Save to database
                    resource.save().then(resource => {
                        resolve(new SelidoResponse(action, success, 'Tagged resource', 200, prettyId(resource._id)))
                    })

                }).catch(function (err) {
                    reject(new SelidoResponse(action, failed, 'Failed to tag, Error:\n' + err, 500))
                });
        })
    }

    delTags(id, tags) {
        return new Promise((resolve, reject) => {
            const action = 'delTags'
            Resource.find({ "_id": id })
                .then(resources => {
                    if (resources.length == 0) {
                        reject(new SelidoResponse(action, failed, 'No resource with that id', 404, prettyId(id)))
                    }
                    else if (resources.length > 1) {
                        reject(new SelidoResponse(action, failed, 'More than one resource with same id', 404, prettyId(id)))
                    }
                    var resource = resources[0]

                    // var msg = ''
                    // var promiseArr = resources.map(function (resource) {

                    // Add tags to element
                    tags.forEach(tag => {
                        resource.tags = resource.tags.filter(function (tag_check) {
                            return !(tag_check.key === tag.key && tag_check.value === tag.value)
                        })
                    })

                    // msg += 'Deleted tags from ' + id + '\n'

                    resource.save().then(resource => {
                        resolve(new SelidoResponse(action, success, 'Deleted tags from resource', 200, prettyId(resource._id)))
                    })
                }).catch(function (err) {
                    reject(new SelidoResponse(action, failed, 'Failed to delete tags Error:\n' + err, 500))
                });

            // Promise.all(promiseArr)
            //     .then(function () {
            //         resolve(new SelidoResponse(action, success, msg, 200, tags))
            //     })
            //     .catch(function (err) {
            //         reject(new SelidoResponse(action, failed, 'Failed to delete tags from entry with id' + id + ' Error: \n' + err, 500, tags))
            //     })
        })
        // })
    }

}

function prettyConvert(object) {
    return {
        id: object['_id'],
        tags: object['tags']
    }
}

function prettyId(id) {
    return {
        id: id
    }
}

class SelidoResponse {
    constructor(action, status, message, code, objects) {
        this.action = action
        this.status = status
        this.code = code
        this.message = message
        this.objects = objects
        this.time = Date.now()
    }
}