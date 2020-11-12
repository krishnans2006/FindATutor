#!/bin/bash

cd /site/public
source venv/bin/activate

unset GIT_SSH
git config user.name "KrishnanS2006"
git config user.password "KsSh101606"
git remote rm origin
git remote add origin 'git@github.com:KrishnanS2006/FindATutor.git'
git add --all
git commit -m 'Committed automatically by run.sh'
git push

gunicorn server:app -b 0.0.0.0:80 -w 1
