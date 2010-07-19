# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# M.-A. Darche <madarche@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

import zLOG
from zLOG import LOG, TRACE, DEBUG, INFO, PROBLEM, ERROR

from Testing.ZopeTestCase import ZopeTestCase

class WikiTestCase(ZopeTestCase):

    def printLogErrors(self, min_severity=INFO):
        """Print out the log output on the console.
        """
        if hasattr(zLOG, 'old_log_write'):
            return
        def log_write(subsystem, severity, summary, detail, error,
                      PROBLEM=PROBLEM, min_severity=min_severity):
            if severity >= min_severity:
                print "\n%s(%s): %s %s" % (subsystem, severity, summary, detail)
        zLOG.old_log_write = zLOG.log_write
        zLOG.log_write = log_write

    def _setup(self):
        ZopeTestCase._setup(self)
        # Override _setup, setUp is not supposed to be overriden
        # Setting up the printing of the log traces
        #self.printLogErrors(TRACE)
        self.printLogErrors(ERROR)

    def _getCurrentUser(self):
        return 'the user'

    def _getCurrentUser2(self):
        return 'the second user'
