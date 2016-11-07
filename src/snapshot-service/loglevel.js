/**
 * Author: Mark Sherman <msherman@cs.uml.edu>
 *
 * Copyright 2015 Mark Sherman
 *
 * License:
 *   Apache : http://www.apache.org/licenses/LICENSE-2.0.txt
 * Set a flag to true to make that category print to console.
 * Flags can be passed as an option object at invocation.
 * See defaults object below.
 */
var _ = require('lodash');

var defaults = {
  log_error: true,
  log_utility: true,
  log_debug: true
};

var silent_function     = function() { };

module.exports = function(opts) {
  var options = _.extend({}, defaults, opts);
  var exports = {};

  exports.error   = options.log_error   ? console.error  : silent_function;
  exports.log     = options.log_utility ? console.log    : silent_function;
  exports.debug   = options.log_debug   ? console.log    : silent_function;

  exports.silent = silent_function;

  return exports;
};
