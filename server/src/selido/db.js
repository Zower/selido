'use strict';
const fs = require('fs');
const mongoose = require('mongoose');
const { resolve } = require('path');
var readline = require('readline');

var Resource = require('../models/resource.js')
const SelidoResponse = require('./response.js')

const failed = 'failed'
const success = 'success'

module.exports = class SelidoDB {
    constructor(url, options = {}) {
        this.host = url
        this.use_password = options.use_password || true
        this.verbosity = options.verbose || false
        this.debug = options.debug || false
    }

    // Startup
    async init() {
        if (this.use_password) {
            try {
                let auth_file = fs.readFileSync(process.cwd() + '/db_auth.txt')
                // This replace is probably unwise :P
                let auth_array = auth_file.toString().replace(/\r/g, "").split('\n')
                if (auth_array.length == 2) {
                    let message = await this.connectWithAuth(auth_array[0], auth_array[1])
                    return message
                }
                else {
                    console.log("db_auth.txt is wrongly formatted, make sure it's username on one line, password on the second")
                    process.exit(1)
                }
            }
            catch (e) {
                if (err.code == 'ENOENT') {
                    var rl = readline.createInterface({
                        input: process.stdin,
                        output: process.stdout
                    });
                    rl.question("No db_auth.txt file present.\nProvide the accountname/password used when creating the database\nName: ", user => {
                        rl.question("Password: ", pass => {
                            rl.close()
                            let auth = user + "\n" + pass
                            fs.writeFileSync(process.cwd() + '/db_auth.txt', auth)
                            return this.connectWithAuth(user, pass)
                        })
                    })
                }
                else {
                    this.error("Failed to connect to database with a password, check that db_auth.txt is correct. Error:")
                    this.error(e)
                    process.exit(1)
                }
            }
        }
        else {
            // No password connect
            await mongoose.connect('mongodb://' + this.host + '/selido', { useNewUrlParser: true, useUnifiedTopology: true })
                .catch(err => {
                    this.info('Failed to connect to mongodb, is mongod started and running on ' + 'mongodb://' + this.host + '/selido' + ' and username/password correct? You can specify location with -d (e.g. -d localhost)')
                    this.error(err)
                    process.exit(1)
                });

            this.db = mongoose.connection;

            this.db.on('error', err => {
                this.error(err)
                process.exit(1)
            })

            return 'Connected to db!'

        }
    }

    async connectWithAuth(user, pass) {
        await mongoose.connect('mongodb://' + this.host + '/selido', { useNewUrlParser: true, useUnifiedTopology: true, user: user, pass: pass, auth: { authSource: "admin" } })
            .catch(err => {
                this.info('Failed to connect to mongodb, is mongod started and running on ' + 'mongodb://' + this.host + '/selido' + ' and username/password correct? You can specify location with -d (e.g. -d localhost)')
                this.error(err)
                process.exit(1)
            });


        this.db = mongoose.connection;

        this.db.on('error', err => {
            if (err.codeName == 'AuthenticationFailed') {
                this.info("Wrong password was probably used for authentication, check your db_auth.txt")
            }
            this.error(err)
            process.exit(1)
        })

        return 'Connected to db with authentication!'

    }

    // Requests
    async get(id) {
        const action = 'get'
        // Found this on stackoverflow, im sure its perfect (check correct syntax for id)
        try {
            if (id.match(/^[0-9a-fA-F]{24}$/)) {
                let resources = await Resource.find(
                    { "_id": id }
                ).exec()

                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources with that id', 404, prettyId(id))
                }
                else if (resources.length > 1) {
                    return new SelidoResponse(action, failed, 'More than one resource with same id, this is unexpected behavior, try deleting the item', 400, prettyId(id))
                }
                var resource = resources[0]
                return new SelidoResponse(action, success, 'Got resource', 200, prettyConvert(resource))

            }
            else {
                return new SelidoResponse(action, failed, 'Invalid id', 400)
            }
        }

        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async add(tags) {
        const action = 'add'

        try {
            var res = new Resource({
                tags
            })
            let resource = await res.save()
            return new SelidoResponse(action, success, 'Created resource', 200, prettyConvert(resource))
        }
        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async delete(id) {
        const action = 'delete'

        try {
            let answer = await Resource.deleteOne({ "_id": id })
            if (answer.deletedCount > 0) {
                return new SelidoResponse(action, success, 'Deleted resource', 200)
            }
            else {
                return new SelidoResponse(action, failed, 'No resource with that id', 404, prettyId(id))
            }
        }
        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async addTags(id, tags) {
        const action = 'tag'

        try {
            let resources = await Resource.find({ "_id": id }).exec()
            if (resources.length == 0) {
                return new SelidoResponse(action, failed, 'No resources with that id', 404, prettyId(id))
            }
            else if (resources.length > 1) {
                return new SelidoResponse(action, failed, 'More than one resource with same id', 404, prettyId(id))
            }
            var resource = resources[0]

            // Add tags to element
            tags.forEach(tag => {
                resource.tags.push(tag)
            })

            // Save to database
            resource = await resource.save()
            return new SelidoResponse(action, success, 'Tagged resource', 200, prettyConvert(resource))
        }
        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async delTags(id, tags) {
        const action = 'delTags'

        try {
            let resources = await Resource.find({ "_id": id }).exec()
            if (resources.length == 0) {
                return new SelidoResponse(action, failed, 'No resource with that id', 404, prettyId(id))
            }
            else if (resources.length > 1) {
                return new SelidoResponse(action, failed, 'More than one resource with same id', 404, prettyId(id))
            }


            var resource = resources[0]

            // Delete tags from element
            tags.forEach(tag => {
                resource.tags = resource.tags.filter(function (tag_check) {
                    return !(tag_check.key === tag.key && tag_check.value === tag.value)
                })
            })

            resource = await resource.save()
            return new SelidoResponse(action, success, 'Deleted tags from resource', 200, prettyConvert(resource))
        }

        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async find(tags, and_search, all = false) {
        const action = 'find'

        // Error checking
        if (!(typeof tags !== 'undefined' && typeof and_search !== 'undefined')) {
            return new SelidoResponse(action, failed, 'Undefined parameters sent', 400)
        }

        try {
            // Return all resources
            if (all) {
                let resources = await Resource.find().exec()
                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources exist', 404)
                }
                return new SelidoResponse(action, success, 'Found resource(s)', 200, prettyConvert(resources, true))
            }

            // No tags
            else if (tags.length == 0) {
                return new SelidoResponse(action, failed, 'No tags specified', 400)
            }

            // Finds all resources that have all of the tags specified, but not all the possible tags
            else if (and_search) {
                let resources = await Resource.find({ tags: { $all: tags } })
                    .exec()
                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources with those tags', 404)
                }
                return new SelidoResponse(action, success, 'Found resource(s)', 200, prettyConvert(resources, true))
            }
            // One of the tags has to match
            else {
                let to_find = []
                let i = 0
                // Creates a list of objects (e.g. [{tags: {key: 'foo', value: 'bar'}}, {tags: {key: 'a', value: 'b'}}])
                // from the tags sent in, so that mongo can filter on only some of them
                tags.forEach(tag => {
                    to_find[i] = { tags: tag }
                    i++
                })
                let resources = await Resource.find({ $or: to_find })
                    .exec()
                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources with those tags', 404)
                }
                return new SelidoResponse(action, success, 'Found resource(s)', 200, prettyConvert(resources, true))
            }

        }
        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
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

function prettyConvert(object, multiple = false) {
    if (multiple) {
        let send = []
        for (const [index, obj] of object.entries()) {
            send[index] = { id: obj._id, tags: obj.tags }
        }
        return send
    }
    else {
        return [{
            id: object['_id'],
            tags: object['tags']
        }]
    }
}

function prettyId(id) {
    return {
        id: id
    }
}