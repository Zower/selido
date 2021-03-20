'use strict'

module.exports = class SelidoResponse {
    constructor(action, status, message, code = 500, objects) {
        this.action = action
        this.status = status
        this.code = code
        this.message = message
        this.objects = objects
        this.time = Date.now()
    }
}