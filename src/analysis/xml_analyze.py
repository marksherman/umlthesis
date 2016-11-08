# https://docs.python.org/3/library/xml.etree.elementtree.html

import xml.etree.ElementTree as ET
import gitfilter as git
import difflib

BLOCK = '{http://www.w3.org/1999/xhtml}block'
ROOT = '{http://www.w3.org/1999/xhtml}xml'

ns = '{http://www.w3.org/1999/xhtml}'

def dens(tag):
    "De-namespace- removes the namespace prefix from a tag"
    return tag.split(ns)[1]

def listToMap(ls):
    "takes a list and converts it to a map where keys are the list indices"
    return dict(zip(range(len(ls)), ls))

# similar is root1.findall('./{http://www.w3.org/1999/xhtml}block')
# but findall lets you filter node tags, in this case for blocks, ignoring the ya version node
def printChildren(treeroot):
    for child in treeroot:
        print(dens(child.tag), child.attrib)

def printAllBlocks(treeroot):
    for block in treeroot.iter(BLOCK):
        print(block.get('id'), block.tag, block.attrib)

def listAllBlocks(treeroot):
    return [block for block in treeroot.iter(BLOCK)]
    # if you don't need filtering, just use list(treeroot)

def printBlockTree(treeroot):
    def printblock(root, n):
        for child in root:
            space = '   ' * n
            print(n, space, dens(child.tag), child.attrib)
            printblock(child, n + 1)

    printblock(treeroot, 0)

def makeParentMap(treeroot):
    "Returns a map of all nodes -> their parent node"
    return {c:p for p in treeroot.iter() for c in p}

def makeIDtoBlockMap(treeroot):
    "Returns a map of block ID numbers -> block elements. (Only block-type nodes have IDs)"
    return {block.get('id'):block for block in treeroot.iter(BLOCK)}

def findParentBlock(element, parentMap):
    "Returns parent block OR root element (ROOT) if top level"
    while parentMap[element].tag != BLOCK and parentMap[element].tag != ROOT:
        element = parentMap[element]
    return parentMap[element]

def findParentBlockByID(ID, parentMap, IDmap):
    "Returns parent block OR root element (ROOT) if top level"
    element = IDmap[ID]
    return findParentBlock(element, parentMap)

def whichMapsisBlockPresent(blockID, IDMaps):
    "returns list of which maps contain the given blockID."
    if isinstance(IDMaps, list):
        maps = listToMap(IDMaps)
    else:
        maps = IDMaps

    positiveKeys = []
    for mapKey in maps.keys():
        if blockID in IDMaps[mapKey]:
            positiveKeys.append(mapKey)

    return positiveKeys

def fixTrailingChars(xmlString):
    "Fixes data corruption where exra characters exist beyond the </xml>"
    if not xmlString:
        return xmlString
    end = '</xml>'
    return xmlString.split(end)[0] + end

# function that loads data into a commit to prepare for testing.
def loadChangeContents(commit, username='', start_time=0):
    "Returns True if the commit had empty blocks and should be ignored."
    git.getFileContentsAt(commit)

    ### Corruption Tests ###
    # fix a class of data corruption: appended junk
    commit['contents']['Screen1/blocks'] = fixTrailingChars(commit['contents']['Screen1/blocks'])
    # detect a class of data corruption: empty blocks
    if not commit['contents']['Screen1/blocks']:
        return True
    
    try:
        commit['etree'] = ET.fromstring(commit['contents']['Screen1/blocks'])
    except ET.ParseError:
        print('XML Parser Crash ' + username + ' ' + commit['dir'] + ' ' + commit['hash'] + '\n')
        commit['etree'] = ET.fromstring("<xml><error>XML Parse Failed</error></xml>")
    commit['IDmap'] = makeIDtoBlockMap(commit['etree'])
    commit['parentmap'] = makeParentMap(commit['etree'])
    if username != '':
        commit['username'] = username
    if isinstance(start_time, str):
        start_time = int(start_time)
    if start_time != 0:
        commit['seconds_elapsed'] = int(commit['date_unix']) - start_time
    return False

# functionss to check for specific changes

def isBlockTopLevel(block):
    "Determines if block is top-level on workspace by looking for x/y paramters"
    return ('x' in block.keys()) & ('y' in block.keys())

def sameBlockCheck(blockA, blockB):
    if blockA.get('id') != blockB.get('id'):
        raise Exception("Blocks do not share an id, therefore are not the same block")

def ElementEqual(a, b):
    "Determines if two etree Elements are data-contents equal, ignoring X/Y position"
    #Currently checks tag, attributes. If a field, checks text.

    eq = [True]         # To be accessible in a function. Python scoping is rediculous.
    def check(exp):
        "Updates equal() value based on exp- one False sticks!"
        eq[0] = eq[0] and exp
    def equal():
        "Are the two elements equal?"
        return eq[0]

    # Tags equal
    check(a.tag == b.tag)

    # Take out the x/y coordinates, those are for another test
    a_attrib = {k:a.attrib[k] for k in a.attrib if k != 'x' if k != 'y'}
    b_attrib = {k:b.attrib[k] for k in b.attrib if k != 'x' if k != 'y'}

    for k in a_attrib:
        check(k in b_attrib)
    for k in b_attrib:
        check(k in a_attrib)

    # if tags all align, continue to check values in attrib
    if False == equal():
        return False
    for k in a_attrib:
        check(a_attrib[k] == b_attrib[k])

    if a.tag == ns + 'field':
        check(a.text == b.text)

    return equal()

