#!/bin/bash

cd /site/public
source venv/bin/activate

git add --all
git commit -m 'Committed automatically by run.sh'
git remote set-url origin https://KrishnanS2006@github.com/KrishnanS2006/FindATutor.git
git push

gunicorn server:app -b 0.0.0.0:80 -w 1
