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

import Interface

class WikiParserInterface(Interface.Base):
    """Define an interface for all wiki parser.
    """

    def parseContent(content, wiki):
        """Return the render of the provided content along with references on
        the linked pages and potentially linked pages.
        """

    def getId():
        """Return a parser unique ID.
        """

class IWikiTag(Interface.Base):
    """ let the user extends the tags parsed
    by providing bracketed content

    for example [id:*anything*] will be sent to
    the right wikitag with the *anything* value
    """

    def getTagId():
        """ returns the id of the tage """

    def render(context, parameters):
        """ gets what's inside the brackets and return
        what has to be displayed, given a context
        """

    def canHandle(parser):
        """ returns true if it's compatible with the given parser """

    def getHelp():
        """ returns translatable text, that can be used to display
        syntax help"""
