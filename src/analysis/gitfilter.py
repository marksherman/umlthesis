"Tools for analysis of Mark Sherman's snapshot block code data."
import os
import subprocess

# list of users to always ignore in data processing
# used for test data, researcher accounts, etc
ignore_users = []

# reads a file as lines, and takes the first token from that file
# allows for comments to be on any line in the file after white space.
def readFileLines(filename):
    if os.path.isfile(filename):
        with open(filename) as afile:
            datalines = [line.split()[0] for line in afile.readlines()]
        return datalines
    else:
        return []

def writeFileLines(filename, linesList):
    with open(filename, 'w') as afile:
        for line in linesList:
            afile.write(str(line) + '\n')

def convertDateISOtoHuman(ISO):
    '''Converts the ISO format to be SPSS compatible.
    ISO:  yyy-mm-ddThh-mm-ss-TZ:TZ 2016-02-01T08:20:34-05:00
    SPSS: yyyy-mm-dd hh:mm:ss      2016-02-01 08:20:34'''
    ymd, time = ISO.split('T')
    return ymd + ' ' + time.split('-')[0]

# if there is an ignore_users file, read it in and populate the ignore list.
# ignore_users will take the first token on each line as a username.
ignore_users.extend(readFileLines('ignore_users'))

def makeCommit(commit_hash, date_unix, date_ISO, git_dir):
    "Makes a dictionary object representing a single commit."
    return {'hash' : commit_hash,
            'date_unix' : date_unix,
            'date' : convertDateISOtoHuman(date_ISO),
            'dir' : git_dir}

def doGit(cmdList, git_dir):
    gitcmd = cmdList
    gitcmd.insert(0, 'git')
    return subprocess.run(gitcmd, stdout=subprocess.PIPE, cwd=git_dir, universal_newlines=True)

# returns a list of commit objects (just some dictionaries), in order,
# with oldest first, given a git directory.
def listCommits(git_dir):
    "Returns a list of commits from a given git directory."
    checkoutCommit(git_dir, 'master')
    result = doGit(['log', '--reverse', '--format="%H,%ct,%cI"'], git_dir)
    if result.returncode == 0:
        list_of_commits = []
        for commit_line in result.stdout.splitlines():
            lines = commit_line.split(',')
            list_of_commits.append(makeCommit(lines[0].strip('"'), lines[1], lines[2].strip('"'), git_dir))
        return list_of_commits
    else:
        print("Error from git subprocess in listCommits: ", result.returncode)
        return result.returncode

# check out a certain commit
def checkoutCommit(git_dir, commit_obj):
    if commit_obj == 'master':
        githash = 'master'
    else:
        githash = commit_obj['hash']
    return doGit(['checkout', githash, '-q'], git_dir)

# add the blocks and form data for Screen1 to the commit object
def getFileContentsAt(commit_obj):
    "Adds the file contents to the commit object."
    git_dir = commit_obj['dir']
    checkoutCommit(git_dir, commit_obj)
    blocksFilePath = os.path.join(git_dir, 'Screen1/blocks.xml')
    formFilePath = os.path.join(git_dir, 'Screen1/form.json')
    contents = {}
    with open(blocksFilePath) as afile:
        contents['Screen1/blocks'] = afile.read()
    with open(formFilePath) as afile:
        contents['Screen1/form'] = afile.read()
    commit_obj['contents'] = contents

# This global variable holds projects that caused problems during doesFileContain
problem_projects = []

# give it a git folder, and a file within it (relative path), and a string to match
# returns True if string is in file.
# doesFileContain(somegitpath, 'Screen1/form1.json', '"AboutScreen":"MSCSPTemperatureActivity"')
# can be used to filter for specific projects
def doesFileContain(git_dir, file_in_git, string_to_match):
    thisfile = os.path.join(git_dir, file_in_git)
    try:
        file = open(thisfile)
    except OSError:
        problem_projects.append({'attempted':thisfile, 'ls':os.listdir(git_dir)})
        return "Error in doesFileContain tryig to open " + thisfile

    contents = file.read()
    file.close()
    return string_to_match in contents

# test if git repo is MSP Temperature activity
def isTemperatureActivity(git_dir):
    return doesFileContain(git_dir, 'Screen1/form.json', '"AboutScreen":"MSCSPTemperatureActivity"')

# test if a git repo is MSP Debugging activity
def isDebuggingActivity(git_dir):
    return doesFileContain(git_dir, 'Screen1/form.json', '"AboutScreen":"MSDEBUGACTIVITY"')

# Find all users in the database, store as variable users
def isUserDir(basefolder, udir):
    return os.path.isdir(os.path.join(basefolder, udir))

# gets the list of all users in a folder
# Users do have absolute path included.
def getAllUsersIn(folder):
    userFiles = os.path.abspath(folder)
    return [os.path.join(userFiles, user) for user in os.listdir(userFiles) if isUserDir(folder, user) if user not in ignore_users]

# gets all the repositories from a user directory
# user directory must be an absolute path
def getReposFrom(user):
    return [d for d in os.listdir(user)]

# walk through all the users and all of their projects
def filterAllProjectsIn(folder, filterProc):
    "Returns list of all projects that match that satisfied filterProc."
    value = []
    for user in getAllUsersIn(folder):
        dirs_in_user = [os.path.join(user, repo) for repo in getReposFrom(user)]
        for repo in dirs_in_user:
            if filterProc(repo):
                value.append(repo)
    # tests may have found problematic projects, we should check for them.
    # note that this function DOES NOT RESET the problem projects list.
    if len(problem_projects) > 0:
        print(problem_projects)
        print("The above projects gave errors during doesFileContain")

    return value

def printList(data):
    for i in data:
        print(i)

##############################################################################
######### D O   I T ##########################################################
##############################################################################
if __name__ == '__main__':
    # identify repos to analyze
    # repos = filterAllProjectsIn('userFiles', isTemperatureActivity)
    #printList(repos)
    #writeFileLines('temperatureProjects', repos)

    testproject = '/Users/mark/android/snapshot-service-data/userFiles/WroclawRat/CSPathwaysDebuggingActivity#5188696437424128.git'
    commits = listCommits(testproject)
    #printList(commits)
    for commit in commits:
        getFileContentsAt(commit)
    print("----------------AND THEN--------------------")
    print(commits[0]['contents']['Screen1/blocks'])

    ##############################################################################
    if len(problem_projects) > 0:
        print(problem_projects)
        print("The above projects gave errors during doesFileContain")

    # in the git repo!
    #print(subprocess.run(["git", "status"]))
    #print(subprocess.run(["git", "status"], stdout=subprocess.PIPE, cwd=repo_dir, universal_newlines=True).stdout)
    #listCommits(repo_dir)
