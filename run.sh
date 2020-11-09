#!/bin/bash
cd /site/public
source venv/bin/activate
git commit -a --allow-empty-message -m ''
git push
gunicorn server:app -b 0.0.0.0:80 -w 1
