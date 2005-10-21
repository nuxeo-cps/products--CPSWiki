# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziadé <tz@nuxeo.com>
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
# $Id:$
from cStringIO import StringIO
from Products.CMFCore.utils import getToolByName

from wikiparserinterface import IWikiTag
from wikitags import registerTag
from colorize import Parser

class PythonCodeColorizer:
    """" usage: code:the code
        renders a colorized code
    """
    __implements__ = (IWikiTag,)

    def getTagId(self):
        return 'pycode'

    def render(self, context, parameters):
        result = StringIO()
        Parser(parameters, result).format()
        result.seek(0)
        return ''.join(result.readlines())

    def canHandle(self, parser):
        return parser != 'restructuredtext'

    def getHelp(self):
        """ returns help """
        return 'cpswiki_pycode_help'

    def __str__(self):
        return self.getHelp()

registerTag(PythonCodeColorizer())
