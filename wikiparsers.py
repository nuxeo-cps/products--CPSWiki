# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziade <tz@nuxeo.com>
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

from baseparser import BaseParser
from wwwparser import WwwParser
from rstparser import RstParser

parsers = ['restructuredtext', 'wikiwikiweb', 'html']

def generateParser(name):
    if name == 'restructuredtext':
        return RstParser()
    elif name == 'wikiwikiweb':
        return WwwParser()
    elif name == 'html':
        # html parser does nothing yet, as epoz does the work
        return BaseParser()
    else:
        return BaseParser()
