#!/usr/bin/env python
"""FutAmigo WSGI entry point for production deployment"""

import os
import sys

# Add the project directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bolao_brasileirao.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()