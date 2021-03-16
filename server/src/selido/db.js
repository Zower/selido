'use strict';
const mongoose = require('mongoose');
const { verbose } = require('winston');
const log = require('../logger/log.js')
var Resource = require('../models/resource.js')

const failed = 'failed'
const success = 'success'

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

module.exports = class SelidoDB {
    constructor(url) {
        this.url = 'mongodb://' + url + '/selido'
    }

    // Startup
    init() {
        return new Promise((resolve, reject) => {
            mongoose.connect(this.url, { useNewUrlParser: true, useUnifiedTopology: true })
                .catch(err => {
                    reject('Failed to connect to mongodb, is mongod started and running on ' + this.url + '? You can specify location with -d (e.g. -d localhost)\nError: ' + err)
                });
            this.db = mongoose.connection;

            this.db.once('open', () => {
                resolve('Connected to db!')
            });
        })
    }

    // Temporary fix
    printAll() {
        Resource.find()
            .exec()
            .then(resources => {
                resources.forEach(resource => {
                    console.log(resource)
                })
            })
    }


    // Requests


    get(id) {
        return new Promise((resolve, reject) => {
            const action = 'get'
            // Found this on stackoverflow, im sure its perfect (check correct syntax for id)
            if (id.match(/^[0-9a-fA-F]{24}$/)) {
                Resource.find(
                    { "_id": id }
                )
                    .exec()
                    .then(resources => {
                        if (resources.length == 0) {
                            resolve(new SelidoResponse(action, failed, 'No resources with that id', 404, prettyId(id)))
                        }
                        else if (resources.length > 1) {
                            reject(new SelidoResponse(action, failed, 'More than one resource with same id, this is unexpected behavior, try deleting the item', 400, prettyId(id)))
                        }
                        var resource = resources[0]
                        // if (tags.length == 0) {
                        resolve(new SelidoResponse(action, success, 'Got resource', 200, prettyConvert(resource)))
                    }).catch(err => {
                        reject(new SelidoResponse(action, failed, 'Couldnt execute query against database.\nError: ' + err, 500))
                    });
            }
            else {
                resolve(new SelidoResponse(action, failed, 'Invalid id', 400))
            }
        })
    }

    add(tags) {
        return new Promise((resolve, reject) => {
            const action = 'add'

            var res = new Resource({
                tags
            })
            res.save()
                .then((resource) => {
                    resolve(new SelidoResponse(action, success, 'Created resource', 200, prettyConvert(resource)))
                })
                .catch(err => {
                    reject(new SelidoResponse(action, failed, 'Couldn\'t save to database:\nError: ' + err, 500))
                })
        })
    }

    delete(id) {
        return new Promise((resolve, reject) => {
            const action = 'delete'

            Resource.deleteOne({ "_id": id }).then(resource => {
                resolve(new SelidoResponse(action, success, 'Deleted resource', 200, prettyId(resource._id)))
                //check that resource existed
            }).catch(err => {
                reject(new SelidoResponse(action, failed, 'Couldn\'t delete from database:\nError: ' + err))
            })
        })
    }

    addTags(id, tags) {
        return new Promise((resolve, reject) => {
            const action = 'tag'

            Resource.find({ "_id": id })
                .exec()
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
                        resolve(new SelidoResponse(action, success, 'Tagged resource', 200, prettyConvert(resource)))
                    })

                }).catch(function (err) {
                    reject(new SelidoResponse(action, failed, 'Failed to tag,\nError: ' + err, 500))
                });
        })
    }

    delTags(id, tags) {
        return new Promise((resolve, reject) => {
            const action = 'delTags'
            Resource.find({ "_id": id })
                .exec()
                .then(resources => {
                    if (resources.length == 0) {
                        resolve(new SelidoResponse(action, failed, 'No resource with that id', 404, prettyId(id)))
                    }
                    else if (resources.length > 1) {
                        reject(new SelidoResponse(action, failed, 'More than one resource with same id', 404, prettyId(id)))
                    }
                    var resource = resources[0]

                    // Add tags to element
                    tags.forEach(tag => {
                        resource.tags = resource.tags.filter(function (tag_check) {
                            return !(tag_check.key === tag.key && tag_check.value === tag.value)
                        })
                    })

                    resource.save().then(resource => {
                        resolve(new SelidoResponse(action, success, 'Deleted tags from resource', 200, prettyConvert(resource)))
                    })
                }).catch(function (err) {
                    reject(new SelidoResponse(action, failed, 'Failed to delete tags\nError: ' + err, 500))
                });
        })
    }

    //$all to avoid order in list

    find(tags, and_search, all = false) {
        return new Promise((resolve, reject) => {
            // check that tags exist
            const action = 'find'
            if (all) {
                Resource.find().exec().then(resources => {
                    if (resources.length == 0) {
                        resolve(new SelidoResponse(action, failed, 'No resources exist', 404))
                    }
                    resolve(new SelidoResponse(action, success, 'Found resource(s)', 200, resources))
                }).catch(err => {
                    reject(new SelidoResponse(action, failed, 'Failed to find resources\nError: ' + err, 500))
                })

            }
            else if (tags.length == 0) {
                resolve(new SelidoResponse(action, failed, 'No tags specified', 400))
            }
            else if (and_search) {
                // Finds all resources that have all of the tags specified, but not all the possible tags
                Resource.find({ tags: { $all: tags } })
                    .exec()
                    .then(resources => {
                        if (resources.length == 0) {
                            resolve(new SelidoResponse(action, failed, 'No resources with those tags', 404))
                        }
                        resolve(new SelidoResponse(action, success, 'Found resource(s)', 200, resources))
                    })
                    .catch(err => {
                        reject(new SelidoResponse(action, failed, 'Failed to find resources\nError: ' + err, 500))
                    })
            }
            else {
                let to_find = []
                let i = 0
                // 
                tags.forEach(tag => {
                    to_find[i] = { tags: tag }
                    i++
                })
                Resource.find({ $or: to_find })
                    .exec()
                    .then(resources => {
                        if (resources.length == 0) {
                            resolve(new SelidoResponse(action, failed, 'No resources with those tags', 404))
                        }
                        resolve(new SelidoResponse(action, success, 'Found resource(s)', 200, resources))
                    })
                    .catch(err => {
                        reject(new SelidoResponse(action, failed, 'Failed to find resources\nError: ' + err, 500))
                    })
            }
        })
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