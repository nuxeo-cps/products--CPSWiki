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
from Globals import Persistent

from ZODB.PersistentList import PersistentList

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.CMFCorePermissions import View, ViewManagementScreens
from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.html import sanitize
from Products.CPSCore.CPSBase import CPSBaseFolder
from Products.CPSCore.CPSBase import CPSBaseDocument

from utils import makeId, getCurrentDateStr
from wikiversionning import VersionContent
from wikipermissions import addWikiPage, deleteWikiPage, viewWikiPage,\
                            editWikiPage

factory_type_information = (
    { 'id': 'CPS Wiki Page',
      'meta_type': 'CPS Wiki Page',
      'description': 'portal_type_CPSWikiPage_description',
      'icon': 'wikipage.png',
      'title': 'portal_type_CPSWikiPage_title',
      'product': 'CPSWiki',
      'factory': 'manage_addWikiPage',
      'immediate_view': 'cps_wiki_pageview',
      'filter_content_types': 0,
      'allowed_content_types': (),
      'allow_discussion': 0,
      'actions': ({'id': 'view',
                   'name': 'action_view',
                   'action': 'cps_wiki_pageview',
                   'permissions': (viewWikiPage,),
                   },
                  {'id': 'edit',
                   'name': 'action_edit',
                   'action': 'cps_wiki_pageedit',
                   'permissions': (editWikiPage,),
                   },
                   {'id': 'history',
                   'name': 'action_history',
                   'action': 'cps_wiki_pagehistory',
                   'permissions': (viewWikiPage,),
                   },
                   {'id': 'delete',
                   'name': 'action_delete',
                   'action': 'deletePage',
                   'permissions': (deleteWikiPage,),
                   },
                   {'id': 'localroles',
                   'name': 'action_local_roles',
                   'action': 'cps_wiki_localrole_form',
                   'permissions': (ViewManagementScreens,)
                   },
                  ),
      'cps_display_as_document_in_listing' : 1,
      },
    )

class ZODBVersionContent(VersionContent):
    """ Overrides all VersionContent read / write
        APIs for Zodb Storage
    """
    def __init__(self, primary, tags={}):
        self.plist = PersistentList()
        self.plist.append((primary, tags))

    def _setContent(self, index, content, tags={}):
        self.plist[index] = (content, tags)

    def _getContent(self, index):
        return self.plist[index]

    def _delContent(self, index):
        if index > 0:
            del self.plist[index]

    def _getHistorySize(self):
        return len(self.plist) - 1

    def _addContent(self, content, tags={}):
        self.plist.append((content, tags))


class WikiPage(CPSBaseFolder):
    """ A persistent WikiPage Page implementation.
        with versionning
    """
    meta_type = "CPS Wiki Page"
    portal_type = meta_type

    _properties = CPSBaseFolder._properties

    def __init__(self, id, source='', **kw):
        CPSBaseFolder.__init__(self, id, **kw)
        initial_tags = self._createVersionTag()
        self.source = ZODBVersionContent(source, initial_tags)

    def _createVersionTag(self):
        tag = {}
        tag['author'] = self._getUserName()
        tag['date'] = getCurrentDateStr()
        return tag

    def _getUserName(self):
        mtool = getToolByName(self, 'portal_membership', None)
        if mtool is None:
            return 'Anonymous'
        else:
            return mtool.getAuthenticatedMember().getUserName()

    def getParent(self):
        return self.aq_inner.aq_parent

    def getParserType(self):
        """ returns parser type """
        wiki = self.getParent()
        return wiki.parser

    def content(self):
        """Render the wiki page source."""
        return self.source.getLastVersion()

    def render(self):
        """Render the wiki page source."""
        result = self.source.getLastVersion()[0]
        result = self.renderLinks(result)
        # adding toolbar
        #result = self.toolbar() + result
        return result

    def editPage(self, title=None, source=None, REQUEST=None):
        """Edits the stuff"""
        if source is not None:
            source = sanitize(source)
            tags = self._createVersionTag()
            self.source.appendVersion(source, tags)
        if title is not None:
            self.title = title
        if REQUEST is not None:
            psm = 'Content changed.'
            REQUEST.RESPONSE.redirect("cps_wiki_pageedit?portal_status_message=%s" % psm)

    def deletePage(self, REQUEST=None):
        """ suicide """
        wiki = self.getParent()
        wiki.deleteWikiPage(self.id, REQUEST)     # need to add a warning here

    def renderLinks(self, content):
        """ creates link with founded [pages] """
        wiki = self.getParent()
        parser = wiki.getParser()
        return parser.parseContent(wiki, content)

    def getAllDiffs(self):
        """ renders a list of differences """
        source = self.source
        version_count = source.getVersionCount()
        versions = []
        for i in range(version_count):
            version = source.getVersion(i)
            tags = version[1]
            versions.append(tags)
        """

        for i in range(version_count-1):
            diff = source.getDifferences(i, i+1)
            versions.append(diff)
        """
        return versions

    def restoreVersion(self, index, REQUEST=None):
        """ restores a previous version """
        self.source.restoreVersion(index)
        if REQUEST is not None:
            psm = 'Version restored.'
            REQUEST.RESPONSE.redirect("cps_wiki_pageview?portal_status_message=%s" % psm)

manage_addWikiPageForm = PageTemplateFile(
    "www/zmi_wikiPageAdd", globals(),
    __name__ = 'manage_addWikiPageForm')

def manage_addWikiPage(self, id, title, REQUEST=None):
    """Add the simple content."""
    ob = WikiPage(id)
    id = self._setObject(id, ob)

    if REQUEST is None:
        return
    try:
        u = self.DestinationURL()
    except:
        u = REQUEST['URL1']
    if REQUEST.has_key('submit_edit'):
        u = "%s/%s" % (u, urllib.quote(id))
    REQUEST.RESPONSE.redirect(u+'/manage_main')
