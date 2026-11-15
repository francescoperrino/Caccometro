# WSGI configuration for the hosting: copy this file over the WSGI file the hosting created
# for the web app and set `path` to the folder that holds caccometro.py.

import sys

# Folder of the project, written out: the environment and .env are not loaded yet at this point
path = '/home/<your-username>'
if path not in sys.path:
    sys.path.insert(0, path)

# The hosting looks for a variable named "application"
from caccometro.webhook import app as application
