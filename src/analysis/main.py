import xml_analyze as xml
import gitfilter as git
import featureNames as names
import csv
import pickle
import json

# For description of extractable features and tests, see featureNames.py
def extractChanges(prevChange, curChange):
    '''Extract features of the current changes relative to its predecessor change.
    prev|curChange must be commit objects with etree, IDmap, and parentmap fields.
    Result: adds result data to the commit object curChange.'''
    features = {}

    curChange['diff'] = xml.getBlocksDiff(prevChange, curChange)

    da = xml.checkForDeletedAddedBlocks(prevChange['etree'], curChange['etree'])
    if len(da[0]) == 0:
        features[names.blocksDeletedFlag] = False
    else:
        features[names.blocksDeletedFlag] = True
        features[names.blocksDeletedList] = da[0]
    if len(da[1]) == 0:
        features[names.blocksAddedFlag] = False
    else:
        features[names.blocksAddedFlag] = True
        features[names.blocksAddedList] = da[1]

    moved = xml.checkForMovedBlocks(prevChange['IDmap'], curChange['IDmap'])
    if len(moved) == 0:
        features[names.blocksMovedInSpaceFlag] = False
    else:
        features[names.blocksMovedInSpaceFlag] = True
        features[names.blocksMovedInSpaceList] = moved

    context = xml.checkForContextMove(prevChange['IDmap'], curChange['IDmap'], prevChange['parentmap'], curChange['parentmap'])
    if len(context) == 0:
        features[names.blocksMovedContextFlag] = False
    else:
        features[names.blocksMovedContextFlag] = True
        features[names.blocksMovedContextList] = context

    changed = xml.checkForChangedBlocks(prevChange['IDmap'], curChange['IDmap'])
    if len(changed) == 0:
        features[names.blocksChangedFlag] = False
    else:
        features[names.blocksChangedFlag] = True
        features[names.blocksChangedList] = changed

    fields = xml.checkForFieldChanges(prevChange['IDmap'], curChange['IDmap'])
    if len(fields) == 0:
        features[names.blocksFieldsChangedFlag] = False
    else:
        features[names.blocksFieldsChangedFlag] = True
        features[names.blocksFieldsChangedList] = fields

    curChange[names.featureExtractionResults] = features

def intersect(list1, list2):
    return list(set(list1) & set(list2))

listMultipleFieldChanges = []
def printCommitReference(msg, commit):
    se = ' '
    #print(msg)
    if( commit.get('seconds_elapsed') ):
        se = se + str(commit['seconds_elapsed']) + ' '
    print(commit['dir'] + ' ' + commit['date'] + se + commit['hash'])
    listMultipleFieldChanges.append(commit)

def reduceFieldChangesF(changes):
    'Functional wrapper for reduceFieldChanges. Returns a new list of changes.'
    new_changes = changes.copy()
    reduceFieldChanges(new_changes)
    return new_changes

def reduceFieldChanges(changes):
    '''Reduces char-by-char field changes into a single change.
    Operates on a list of changes, and modifies that list in place.
    This would run on the return value from processProject.
    Returns nothing, as changes are made in the argument itself.'''

    changesToDelete = []
    prevFlag = False
    prevList = []
    prevChange = {'date': '0'}
    for thisChange in changes:
        thisFlag = False
        thisList = []
        if thisChange.get(names.featureExtractionResults):
            feat = thisChange[names.featureExtractionResults]
            thisFlag = feat[names.blocksFieldsChangedFlag]
        if thisFlag:
            thisList = feat[names.blocksFieldsChangedList]
        #TODO WARNING disabled test for multiple changes. Will create slighly wrong data. PRELIM TESTING ONLY!
        TurnOnMultipleChangesTestMustBeTrue = False
        if(TurnOnMultipleChangesTestMustBeTrue and (len(thisList) > 1)):
            printCommitReference('Multiple field changes in this commit: ', thisChange)
        else:
            if prevFlag and thisFlag and intersect(prevList, thisList):
                #print('Same field change detected. Deleted: ' + prevChange['date'])
                changesToDelete.append(prevChange)

        prevFlag = thisFlag
        prevList = thisList
        prevChange = thisChange

    for c in changesToDelete:
        changes.remove(c)

