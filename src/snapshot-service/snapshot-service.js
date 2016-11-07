/**
 * Author: Mark Sherman <msherman@cs.uml.edu>
 *
 * Copyright 2015 Mark Sherman
 *
 * License:
 *   Apache : http://www.apache.org/licenses/LICENSE-2.0.txt
 */

var rpc = require('jrpc2');
var express = require('express');
var cors = require('cors');
var app = express();
var rpcServer = new rpc.Server();
var Log = require('./loglevel.js')();

app.use(cors());

rpcServer.loadModules(__dirname + '/rpc_modules/', function () {
  app.post('/v1.0', rpc.middleware(rpcServer));
  app.listen(8000, function() {
    Log.log("server running from " + __dirname);
  });
});

rpcServer.expose('sayHello',function(){
  return Promise.resolve("Hello!");
});
