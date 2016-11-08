'use strict';

goog.provide('Blockly.Playback');

Blockly.Playback.start = function (filename){
    var history = [];
    var length = 0;
    var current = 0;

    var injectBlocks = function (blocksXML){
        Blockly.mainWorkspace.clear(); // Remove any existing blocks before we add new ones.
        Blockly.Xml.domToWorkspace(Blockly.mainWorkspace, Blockly.Xml.textToDom(blocksXML));
    };

    var load = function (framenum){
        if (framenum <= length && framenum > 0) {
            injectBlocks(history[framenum - 1]['contents']['Screen1/blocks']);
            current = framenum;
        }
        console.log("Frame " + current + " of " + length + "   time: " + history[framenum - 1]['seconds_elapsed']);
    };

    var loadProjectFile = function (){
        fetch("http://localhost:8000/" + filename)
            .then(function(result){return result.json();})
            .then(function(jsontext){
                history = jsontext;
                length = history.length;
                load(1);
            });
    };

    loadProjectFile();

    return {
        length: function () { return length },
        load: load,
        next: function () { load( current + 1 ) },
        prev: function () { load( current - 1 ) }
    };

};