def processProject(projFolder):
    "Extracts features from all commits of a project."
    changes = git.listCommits(projFolder)
    user = projFolder.split('/')[-2]
    start_time = int(changes[0]['date_unix'])
    # run through all commit objects, loading their contents into them
    changesToDelete = []
    for c in changes:
        if xml.loadChangeContents(c, user, start_time):
            changesToDelete.append(c)
    # remove commits that had empty blocks (corruption mitigation)
    for c in changesToDelete:
        changes.remove(c)
        print('\nRemoved due to empty blocks file:\n' + user + ' ' + str(c))
    # run the extractor
    for prev, cur in zip(changes[:-1], changes[1:]):
        extractChanges(prev, cur)
    # reduce text field changes to their final state
    #reduceFieldChanges(changes)

    return changes

def countChangeFlags(changes, flag):
    count = 0
    for change in changes:
        if change.get(names.featureExtractionResults):
            if change[names.featureExtractionResults][flag]:
                count = count + 1
    return count

def countAllChangeFlags(changes):
    flagCounts = {}
    for flag in names.allFlags:
        flagCounts[flag] = countChangeFlags(changes, flag)
    flagCounts['allChanges'] = len(changes)
    return flagCounts

def combineLines(textList):
    'Takes a list of strings and concatenates them as lines in a single text.'
    bulk = ''
    for l in textList:
        bulk = bulk + l + '\n'
    return bulk

def constructPrint(commit):
    "Constructs a dictionary of data to be printed to file"
    c = {}
    if 'features' in commit:
        c = commit['features'].copy()
    c['date'] = commit['date']
    c['seconds_elapsed'] = commit['seconds_elapsed']
    c['hash'] = commit['hash']
    c['username'] = commit['username']
    if 'diff' in commit:
        c['diff'] = combineLines(commit['diff'])
    return c

def printCSV(changes, filename, diff=True):
    "Prints data to a CSV file."
    changeList = []
    if diff:
        fieldsToExport = names.exportFieldsDiff
    else:
        fieldsToExport = names.exportFields

    # Flatten changes if it is a list of lists
    if isinstance(changes[0], list):
        changeList = [c for sublist in changes for c in sublist]
    else:
        changeList = changes
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldsToExport)
        writer.writeheader()
        for c in changeList:
            writer.writerow(constructPrint(c))

def exportJSONforPlayback(changes, filename):
    """Prints a set of changes to a JSON file for import into App Inventor playback."""
    data = [{k: v for (k, v) in c.items() if k in ['seconds_elapsed', 'dir', 'date', 'contents']} for c in changes]

    with open(filename, 'w') as file:
        json.dump(data, file)

def saveVar(variable, name):
    with open(name + '.pickle', 'wb') as f:
        pickle.dump(variable, f)

def restoreVar(name):
    print("Restoring " + name + " data...")
    with open(name + '.pickle', 'rb') as f:
        p = pickle.load(f)
    return p
### Start here! ###

#AllDebugProjects = git.filterAllProjectsIn('userFiles', git.isDebuggingActivity)
AllDebugProjects = restoreVar('AllDebugProjects')
allp = []
#allp = [processProject(p) for p in AllDebugProjects]

# How to restore allp quickly:
allp = restoreVar('allp')
allp_reduced = restoreVar('allp_reduced')

#AllTemperatureProjects = git.filterAllProjectsIn('userFiles', git.isTemperatureActivity)
# temperature n = 35! really?

testProjFolder = AllDebugProjects[0]
testProjFolder2 = '/Users/mark/android/snapshot-service-data/userFiles/CalgaryHyena/CSPathwaysDebuggingActivity#5196459188158464.git'
# Folder 3 has nearly 30% flagged commits with multiple field changes at the same time. Oy vey.
testProjFolder3 = '/Users/mark/android/snapshot-service-data/userFiles/VaranasiOstrich/CSPathwaysDebuggingActivity#6214707618775040.git'

#print('processing ' + testProjFolder3)
#commits = processProject(testProjFolder3)
#c2 = processProject(AllDebugProjects[1])
# p = processProject('userFiles/ChongjuOwl/CSPathwaysDebuggingActivity#5652383656837120.git')

# # some test data...
# # b60 -> b61 text block that doesn't change
# # b30 -> b31 text block that DOES change
# # from IDmaps[0|1]['6'|'3']
# # useful: b10 -> b11 because it has many sub-properties
# b60 = IDmaps[0]['6']
# b61 = IDmaps[1]['6']
# b30 = IDmaps[0]['3']
# b31 = IDmaps[1]['3']
# b10 = IDmaps[0]['1']
# b11 = IDmaps[1]['1']
# # 29-30 id 6 DELETES
# b629 = IDmaps[29]['6']
# # 31-32 ID 3 MOVES
# b330 = IDmaps[31]['3']
# b331 = IDmaps[32]['3']
