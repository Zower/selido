'use strict'
const mongoose = require('mongoose')

var resourceSchema = mongoose.Schema({
    name: String,
    tags: [
        {
            key: {
                type: String,
                required: true,
            },
            value: String,
            _id: false
        }
    ],
})

var Resource = mongoose.model('Resource', resourceSchema)

module.exports = Resource