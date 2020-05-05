git checkout -b $1
git fetch upstream
git revert --hard upstream/master
