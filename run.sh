#!/bin/bash

cd /site/public
source venv/bin/activate


git add --all
git commit -m 'Committed automatically by run.sh'
git push git@github.com:KrishnanS2006/FindATutor.git master

gunicorn server:app -b 0.0.0.0:80 -w 1
