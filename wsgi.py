# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys
import os
from dotenv import load_dotenv

load_dotenv()
# add your project directory to the sys.path
PATH = os.environ.get('PATH')
if PATH not in sys.path:
    sys.path.insert(0, PATH)

# import flask app but need to call it "application" for WSGI to work
from caccometro import app as application