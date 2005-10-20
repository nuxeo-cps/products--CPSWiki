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
from Products.CMFCore.utils import getToolByName

from wikiparserinterface import IWikiTag
from wikitags import registerTag

class MemberInfos:
    """" usage: [member:member id, text]
        renders a link to member's directory entry
        if text is given, it's used to be displayed in the link

        example: [member:tarek, Tarek Ziadé]
    """
    __implements__ = (IWikiTag,)

    def getTagId(self):
        return 'member'

    def render(self, context, parameters):
        portalurl = getToolByName(context, 'portal_url').getPortalPath()
        splited = parameters.split(',')
        member_id = splited[0].strip()
        if member_id == '':
            return parameters

        if len(splited) > 1:
            text = splited[1]
        else:
            text = member_id
        link = '%s/cpsdirectory_entry_view?dirname=members&id=%s' \
            % (portalurl, member_id)
        return '<a href="%s">%s</a>' % (link, text.strip())

    def canHandle(self, parser):
        return True

    def getHelp(self):
        """ returns help """
        return 'cpswiki_member_help'

    def __str__(self):
        return self.getHelp()

registerTag(MemberInfos())
