#!/bin/bash

# Script to optimize the collection of git repos that makes up the userFiles datastore.
# Run this after significant use to free up disk space and inode file handles. 

# set GC_METHOD to the name of the function to run in each git repo. 
# different methods exist, so this makes it easy to try things.
GC_METHOD=git_linus

function git_gc1 {
	git gc --aggressive --prune=all
        git repack -Ad
        git prune
}

function git_linus {
	# As proposed by Linus himself: http://stackoverflow.com/questions/28720151/git-gc-aggressive-vs-git-repack
	git repack -a -d -f --depth=250 --window=250
}
 
cd userFiles
D=`pwd`
echo $D
for dir in *; do
	echo $D/$dir
	cd $D/$dir
	for gitdir in *.git; do
		echo $gitdir
		cd $D/$dir/$gitdir
		# in the gir directory, do the gc command
		$GC_METHOD
	done
	cd $D
done

