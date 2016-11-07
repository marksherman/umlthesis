/**
 * Author: Mark Sherman <msherman@cs.uml.edu>
 *
 * Copyright 2015 Mark Sherman
 *
 * Functions for saving App Inventor project files and metadata to git.
 *
 * Git commit process based on work of Derrell Lipman:
 *   https://github.com/derrell/LearnCS/blob/master/dbif/source/class/playground/dbif/MFiles.js
 *
 * License:
 *   Apache : http://www.apache.org/licenses/LICENSE-2.0.txt
 */

var _ = require('lodash');
var System = require('./promise-system.js');


var exports = module.exports = {};

module.exports = function (opts) {

  var defaults = {
    log_error: true,
    log_utility: true,
    log_debug: true
  };

  var options = _.extend({}, defaults, opts);

  var Log = require('./loglevel.js')(options);

  // 1 Be sure the file's directory has been created
  exports.mkScreenDir = (screenDir) => {
    return function(){
      Log.debug(Date() + " 1.");
      return System.system(
        [ "mkdir", "-p", screenDir ],
        { showStdout : true }
      );
    };
  };

  // 2,3 Write the blocks/component code to a file in the screen's directory
  exports.writeFile = (screenDir, filename, filecontents) => {
    return function(){
      Log.debug(Date() + " 2/3.");
      return System.writeFile( screenDir + "/" + filename, filecontents);
    };
  };

  // 4 Create the git repository
  exports.createRepo = (gitDir) => {
    return function(){
      Log.debug(Date() + " 4.");
      return System.system([ "git", "init" ],
      {
        cwd        : gitDir,
        showStdout : true
      });
    };
  };

  // 5 Identify the user to git
  exports.setUser = (gitDir, userName) => {
    return function(){
      Log.debug(Date() + " 5.");
      return System.system(
        [ "git", "config", "user.name", userName],
        {
          cwd        : gitDir,
          showStdout : true
        }
      );
    };
  };

  // 6 Identify user's (fake) email to git
  exports.setFakeEmail = (gitDir) => {
    return function(){
      Log.debug(Date() + " 6.");
      return System.system(
        [ "git", "config", "user.email", "anonymous@noplace.at.all"],
        {
          cwd        : gitDir,
          showStdout : true
        }
      );
    };
  };

  // 7 Add files to this git repository
  exports.addFiles = (screenDir, blocksfile, formfile) => {
    return function(){
      Log.debug(Date() + " 7.");
      Log.debug("cwd : " + screenDir);
      Log.debug("files: " + blocksfile + " , " + formfile);
      return System.system(
        [ "git", "add", blocksfile, formfile ],
        {
          cwd        : screenDir,
          showStdout : true
        }
      );
    };
  };

  // 8 Commit files
  exports.commit = (gitDir, detail) => {
    return function(){
      Log.debug(Date() + " 8.");
      return System.system(
        ["git", "commit", "-m", detail, "--"],
        {
          cwd        : gitDir,
          showStdout : true
        }
      );
    };
  };

  // 9 Did the commit succeed?
  // typical result object:
  //    exitCode: 0
  //    stdout
  //    stderr
  exports.afterCommitSucceed = (gitDir, notes) => {
    return function(data){
      Log.debug(Date() + " 9A.");
      if (notes)
      {
        Log.debug(Date() + " 9 Notes.");
        return System.system(
          [ "git", "notes", "append", "-m", notes + "\n-----\n"],
          {
            cwd        : gitDir,
            showStdout : true
          }
        );
      }
      else
      {
        Log.debug(Date() + " 9 No Notes.");
        return Promise.resolve(data); //EXIT POINT
      }
    };
  };

  // internal util: commit detail as notes
  var commitDetailAsNotes = (gitDir, detail, notes) => {
    return function(){
      Log.debug(Date() + " 9F2.");
      return System.system(
        [ "git", "notes", "append", "-m",
          detail + (notes ? "\n" : "\n-----\n")
        ],
        {
          cwd        : gitDir,
          showStdout : true
        }
      );
    };
  };

  var addToNotes = (gitDir, notes) => {
    return function(data){
      if (notes)
      {
        Log.debug(Date() + " 9F3.");

        return System.system(
          ["git", "notes", "append", "-m",
            notes + "\n-----\n"
          ],
          {
            cwd        : gitDir,
            showStdout : true
          }
        );
      }
      else
      {
        return Promise.resolve(data); //EXIT POINT
      }
    };
  };

  // 9F Commit did not succeed.
  // This usually means no files changed, and is ok.
  // Add the commit details to the git notes.
  exports.afterCommitFail = (gitDir, screenDir, blocksfile, formfile, detail, notes) => {
    return function(){
      Log.debug(Date() + " 9F1.");
      return System.system(
        [ "git", "checkout", blocksfile, formfile ],
        {
          cwd        : screenDir,
          showStdout : true
        }
      )
      .then( commitDetailAsNotes(gitDir, detail, notes) )
      .then( addToNotes(gitDir, notes) );
    };
  };


  return exports;
};
