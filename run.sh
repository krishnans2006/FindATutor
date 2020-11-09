#!/bin/bash

cd /site/public
source venv/bin/activate

git add *
git add .
git commit -m 'Committed automatically by run.sh'
git push

gunicorn server:app -b 0.0.0.0:80 -w 1
