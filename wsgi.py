#!/usr/bin/env python

import sys
import site

site.addsitedir('/var/www/mydefensiblespace.org/html/lib/python3.6/site-packages')
# site.addsitedir('/var/www/hitme/lib/python3.6/site-packages')

sys.path.insert(0, '/var/www/mydefensiblespace.org/html')

from templates import app as application
