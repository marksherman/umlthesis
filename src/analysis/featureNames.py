# Extractable Features,
# name of field in commit JSON that will hold all feature data
featureExtractionResults = 'features'
# Tests:
#   whichMapsisBlockPresent (str blockID, list|dict IDmaps)
#       for a list|map of IDmaps, returns list of which maps contain given block
#       Can be used to identify when a block appears or disappears in a history
################################################################################
#   checkForDeletedAddedBlocks (treeroot A, treeroot B)
#       returns list of blocks that were deleted from A to B
#           and list of blocks that werer added from A to B
blocksDeletedFlag = 'blocksDeletedFlag'
blocksDeletedList = 'blocksDeletedList'
blocksAddedFlag = 'blocksAddedFlag'
blocksAddedList = 'blocksAddedList'
#   checkForMovedBlocks (IDmap A, IDmap B)
blocksMovedInSpaceFlag = 'blocksMovedInSpaceFlag'
blocksMovedInSpaceList = 'blocksMovedInSpaceList'
#   checkForContextMove (IDmap A, IDmap B, parentMap A, parentMap B)
blocksMovedContextFlag = 'blocksMovedContextFlag'
blocksMovedContextList = 'blocksMovedContextList'
#   checkForChangedBlocks (IDmap A, IDmap B)
blocksChangedFlag = 'blocksChangedFlag'
blocksChangedList = 'blocksChangedList'
#   checkForFieldChanges (IDmap A, IDmap B)
blocksFieldsChangedFlag = 'blocksFieldsChangedFlag'
blocksFieldsChangedList = 'blocksFieldsChangedList'
#   lists for reference
allFlags = [blocksDeletedFlag, blocksAddedFlag,
            blocksMovedInSpaceFlag, blocksMovedContextFlag,
            blocksFieldsChangedFlag, blocksChangedFlag]
################################################################################
#   isBlockTopLevel (block)
#       True: block has x and y parameters indicating it is on the workspace and not nested
#   didThisBlockMoveinSpace (block A, block B)
#       True: block is top-level and moved on workpace
#       True: block was moved in or out of top-level (in/out of being nested)
#       False: block is top level and coordinates did not change
#       False: block is nested and stayed as such (though parent may have moved)
#   didThisBlockChange (block A, block B)
#       True: any parameter(s) of the block changed from A to B
#       Ignores x/y position data, as this is tested by MoveinSpace
#   didThisBlocksFieldsChange (block A, block B)
#       Can be used to detect text changes (text blocks, variable names, etc)
#       True: block has at least one field, and the text of a field changed
#       False: no fields, or all fields stayed the same
################################################################################
# names of the fields to be printed in the CSV export
exportFields = [
    'username', 'date', 'seconds_elapsed', 'hash',
    blocksAddedFlag, blocksAddedList,
    blocksDeletedFlag, blocksDeletedList,
    blocksMovedInSpaceFlag, blocksMovedInSpaceList,
    blocksMovedContextFlag, blocksMovedContextList,
    blocksFieldsChangedFlag, blocksFieldsChangedList,
    blocksChangedFlag, blocksChangedList]
exportFieldsDiff = [
    'username', 'date', 'seconds_elapsed', 'hash',
    blocksFieldsChangedFlag, blocksFieldsChangedList,
    'diff',
    blocksAddedFlag, blocksAddedList,
    blocksDeletedFlag, blocksDeletedList,
    blocksMovedInSpaceFlag, blocksMovedInSpaceList,
    blocksMovedContextFlag, blocksMovedContextList,
    blocksChangedFlag, blocksChangedList]
