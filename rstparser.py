# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
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
#
# $Id$
import re

from wikiparserinterface import WikiParserInterface
from urllib import quote
from baseparser import BaseParser

try:
    from reStructuredText import HTML # import this one first
    rst_available = True
except ImportError:
    rst_available = False

class RstParser(BaseParser):

    __implements__ = (WikiParserInterface, )

    output_encoding = 'iso-8859-15'

    def getId(self):
        return 'restructuredtext'

    def parseContent(self, wiki, content):
        """ parses content """
        if rst_available:
            content = HTML(content, output_encoding=self.output_encoding,
                           initial_header_level=2, report_level=0)

        # called for references
        content = BaseParser.parseContent(self, wiki, content)
        return content
