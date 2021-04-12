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
        this.use_password = options.use_password
        this.verbosity = options.verbose
        this.debug = options.debug
    }

    // Startup
    async init() {
        return new Promise(async (resolve, reject) => {
            if (this.use_password) {
                try {
                    let auth_file = fs.readFileSync(process.cwd() + '/db_auth.txt')
                    // This replace is probably unwise :P
                    let auth_array = auth_file.toString().replace(/\r/g, "").split('\n')
                    if (auth_array.length == 2) {
                        let message = await this.connectWithAuth(auth_array[0], auth_array[1])
                        resolve(message)
                    }
                    else {
                        console.log("db_auth.txt is wrongly formatted, make sure it's username on one line, password on the second")
                        process.exit(1)
                    }
                }
                catch (err) {
                    if (err.code == 'ENOENT') {
                        var rl = readline.createInterface({
                            input: process.stdin,
                            output: process.stdout
                        });
                        rl.question("No db_auth.txt file present.\nProvide the accountname/password used when creating the database\nName: ", user => {
                            rl.question("Password: ", async pass => {
                                rl.close()
                                let auth = user + "\n" + pass
                                fs.writeFileSync(process.cwd() + '/db_auth.txt', auth)
                                let message = await this.connectWithAuth(user, pass)
                                resolve(message)
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

                resolve('Connected to db!')

            }

        })
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
    async get(ids) {
        const action = 'get'
        // Found this on stackoverflow, im sure its perfect (check correct syntax for id)
        try {
            let valid_ids = findValidIds(ids)
            let resources = await Resource.find(
                { "_id": { $in: valid_ids } }
            ).exec()

            if (resources.length == 0) {
                return new SelidoResponse(action, failed, 'No resources with those id(s)', 404)
            }
            return new SelidoResponse(action, success, 'Got resource(s)', 200, prettyConvert(resources, true))
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

    async delete(ids) {
        const action = 'delete'

        try {
            let valid_ids = findValidIds(ids)
            let answer = await Resource.deleteMany({ "_id": { $in: valid_ids } })
            if (answer.deletedCount > 0) {
                return new SelidoResponse(action, success, 'Deleted resource(s)', 200)
            }
            else {
                return new SelidoResponse(action, failed, 'No resource with those id(s)', 404)
            }
        }
        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async addTags(ids, tags) {
        const action = 'tag'

        if (!(typeof tags !== 'undefined')) {
            return new SelidoResponse(action, failed, 'Undefined parameters sent', 400)
        }

        try {

            let valid_ids = findValidIds(ids)
            let resources = await Resource.updateMany({ "_id": { $in: valid_ids } }, { $push: { tags } }).exec()
            if (resources.n == 0) {
                return new SelidoResponse(action, failed, 'No resources with those id(s)', 404)
            }

            return new SelidoResponse(action, success, 'Tagged resources', 200)
        }
        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    async delTags(ids, tags) {
        const action = 'delTags'

        if (!(typeof tags !== 'undefined')) {
            return new SelidoResponse(action, failed, 'Undefined parameters sent', 400)
        }

        try {
            let valid_ids = findValidIds(ids)
            let resources = await Resource.updateMany({ "_id": { $in: valid_ids } }, { $pullAll: { tags } }).exec()
            if (resources.n == 0) {
                return new SelidoResponse(action, failed, 'No resources with those id(s)', 404)
            }
            else if (resources.nModified == 0) {
                return new SelidoResponse(action, failed, 'No resources with those ids have the specified tags', 400)
            }

            return new SelidoResponse(action, success, 'Deleted tags from resource(s)', 200)
        }

        catch (e) {
            this.error(e)
            return new SelidoResponse(action, failed, 'Internal error. Check server logs.', 500)
        }
    }

    // Tags must be a list of objects, e.g. [{key: 'foo', value:'bar'}, {key: 'baz', value:'foo'}]. Keys must be list of strings, while and_search and all are booleans
    async find(keys = [], tags = [], and_search = true, all = false) {
        const action = 'find'

        try {
            // Return all resources
            if (all) {
                let resources = await Resource.find().exec()
                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources exist', 404)
                }
                return new SelidoResponse(action, success, 'Found resource(s)', 200, prettyConvert(resources, true))
            }

            // No tags or keys
            else if (keys.length == 0 && tags.length == 0) {
                return new SelidoResponse(action, failed, 'No keys or tags specified', 400)
            }

            // Finds all resources that have all of the tags and keys specified, but not all the possible tags
            else if (and_search) {
                // let resources = await Resource.find({ tags: { $all: keys } })
                //     .exec()
                var resources;
                // Both tag and value search
                if (tags.length > 0 && keys.length > 0) {
                    resources = await Resource.find({ 'tags.key': { $all: keys }, 'tags': { $all: tags } })
                        .exec()
                }
                // Just tag search
                else if (tags.length > 0) {
                    resources = await Resource.find({ 'tags': { $all: tags } })
                        .exec()
                }
                // Just keys
                else {
                    resources = await Resource.find({ 'tags.key': { $all: keys } })
                        .exec()
                }
                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources with those tags/values', 404)
                }
                return new SelidoResponse(action, success, 'Found resource(s)', 200, prettyConvert(resources, true))
            }
            // One of the tags or keys has to match
            else {
                let to_find = []
                let i = 0
                // Creates a list of objects (e.g. [{tags: {key: 'foo', value: 'bar'}}, {tags: {key: 'a', value: 'b'}}])
                // from the tags sent in, so that mongo can filter on only some of them
                tags.forEach(tag => {
                    to_find[i] = { tags: tag }
                    i++
                })
                var resources;
                if (tags.length > 0 && keys.length > 0) {
                    // Jank shit incoming
                    let resources_keys = await Resource.find({ 'tags.key': { $in: keys } })
                        .exec()
                    resources = resources_keys
                    let resources_tags = await Resource.find({ $or: to_find })
                        .exec()
                    resources_tags.forEach(res => {
                        resources.push(res)
                    })
                    // This is what I wanna do, no idea why it doesnt work..
                    // resources = await Resource.find({ $or: [{ 'tags.key': { $in: keys }, $or: to_find }] })
                    //     .exec()
                }
                // Just tag search
                else if (tags.length > 0) {
                    resources = await Resource.find({ $or: to_find })
                        .exec()
                }
                // Just keys
                else {
                    resources = await Resource.find({ 'tags.key': { $in: keys } })
                        .exec()
                }

                if (resources.length == 0) {
                    return new SelidoResponse(action, failed, 'No resources with those tags/values', 404)
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
        if (this.verbosity && !this.quiet) {
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

function findValidIds(ids) {
    let valid_ids = []
    ids.forEach(id => {
        if (id.match(/^[0-9a-fA-F]{24}$/)) {
            valid_ids.push(id)
        }
    })
    return valid_ids
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