def commonKeys(map1, map2):
    return list(set([a for a in map1.keys()]) & set([b for b in map2.keys()]))
##########################################################
########  Operates on SAME BLOCK, DIFFERENT TIME  ########

# Returns
#   True: block is top-level and moved on workpace
#   False: block was moved in or out of top-level (in/out of being nested)
#   False: block is top level and coordinates did not change
#   False: block is nested and stayed as such (though parent may have moved)
def didThisBlockMoveinSpace(blockA, blockB):
    "Checks the same block element at two different itmes for motion in space"
    sameBlockCheck(blockA, blockB)
    #isTop* is True if location coordinates are in that block
    isTopA = isBlockTopLevel(blockA)
    isTopB = isBlockTopLevel(blockB)

    if isTopA and isTopB:
        # both are top-level
        return blockA.get('x') != blockB.get('x') or blockA.get('y') != blockB.get('y')
    else:
        # block either is not top level or changed contexts
        return False

def didThisBlockChange(blockA, blockB):
    "True: blockA/B and their child Elements DIFFER, ignoring fields."
    sameBlockCheck(blockA, blockB)

    if ElementEqual(blockA, blockB) == False:
        return True

    # This assumes blocks cannot be direct descendants of other blocks-
    #   which seems to be true as blocks must be plugged into a value socket.
    #   As a result, no filtering for non-block children is performed
    childrenA = [e for e in blockA.findall('*') if e.tag != ns + 'field']
    childrenB = [e for e in blockB.findall('*') if e.tag != ns + 'field']

    if len(childrenA) != len(childrenB):
        return True

    for childA, childB in zip(childrenA, childrenB):
        if ElementEqual(childA, childB) == False:
            return True

    # passed all tests without finding a change, so it must not have changed.
    return False

def didThisBlocksFieldsChange(blockA, blockB):
    "Detect text field changes, whether strings or variable names, etc"
    fieldsA = blockA.findall(ns + 'field')
    fieldsB = blockB.findall(ns + 'field')
    for fA, fB in zip(fieldsA, fieldsB):
        if fA.text != fB.text:
            return True
    return False

#########################################################
########  Operates on SAME TREE, DIFFERENT TIME  ########

def checkForDeletedAddedBlocks(rootA, rootB):
    "Returns lists: deleted and added blocks from A to B."
    iterA = rootA.iter(BLOCK)
    iterB = rootB.iter(BLOCK)
    setA = frozenset([el.get('id') for el in iterA])
    setB = frozenset([el.get('id') for el in iterB])
    deleted = setA.difference(setB)
    added = setB.difference(setA)
    return list(deleted), list(added)

def checkForMovedBlocks(IDmapA, IDmapB):
    "Returns list: blocks that moved in space or context from A to B."
    #only check blocks that exist in both time steps (set intersection)
    blockIDs = commonKeys(IDmapA, IDmapB)
    return [i for i in blockIDs if didThisBlockMoveinSpace(IDmapA[i], IDmapB[i])]

def checkForContextMove(IDmapA, IDmapB, parentMapA, parentMapB):
    "Returns list: blocks that moved in context, having a new parent, from A to B"
    blockIDs = commonKeys(IDmapA, IDmapB)
    # for each ID, get that block, and compare parentmaps
    return [i for i in blockIDs if
        findParentBlockByID(i, parentMapA, IDmapA).get('id') !=
        findParentBlockByID(i, parentMapB, IDmapB).get('id')]

def checkForChangedBlocks(IDmapA, IDmapB):
    "Returns list: blocks that changed (not moved) from A to B, common to A&B"
    blockIDs = commonKeys(IDmapA, IDmapB)
    return [i for i in blockIDs if didThisBlockChange(IDmapA[i], IDmapB[i])]

def checkForFieldChanges(IDmapA, IDmapB):
    "Returns list: blocks whose field(s) changed from A to B, common to A&B"
    blockIDs = commonKeys(IDmapA, IDmapB)
    return [i for i in blockIDs if didThisBlocksFieldsChange(IDmapA[i], IDmapB[i])]

def getBlocksDiff(prevChange, curChange):
    textA = prevChange['contents']['Screen1/blocks'].split('\n')
    textB = curChange['contents']['Screen1/blocks'].split('\n')
    return list(difflib.Differ().compare(textA, textB))

######## Testing Data ########
if __name__ == '__main__':
    # For testing, need to load a bunch of xml files as trees and roots
    filesToLoad = list(range(0,6)) + list(range(16,30))
    def mkFileName(num):
        return 'wroclaw' + str(num) + '.xml'
    roots = {num:ET.parse(mkFileName(num)).getroot() for num in filesToLoad}
    IDmaps = {num:makeIDtoBlockMap(roots[num]) for num in filesToLoad}
    parentmaps = {num:makeParentMap(roots[num]) for num in filesToLoad}

    # these are just to preserve older test code with hard names
    root0 = roots[0]
    root1 = roots[1]
    root17 = roots[17]
    root18 = roots[18]
    root19 = roots[19]

    # Block id#6 in root0 is deeply nested, and pulled out to top-level in root1.
    # The block is then moved back into nested position in root2.
    # #6 is a text block, originally placed in the text-to-speech arg0
    # These variables access these elements for testing.
    b6r0 = root0[1][2][0][2][0]
    b6r1 = root1[2]
