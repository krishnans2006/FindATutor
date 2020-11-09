#!/bin/bash

# This assumes you've created a virtual environment and installed Gunicorn
# See the docs for instructions

cd /site/public

source venv/bin/activate

# Flask
gunicorn server:app -b 0.0.0.0:80 -w 1
# Django (replace <name> with the name of your application)
# gunicorn <name>.wsgi -b $HOST:$PORT -w 1
