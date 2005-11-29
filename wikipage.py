# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziad�<tz@nuxeo.com>
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

from zLOG import LOG, DEBUG, TRACE

import urllib
from datetime import datetime

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from ZODB.PersistentList import PersistentList
from OFS.Image import cookId
from ZPublisher.HTTPRequest import FileUpload
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

try:
    from Products.CMFCore.permissions import \
         View, ModifyPortalContent, DeleteObjects
except ImportError: # CPS <= 3.2
    from Products.CMFCore.CMFCorePermissions import \
         View, ModifyPortalContent, DeleteObjects

from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.html import sanitize
from Products.CPSCore.CPSBase import CPSBaseFolder
from Products.CPSCore.CPSBase import CPSBaseDocument

from wikiversionning import VersionContent
from wikirelations import WikiRelation, ZODBDummyBackEnd

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
                   'action': 'cps_wiki_pagedelete',
                   'permissions': (DeleteObjects,),
                   },
                   {'id': 'syntax_help',
                   'name': 'action_syntax_help',
                   'action': 'cps_wiki_help',
                   'permissions': (View,),
                   },
                  ),
      'cps_display_as_document_in_listing': 1,
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
    """A persistent WikiPage Page implementation with versionning.
    """
    meta_type = 'Wiki Page'
    portal_type = meta_type

    _properties = CPSBaseFolder._properties

    security = ClassSecurityInfo()

    def __init__(self, id, source='', **kw):
        CPSBaseFolder.__init__(self, id, **kw)
        initial_tags = self._createVersionTag()
        self.source = ZODBVersionContent(source, initial_tags)

        # This is a cache. It contains the last HTML render as a string.
        self._render = None

        # This is a cache. It contains the IDs of the pages that can be created
        # from this page.
        self._potential_linked_pages = None

        self._relations = WikiRelation(self, ZODBDummyBackEnd())

    def _getCurrentDateStr(self):
        """ gets current date """
        date = datetime(1970, 1, 1)
        now = date.now()
        # english style
        return now.strftime('%a %m/%d/%y %H:%M')

    def _createVersionTag(self):
        tag = {}
        tag['author'] = self._getUserName()
        tag['date'] = self._getCurrentDateStr()
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

    security.declareProtected(View, 'getSource')
    def getSource(self):
        """Return the source as it has been entered by the user.
        """
        return self.source.getLastVersion()[0]

    security.declareProtected(View, 'render')
    def render(self):
        """Render the wiki page source."""
        if self._render is None:
            self.updateCache()
        return self._render

    security.declareProtected(View, 'getLinkedPages')
    def getLinkedPages(self):
        """Return the IDs of the pages this page links to.
        """
        return self._relations.isLinkedTo()

    security.declareProtected(View, 'getPotentialLinkedPages')
    def getPotentialLinkedPages(self):
        """Return the IDs of the pages that can be created from this page.
        """
        return self._relations.isLinkableTo()

    security.declareProtected(View, 'updateCache')
    def updateCache(self):
        """Update all the caches of the page with the current computed values.
        """
        wiki = self.getParent()
        parser = wiki.getParser()
        source = self.getSource()

        # calculate the page
        render, links, potential_links = parser.parseContent(source, wiki)

        # update rendered
        self._render = render

        # update links
        self._relations.clearAll()

        # link to pages
        self._relations.addLinksTo(links)
        for link in links:
            linked_page = wiki.getPage(link)
            if linked_page is not None:
                linked_page.addBackLinksTo([self.id])

        # potential links
        self._relations.addLinkablesTo(potential_links)

        # back links
        for page_id, page in wiki.getPages():
            if page == self:
                return

            page_links = page.getLinkedPages()
            if self.id in page_links:
                self.addBackLinksTo([page_id])

            potential_page_links = page.getPotentialLinkedPages()
            if self.id in potential_page_links:
                self.addBackLinksTo([page_id])
                page.addLinksTo(self.id)

    security.declareProtected(View, 'getBackedLinkedPages')
    def getBackedLinkedPages(self):
        """Return the IDs of the pages where this page is linked.
        """
        return self._relations.isBackLinkedTo()

    security.declareProtected(ModifyPortalContent, 'uploadFile')
    def uploadFile(self, file, REQUEST=None):
        """Upload a file in the repository."""
        if file is None or file == '':
            return False
        if not isinstance(file, FileUpload):
            if REQUEST is not None:
                psm = 'not a file'
                REQUEST.RESPONSE.\
                    redirect("cps_wiki_pageedit?portal_status_message=%s" % psm)
            return False

        fileid = cookId('', '', file)[0]
        self.manage_addFile(fileid, file=file)

        if REQUEST is not None:
            psm = 'File uploaded.'
            REQUEST.RESPONSE.\
                redirect("cps_wiki_pageview?portal_status_message=%s" % psm)
        return True

    security.declareProtected(ModifyPortalContent, 'edit')
    def edit(self, title=None, source=None, REQUEST=None):
        """Edit the page."""
        is_locked, psm = self._verifyLocks(REQUEST)
        if is_locked:
            # TODO: Propose a merge
            if REQUEST is not None:
                REQUEST.RESPONSE.\
                    redirect("cps_wiki_pageedit?portal_status_message=%s" % psm)
            return False
        else:
            self.clearCache()
            try:
                if source is not None:
                    source = sanitize(source)
                    tags = self._createVersionTag()
                    self.source.appendVersion(source, tags)
                    self.updateCache()
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
        """Delete this page."""
        wiki = self.getParent()
        wiki.deletePage(self.id, REQUEST)

        # Clearing the cache of the pages that have links to this page
        for id in self.getBackedLinkedPages():
            page = wiki[id]
            page.removeBackLinksTo([self.id])

    security.declareProtected('View archived revisions', 'getAllDiffs')
    def getAllDiffs(self):
        """Renders a list of differences with last diff first."""
        source = self.source
        version_count = source.getVersionCount()
        versions = []
        version_numbers = range(version_count)
        version_numbers.reverse()
        for i in version_numbers:
            version = source.getVersion(i)
            tags = version[1]
            versions.append(tags)
        return versions

    security.declareProtected('View archived revisions', 'getDiffs')
    def getDiffs(self, version_1, version_2, separator=''):
        """Retrieve differences between 2 versions."""
        if isinstance(version_1, str):
            version_1 = int(version_1)

        if isinstance(version_2, str):
            version_2 = int(version_2)

        return self.source.getDiffs(version_1, version_2, separator)

    security.declareProtected(ModifyPortalContent, 'restoreVersion')
    def restoreVersion(self, index, REQUEST=None):
        """Restore a previous version."""
        self.source.restoreVersion(index)
        if REQUEST is not None:
            psm = 'Version restored.'
            REQUEST.RESPONSE.redirect\
                ("cps_wiki_pageview?portal_status_message=%s" % psm)

    security.declarePrivate('_verifyLocks')
    def _verifyLocks(self, REQUEST):
        """Edition check lock."""
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

    security.declareProtected(ModifyPortalContent, 'lockPage')
    def lockPage(self, REQUEST=None):
        """Lock the page."""
        wiki = self.getParent()
        return wiki.lockPage(self, REQUEST)

    security.declareProtected(ModifyPortalContent, 'unLockPage')
    def unLockPage(self, REQUEST=None):
        """Unlock the page."""
        wiki = self.getParent()
        return wiki.unLockPage(self, REQUEST)

    security.declareProtected(ModifyPortalContent, 'clearCache')
    def clearCache(self):
        self._render = None

    #
    # utf8 I/O for AJAX - XXX need to be moved in a view
    #
    def _Utf8ToIso(self, value, codec='ISO-8859-15'):
        if isinstance(value, str):
            uvalue = value.decode('utf-8', 'replace')
            return uvalue.encode(codec)
        else:
            return value

    security.declareProtected(ModifyPortalContent, 'jedit')
    def jedit(self, title=None, source=None, REQUEST=None):
        """ prevents uf8 junk

        if edited from AJAX for example, we get a string
        that contains unicode"""
        if title is not None:
            title = self._Utf8ToIso(title)
        if source is not None:
            source = self._Utf8ToIso(source)
        return self.edit(title, source)

    security.declareProtected(View, 'jrender')
    def jrender(self, REQUEST):
        """ prevents uf8 junk """
        REQUEST.response.setHeader('content-type',
                                   'text/plain; charset=ISO-8859-15')
        return self.render()

    security.declareProtected(View, 'jgetSource')
    def jgetSource(self, REQUEST):
        """ prevents uf8 junk """
        REQUEST.response.setHeader('content-type',
                                   'text/plain; charset=ISO-8859-15')
        return self.getSource()

    #
    # public relations APIs (backlinks)
    #
    security.declareProtected(ModifyPortalContent, 'addBackLinksTo')
    def addBackLinksTo(self, ids):
        self._relations.addBackLinksTo(ids)

    security.declareProtected(ModifyPortalContent, 'removeBackLinksTo')
    def removeBackLinksTo(self, ids):
        self._relations.removeBackLinksTo(ids)

    security.declareProtected(ModifyPortalContent, 'addLinksTo')
    def addLinksTo(self, ids):
        # remove potential link, if exists
        self._relations.removeLinkablesTo(ids)
        # add the link
        self._relations.addLinksTo(ids)
        # clear the cache
        self.clearCache()

    security.declareProtected(ModifyPortalContent, 'removeReference')
    def removeReference(self, id):
        self._relations.removeBackLinksTo([id])
        self._relations.removeLinkablesTo([id])
        count = self._relations.removeLinksTo([id])
        if count > 0:
            self.clearCache()

    security.declareProtected(View, 'getLinksSummary')
    def getLinksSummary(self):
        """ summarizes links """
        summary = {}
        summary['links'] = self.getLinkedPages()
        summary['potential_links'] = self.getPotentialLinkedPages()
        summary['back_links'] = self.getBackedLinkedPages()
        return summary

    #
    # ZMI
    #
    manage_options = (
        {'label': "Edit",
         'action': 'manage_editPageForm'
         },
        ) + CPSBaseFolder.manage_options

    security.declareProtected(ModifyPortalContent, 'manage_editPageForm')
    manage_editPageForm = PageTemplateFile('zmi/edit_page', globals(),
                                           __name__='manage_editPageForm')

    security.declareProtected(ModifyPortalContent, 'manage_editPage')
    def manage_editPage(self, title, source, REQUEST=None):
        """Modify the source of the page."""
        self.edit(title, source)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url()
                                      + '/manage_editPageForm'
                                      '?manage_tabs_message=Modified.')

InitializeClass(WikiPage)


manage_addWikiPageForm = PageTemplateFile('zmi/zmi_wikiPageAdd', globals(),
                                          __name__='manage_addWikiPageForm')

def manage_addWikiPage(self, id, title, REQUEST=None):
    """Add the simple content."""
    ob = WikiPage(id)
    ob.title = title

    id = self._setObject(id, ob)

    if REQUEST is None:
        return
    try:
        u = self.DestinationURL()
    except AttributeError:
        u = REQUEST['URL1']
    if REQUEST.has_key('submit_edit'):
        u = "%s/%s" % (u, urllib.quote(id))
    REQUEST.RESPONSE.redirect(u + '/manage_main')
