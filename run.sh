#!/bin/bash

cd /site/public
source venv/bin/activate

unset GIT_SSH
git config user.name 'KrishnanS2006'
git config user.password 'KsSh101606'
git add --all
git commit -m 'Committed automatically by run.sh'
git push 'git@github.com:KrishnanS2006/FindATutor.git'

gunicorn server:app -b 0.0.0.0:80 -w 1
