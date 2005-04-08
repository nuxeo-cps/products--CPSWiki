# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziad� <tz@nuxeo.com>
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
#
# $Id$

from ZODB.PersistentList import PersistentList
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.permissions import \
     View, ModifyPortalContent, DeleteObjects
from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.html import sanitize
from Products.CPSCore.CPSBase import CPSBaseFolder
from Products.CPSCore.CPSBase import CPSBaseDocument

from utils import getCurrentDateStr
from wikiversionning import VersionContent
import urllib

factory_type_information = (
    { 'id': 'Wiki Page',
      'meta_type': 'Wiki Page',
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
                   'permissions': (View,),
                   },
                  {'id': 'edit',
                   'name': 'action_edit',
                   'action': 'cps_wiki_pageedit',
                   'permissions': (ModifyPortalContent,),
                   },
                   {'id': 'history',
                   'name': 'action_history',
                   'action': 'cps_wiki_pagehistory',
                   'permissions': ('View archived revisions',),
                   },
                   {'id': 'delete',
                   'name': 'action_delete',
                   'action': 'delete',
                   'permissions': (DeleteObjects,),
                   },
                  ),
      'cps_display_as_document_in_listing' : 1,
      },
    )

class ZODBVersionContent(VersionContent):
    """Overrides all VersionContent read / write
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
    meta_type = 'Wiki Page'
    portal_type = meta_type

    _properties = CPSBaseFolder._properties

    security = ClassSecurityInfo()

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

    security.declareProtected(View, 'getParent')
    def getParent(self):
        return self.aq_inner.aq_parent

    security.declareProtected(View, 'getParserType')
    def getParserType(self):
        """Return parser type """
        wiki = self.getParent()
        return wiki.parser

    security.declareProtected(View, 'content')
    def content(self):
        """Render the wiki page source.

        This method is needed and called by Zope even if the code of CPSWiki
        doesn't make any reference to it.
        """
        return self.source.getLastVersion()

    security.declareProtected(View, 'render')
    def render(self):
        """ Render the wiki page source."""
        result = self.source.getLastVersion()[0]
        result = self.renderLinks(result)
        return result

    security.declareProtected(View, 'renderLinks')
    def renderLinks(self, content):
        """creates link with founded [pages]"""
        wiki = self.getParent()
        parser = wiki.getParser()
        return parser.parseContent(wiki, content)

    security.declareProtected(ModifyPortalContent, 'edit')
    def edit(self, title=None, source=None, REQUEST=None):
        """Edit the page"""
        is_locked, psm = self._verifyLocks(REQUEST)
        if is_locked:
            # TODO: Propose a merge
            if REQUEST is not None:
                REQUEST.RESPONSE.\
                    redirect("cps_wiki_pageedit?portal_status_message=%s" % psm)
            return False
        else:
            try:
                if source is not None:
                    source = sanitize(source)
                    tags = self._createVersionTag()
                    self.source.appendVersion(source, tags)
                if title is not None:
                    self.title = title
            finally:
                self.unLockPage(REQUEST)

            if REQUEST is not None:
                psm = 'Content changed.'
                REQUEST.RESPONSE.\
                    redirect("cps_wiki_pageview?portal_status_message=%s" % psm)
            return True

    security.declareProtected(DeleteObjects, 'delete')
    def delete(self, REQUEST=None):
        """suicide"""
        wiki = self.getParent()
        # XXX: Need to add a warning here
        wiki.deletePage(self.id, REQUEST)

    security.declareProtected('View archived revisions', 'getAllDiffs')
    def getAllDiffs(self):
        """renders a list of differences"""
        source = self.source
        version_count = source.getVersionCount()
        versions = []
        for i in range(version_count):
            version = source.getVersion(i)
            tags = version[1]
            versions.append(tags)
        """

        for i in range(version_count-1):
            diff = source.getDiffs(i, i+1)
            versions.append(diff)
        """
        return versions

    security.declareProtected('View archived revisions', 'getDiffs')
    def getDiffs(self, version_1, version_2):
        """retrieves differences between 2 versions"""
        if isinstance(version_1, str):
            version_1 = int(version_1)

        if isinstance(version_2, str):
            version_2 = int(version_2)

        return self.source.getDiffs(version_1, version_2)

    security.declareProtected(ModifyPortalContent, 'restoreVersion')
    def restoreVersion(self, index, REQUEST=None):
        """restores a previous version"""
        self.source.restoreVersion(index)
        if REQUEST is not None:
            psm = 'Version restored.'
            REQUEST.RESPONSE.redirect\
                ("cps_wiki_pageview?portal_status_message=%s" % psm)

    def _verifyLocks(self, REQUEST):
        """edition checks lock"""
        wiki = self.getParent()
        infos = wiki.pageLockInfo(self)
        if infos is None:
            # the page is not locked, we can continue
            return False, ''
        else:
            lock_id = wiki.getLockId(REQUEST)
            if infos[1] == lock_id:
                # page locked by current user,  we can continue
                return False, ''
            else:
                # page locked by someone else
                return True, 'Page locked.'

    def lockPage(self, REQUEST=None):
        """locks the page"""
        wiki = self.getParent()
        return wiki.lockPage(self, REQUEST)

    def unLockPage(self, REQUEST=None):
        """unlocks the page"""
        wiki = self.getParent()
        return wiki.unLockPage(self, REQUEST)

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
    REQUEST.RESPONSE.redirect(u + '/manage_main')
