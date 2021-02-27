const MongoClient = require('mongodb').MongoClient;
const assert = require('assert');

// Connection URL
const url = 'mongodb://mongo:27017';

// Database Name
const dbName = 'myproject';

// Use connect method to connect to the server
// MongoClient.connect(url, function(err, client) {
//   console.log(err);
//   console.log("Connected successfully to server");

//   const db = client.db(dbName);

//   insertDocuments(db, function() {
//     findDocuments(db, function() {
//       client.close();
//     });
//   });
// });

// const findDocuments = function(db, callback) {
//   // Get the documents collection
//   const collection = db.collection('documents');
//   // Find some documents
//   collection.find({}).toArray(function(err, docs) {
//     assert.equal(err, null);
//     console.log("Found the following records");
//     console.log(docs)
//     callback(docs);
//   });
// }

// const insertDocuments = function(db, callback) {
//   // Get the documents collection
//   const collection = db.collection('documents');
//   // Insert some documents
//   collection.insertMany([
//     {a : 1}, {a : 2}, {a : 3}
//   ], function(err, result) {
//     assert.equal(err, null);
//     assert.equal(3, result.result.n);
//     assert.equal(3, result.ops.length);
//     console.log("Inserted 3 documents into the collection");
//     callback(result);
//   });
// }