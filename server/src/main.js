const log = require('./logger/log.js');
const db = require('./db/db.js');

var express = require('express');
var app = express();

const PORT = 3912;

app.get('/', function (req, res) {
  res.send('Hello World!');
});

app.listen(PORT, function () {
  log.info('Example app listening on port ' + PORT);
});
