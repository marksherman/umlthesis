/**
 * Author: Mark Sherman <msherman@cs.uml.edu>
 *
 * Copyright 2015 Mark Sherman
 *
 * The RPC module that takes file data from the client and files it.
 * The RPC client will call the "log" procedure with one argument-
 *   The one argument is a JSON object of file contents and metadata.
 *
 * Function exports.log must be a procedure that will do the filing.
 * Included are two:
 *  "saveProject" which commits, internally, to git.
 *  "consolelog" for debugging, dumping data to console
 *
 * Git commit process based on work of Derrell Lipman:
 *   https://github.com/derrell/LearnCS/blob/master/dbif/source/class/playground/dbif/MFiles.js
 *
 * License:
 *   Apache : http://www.apache.org/licenses/LICENSE-2.0.txt
 */

var defaults =
{
  "log_debug": false
};
var userdb = require('../userdb.js')();
var Log = require('../loglevel.js')(defaults);
var git = require('../savegit.js')(defaults);

var dumpToFile = true;  // consolelog can optionally dump the received JSON to file
if (dumpToFile) { var fs = require("fs"); }

/**
* Logs a snapshot to console.
* Can be used for debugging, but doesn't actually save anything!
*
* @param metadata {String}
*
* @param projectContents {String}
*
* @return promise {Number/Error}
*   Zero upon success; Error object otherwise
*/
function consolelog (projectData) {

  var data = JSON.parse(projectData);

  if(dumpToFile){
    var filename = __dirname + "/../datadumps/" + "serialized_" + Date.now();
    fs.writeFile(filename, JSON.stringify(data), function(e){
      if(e){
        Log.error("Dump Error: " + e);
        throw e;
      } else {
        Log.debug("Dumped projectData to " + filename);
      }
    });
  }

  return userdb.get_code_name(data.userName)
  .then(function(codename)
  {
    Log.log("\n\n--------------------------------------\n");
    Log.log("Snapshot (" + data.eventType + ") received at " + new Date());
    Log.log("Codename: " + codename);
    Log.log("Sane screenName: " + sanitize(data.screenName) );
    Log.log(data);

    return Promise.resolve("0");
  })
  .catch(function(err)
  {
    Log.error("Error caught from get_code_name in consolelog: " + err);
    return Promise.reject(err);
  });
}

/**
* Save a project - call this one!
* Parses input and anonymizes data, then saves it.
*
* @param metadata {String}
*
* @param projectContents {String}
*
* @return promise {Number/Error}
*   Zero upon success; Error object otherwise
*/
function saveProject (projectData){

  var data = JSON.parse(projectData);

  var userRealName = data.userName;

  return userdb.get_code_name(userRealName)
  .then(function(codename)
  {
    data.userName = codename;
    return saveProjectToGit(data)
    .then(function(){
      return Promise.resolve("0");
    })
    .catch(function(err)
    {
      Log.error("Error caught from saveProjectToGit: " + err);
      return Promise.reject(err);
    });
  })
  .catch(function(err)
  {
    Log.error("Error caught from get_code_name in saveProject: " + err);
    return Promise.reject(err);
  });
}

/**
* Save a program via git.
* DO NOT CALL DIRECTLY - use saveProject
*
* Needs to return a promise that resolves.
* The calling 'saveProject' function will then resolve for the RPC.
*
* Based on _saveProgram, part of LearnCS by Derrell Lipman
* github.com/derrell/LearnCS
*
* @param metadata {Map}
*
* @param projectContents {Map}
*
* @return promise {Number/Error}
*   Zero upon success; Error object otherwise
*/
function saveProjectToGit (projectData)
{
  return new Promise(function(resolve, reject)
  {
    var date = Date();
    Log.log("\nRecieve started " + date);
    // data that becomes a file or directory name must be sanitized
    var userName        = sanitize(projectData.userName);
    var projectName     = sanitize(projectData.projectName);
    var projectId       = sanitize(projectData.projectId);
    var screenName      = sanitize(projectData.screenName);
    var sessionId       = projectData.sessionId;
    var yaversion       = projectData.yaversion;
    var languageVersion = projectData.languageVersion;
    var eventType       = projectData.eventType;
    var sendDate        = projectData.sendDate;

    var detail          = "committed automatically by snapshot server";
    var notes           = "sendDate: " + sendDate + "\n" +
                          "eventType: " + eventType + "\n" +
                          "sessionID: " + sessionId + "\n" +
                          "yaversion: " + yaversion + "\n" +
                          "languageVersion: " + languageVersion;

    var blocks          = projectData.blocks;
    var form            = projectData.form;

    // Create the directory name
    // Format: userFiles/userName/projectName#projectID.git/screen/{files}
    var gitDir = __dirname + "/../userFiles/" + userName + "/" + projectName + "#" + projectId + ".git";
    var screenDir = gitDir + "/" + screenName;

    var blocksfile = "blocks.xml";
    var formfile = "form.json";

    Log.log("Files to commit will be: \n\t" +
      screenDir + "/" + blocksfile + "\n\t" +
      screenDir + "/" + formfile);

    // 1. Be sure the file's directory has been created
    Log.debug(date + " 0");
    return git.mkScreenDir(screenDir)()
      .then( git.writeFile(screenDir, blocksfile, blocks) )
      .then( git.writeFile(screenDir, formfile, form) )
      .then( git.createRepo(gitDir) )
      .then( git.setUser(gitDir, userName) )
      .then( git.setFakeEmail(gitDir) )
      .then( git.addFiles(screenDir, blocksfile, formfile) )
      .catch(
        function(error){
          Log.debug("Error in system calls in saveProjectToGit, prior to commit: " + error);
          reject(error);
        })
      .then( git.commit(gitDir, detail) )
      .then( git.afterCommitSucceed(gitDir, notes),
             git.afterCommitFail(gitDir, screenDir, blocksfile, formfile, detail, notes) )
      // TODO add post-commit options and features, @ MFiles.js:277
      .then(resolve("0"))
      .catch(
        function(error){
          Log.debug("Error in system calls in saveProjectToGit: " + error);
          reject(error);
        });

  });
}

/**
* Sanitize a file name by replacing ".." with "DOTDOT", backslash with
* slash, multiple adjacent slashes with a single slash, and any remaining
* slash with "SLASH".
*
* @author Derrell Lipman
* @param name {String}
*   The file name to be sanitized
*
* @return {String}
*   The sanitized file name
*/
function sanitize (name)
{
  // Remove dangerous ..
  name = name.replace(/\.\./g, "DOTDOT");

  // Replace backslashes with forward slashes
  name = name.replace(/\\/g, "/");

  // Strip any double slashes; replace with single slashes
  name = name.replace(/\/+/g, "/");

  // Replace dangerous slashes
  name = name.replace(/\//g, "SLASH");

  return name;
}

module.exports = {
  log: saveProject
  //log: consolelog
};
