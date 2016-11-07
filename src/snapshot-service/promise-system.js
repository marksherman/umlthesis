/**
 * Author: Mark Sherman <msherman@cs.uml.edu>
 * Part of snapshot-service, by Mark Sherman
 *
 * This file is a Promises port of liberated-system.js by Derrell Lipman,
 * Copyright (c) 2014, 2016 Derrell Lipman
 *
 * License:
 *   Apache : http://www.apache.org/licenses/LICENSE-2.0.txt
 */

/*
 * This is an npm adaptation of the System module from Liberated
 * Derrell Lipman, 2016
 */

var fs = require("fs");

/**
* Read a file and return its data
*
* @param filename {String}
*   The full or relative path to the file.
*
* @param options {Map?}
*   Options for reading from the file. The available options are:
*     encoding - The data is read as/converted to the specified
*                encoding (defaults to "utf8")
*
* @return promise {String}
*   The data read from the file.
*/
var readFile = function(filename, options)
{
  return new Promise(function(resolve, reject)
  {
    // If no options were specified...
    if (! options)
    {
      // ... then create an empty options map
      options = {};
    }

    // Set default options
    options.encoding = options.encoding || "utf8";

    // Read the file data
    fs.readFile(
      filename,
      options,
      function(error, data)
      {
        if (error)
        {
          reject(error);
        }
        else
        {
          // Convert data from "buffer" format into a string
          resolve(data.toString());
        }
      });
  });
};


/**
 * Write data to a file
 *
 * @param filename {String}
 *   The name of the file to be written to
 *
 * @param data {String}
 *   The data to be written to the file
 *
 * @param options {Map?}
 *   A map of options, any of which may be omitted:
 *
 *     encoding {String}
 *       The encoding to use writing to the file. (default: "utf8")
 *
 *     mode {Number}
 *       The file creation mode. (default: 0666)
 *
 *     flag {String}
 *       The method of writing to the file, "w" to truncate then write;
 *       "a" to append. (default: "w")
 *
 * @return promise {}
 *   Resolves with no data on success.
*/
var writeFile = function(filename, data, options)
{
  return new Promise(function(resolve, reject)
  {
    // If no options were specified...
    if (! options)
    {
      // ... then create an empty options map
      options = {};
    }
    // Set default options
    options.encoding = options.encoding || "utf8";
    options.mode = options.mode || 0666;
    options.flag = options.flag || "w";

    // Write the file data!
    fs.writeFile(
      filename,
      data,
      options,
      function(error)
      {
        // File data was written if error is null
        if (error === null){
          resolve();
        } else {
          reject(error);
        }
      });
    });
  };


/**
 * Rename a file.
 *
 * @param oldName {String}
 *   The existing name of the file.
 *
 * @param newName {String}
 *   The name to move the file to.
 *
 * @return promise {}
 *   Resolves with no data on success.
*/
var rename = function(oldName, newName)
{
  return new Promise(function(resolve, reject)
  {
    fs.rename(
      oldName,
      newName,
      function(error)
      {
        // File was renamed if error is null
        if (error === null){
          resolve();
        } else {
          reject(error);
        }
      });
  });
};

/**
 * Read a directory and retrieve its constituent files/directories
 *
 * @param directory {String}
 *   The name of the directory to be read
 *
 * @param callback {Function}
 *   Callback function. Arguments to function:
 *      error {Error|null}
 *      files {Array}
 *
 *   If the specified directory name exists and is a directory, the
 *   returned array will be the list of files and directories found
 *   therein. Otherwise, null is returned.
 *
 * @return promise {Array}
 *   Array will be the list of files and directories found
 *   in the specified directory.
*/
var readdir = function(directory)
{
  return new Promise(function(resolve, reject)
  {
    fs.readdir(
      directory,
      function(error, files)
      {
        if (error === null){
          resolve(files);
        } else {
          reject(error);
        }
      });
  });
};


/**
 * Execute a system command.
 * Note: does NOT use a shell, so shell expansions and wildcards don't work.
 *
 * @param cmd {Array}
 *   The command to be executed, as an array of the individual
 *   arguments, a la "argv"
 *
 * @param options {Map?}
 *   A map of options, any of which may be excluded. The options are:
 *
 *     cwd {String}
 *       The directory in which the command should be executed
 *
 *     showStdout {Boolean}
 *       If true, display any stdout output
 *
 *     showStderr {Boolean}
 *       If true, display any stderr output
 *
 * @return promise {Map}
 *   The data returned map has three members:
 *
 *     exitCode {Number/Error}
 *       0 upon successful termination of the specified command;
 *       Error object otherwise.
 *
 *     stdout {String}
 *       The standard output of the program. This may be undefined or
 *       null if exitCode was non-zero
 *
 *     stderr {String}
 *       The standard error output of the program. This may be undefined
 *       or null if exitCode was non-zero.
 *
 *  This map is always returned, in both resolve and reject.
 */

 var system = function(cmd, options)
 {
   return new Promise(function(resolve, reject)
   {
     var             args;
     var             localOptions = {};
     var             execFile = require("child_process").execFile;

     // If no options were specified...
     if (! options)
     {
       // ... then create an empty options map
       options = {};
     }

     // Separate the arguments from the command name
     args = cmd.slice(1);
     cmd = cmd[0];

     // Save the local options, and strip them from the options map to be
     // passed to exec
     [
       "showStdout",
       "showStderr"
     ].forEach(
       function(opt)
       {
         localOptions[opt] = options[opt];
         delete options[opt];
       });


       var             child;

       child = execFile(
         cmd,
         args,
         options,
         function(err, stdout, stderr)
         {
           // If we were asked to display stdout...
           if (localOptions.showStdout && stdout.toString().length > 0)
           {
             console.log("STDOUT: " + stdout);
           }

           // Similarly for stderr...
           if (localOptions.showStderr && stderr.toString().length > 0)
           {
             console.log("STDERR: " + stderr);
           }

           var data =
           {
             exitCode : err === null ? 0 : err,
             stdout   : stdout,
             stderr   : stderr
           };

           if (err === null){
             resolve(data);
           } else {
             reject(data);
           }

         });
       });
     };


module.exports =
{
 readFile   : readFile,
 writeFile  : writeFile,
 rename     : rename,
 readdir    : readdir,
 system     : system
};
