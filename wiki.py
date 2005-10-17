# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziadé <tz@nuxeo.com>
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

import urllib

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
try:
    from Products.CMFCore.permissions import \
         View, ModifyPortalContent, AddPortalContent, DeleteObjects, \
         ChangePermissions, ManagePortal
except ImportError: # CPS <= 3.2
    from Products.CMFCore.CMFCorePermissions import \
         View, ModifyPortalContent, AddPortalContent, DeleteObjects, \
         ChangePermissions, ManagePortal
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CPSCore.CPSBase import CPSBaseFolder
from Products.CPSUtil.id import generateId

from wikipage import WikiPage
from wikiparsers import parsers, generateParser
from wikilocker import LockerList, ILockableItem

from zLOG import LOG, DEBUG, TRACE

LOG_KEY = 'CPSWiki.wiki'

factory_type_information = (
    { 'id': 'Wiki',
      'meta_type': 'Wiki',
      'description': 'portal_type_CPSWiki_description',
      'icon': 'wiki.png',
      'title': "portal_type_CPSWiki_title",
      'product': 'CPSWiki',
      'factory': 'manage_addWiki',
      'immediate_view': 'cps_wiki_view',
      'filter_content_types': 0,
      'allowed_content_types': ('Wiki Page',),
      'allow_discussion': 0,
      'actions': ({'id': 'view',
                   'name': 'action_view',
                   'action': 'cps_wiki_view',
                   'permissions': (View,),
                   },
                  {'id': 'full_view',
                   'name': 'action_full_view',
                   'action': 'cps_wiki_full_view',
                   'permissions': (ModifyPortalContent,),
                   },
                  {'id': 'properties',
                   'name': 'action_properties',
                   'action': 'cps_wiki_properties',
                   'permissions': (ModifyPortalContent,),
                   },
                 {'id': 'add_page',
                   'name': 'action_add_page',
                   'action': 'cps_wiki_pageadd',
                   'permissions': (AddPortalContent,),
                   },
                  {'id': 'contents',
                   'name': 'action_folder_contents',
                   'action': 'folder_contents',
                   'permissions': (ModifyPortalContent,),
                   },
                  {'id': 'localroles',
                   'name': 'action_local_roles',
                   'action': 'folder_localrole_form',
                   'permissions': (ChangePermissions,)
                   },
                  ),
      'cps_display_as_document_in_listing': 1,
      },
    )


class WikiLockablePage:
    __implements__ = (ILockableItem,)

    def __init__(self, wikipage, lock_info, lock_duration):
        self.uri = wikipage.absolute_url()
        self.lock_info = lock_info
        self.lock_duration = lock_duration

    def getURI(self):
        return self.uri

    def getLockInfo(self):
        return self.lock_info

    def getLockDuration(self):
        return self.lock_duration


class Wiki(CPSBaseFolder):
    """
    >>> wiki = Wiki()
    >>> wiki.title
    ''
    >>> wiki.title = 'Wiki Title'
    >>> wiki.title
    'Wiki Title'
    """
    meta_type = 'Wiki'
    portal_type = meta_type
    _properties = CPSBaseFolder._properties + (
        {'id': 'parser', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_parsers',
         'label': 'Parser'},
           )

    all_parsers = parsers
    parser = all_parsers[0]
    _parser = None
    lock_duration = 30

    security = ClassSecurityInfo()

    def __init__(self, id, **kw):
        CPSBaseFolder.__init__(self, id, **kw)
        self.locker = LockerList()

    def _getCurrentUser(self):
        mt = getToolByName(self, 'portal_membership')
        return mt.getAuthenticatedMember()

    security.declareProtected(ModifyPortalContent, 'pageLockInfo')
    def pageLockInfo(self, page):
        """ returns page lock infos """
        # kept for compatibility with previous wiki instances
        if not hasattr(self, 'locker'):
            self.locker = LockerList()
        # not using adapter to avoid info recalculations
        uri = page.absolute_url()
        return self.locker.getItemInfo(uri)


    security.declareProtected(ModifyPortalContent, 'getLockId')
    def getLockId(self, REQUEST=None):
        """ returns a lock info """
        if REQUEST is not None:
            info = REQUEST.SESSION.id        # works in all cases
        else:
            info = self._getCurrentUser()
        return info


    security.declareProtected(ModifyPortalContent, 'lockPage')
    def lockPage(self, page, REQUEST=None):
        """ locks a page """
        # kept for compatibility with previous wiki instances
        if not hasattr(self, 'locker'):
            self.locker = LockerList()

        duration = self.lock_duration
        info = self.getLockId(REQUEST)

        li = self.pageLockInfo(page)
        if li is not None:
            # page is already locked
            if li[1] == info:
                return True
            else:
                # by someone else
                return False
        else:
            item = WikiLockablePage(page, info, duration)
            self.locker.addItem(item)
            return True

    security.declareProtected(ModifyPortalContent, 'unLockPage')
    def unLockPage(self, page, REQUEST=None):
        """ unlocks a page """
        # kept for compatibility with previous wiki instances
        if not hasattr(self, 'locker'):
            self.locker = LockerList()

        info = self.getLockId(REQUEST)

        # not using adapter to avoid info recalculations
        li = self.pageLockInfo(page)
        if li is not None:
            if li[1] != info:
                # locked by another user
                return False
        else:
            # nothing to unlock
            return False

        uri = page.absolute_url()
        self.locker.removeItem(uri)
        return True

    security.declareProtected(View, 'getParser')
    def getParser(self):
        """ returns a parser instance """
        parser = self._parser
        if parser is None or parser.getId() != parser:
            parser = generateParser(self.parser)
        return parser

    security.declareProtected(View, 'getPage')
    def getPage(self, title_or_id):
        if isinstance(title_or_id, unicode):
            title_or_id = title_or_id.encode('ISO-8859-15')
        wikipage_id = generateId(title_or_id, lower=False)
        if wikipage_id in self.objectIds():
            return self[wikipage_id]
        return None

    security.declareProtected(DeleteObjects, 'deletePage')
    def deletePage(self, title_or_id, REQUEST=None):
        """ deletes a page, given its id or title """
        page = self.getPage(title_or_id)
        if page is not None:
            self.manage_delObjects([page.id])

        if REQUEST is not None:
            psm = 'psm_page_deleted'
            REQUEST.RESPONSE.redirect(self.absolute_url()+\
                '?portal_status_message=%s' % psm)

    security.declareProtected(AddPortalContent, 'addPage')
    def addPage(self, title, REQUEST=None):
        """Create and add a wiki page."""
        if isinstance(title, unicode):
            title = title.encode('ISO-8859-15')
        wikipage_id = generateId(title, lower=False)
        if wikipage_id in self.objectIds():
            raise ValueError("The ID \"%s\" is already in use." % wikipage_id)

        # Creating the actual page
        wikipage = WikiPage(wikipage_id)
        wikipage.title = title
        wikipage_id = self._setObject(wikipage_id, wikipage)
        wikipage = self[wikipage_id]

        # Clearing the cache of the pages that have a reference to this page.
        for id, object in self.objectItems():
            if object.portal_type != WikiPage.portal_type:
                continue
            page = self[id]
            potential_links = page.getPotentialLinkedPages()
            #LOG(LOG_KEY, TRACE, "page %s has potential_links = %s"
            #    % (page_id, potential_links))
            if potential_links:
                page.clearCache()

        # Redirecting to the edit view of the newly created page
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(wikipage.absolute_url() +
                                      '/cps_wiki_pageedit')
        else:
            return self[wikipage_id]

    security.declarePrivate('_recursiveGetLinks')
    def _recursiveGetLinks(self, page, called=[]):
        """ make link tree, avoiding circular references """
        if page in called:
            return []
        else:
            called.append(page)

        returned = []

        pages = page.getLinkedPages()

        for cpage in pages:
            object = self[cpage]
            if object.id == page.id or object in called:
                continue
            element = {}
            element['page'] = object
            element['children'] = self._recursiveGetLinks(object, called)
            returned.append(element)

        returned.sort(lambda x, y: cmp(x['page'].title, y['page'].title))
        return returned

    security.declareProtected(View, 'getSummary')
    def getSummary(self):
        """ creates the summary tree """
        # first of all, let's find the first layer
        # of pages by sorting pages with their backlink count
        sorted_list = []
        for id, object in self.objectItems():
            if object.portal_type != WikiPage.portal_type:
                continue
            page = self[id]
            element = (len(page.getLinkedPages()),
                       len(page.getBackedLinkedPages()), page)
            sorted_list.append(element)
        if len(sorted_list) == 0:
            return []
        sorted_list.sort()

        # Now constructing the tree
        tree = []
        for item in sorted_list:
            if item[1] > 0:
                continue
            element = {}
            element['page'] = item[2]
            children = self._recursiveGetLinks(item[2], [])
            element['children'] = children
            tree.append((len(children), element))
        tree_first_level = [node[1] for node in tree]
        tree_first_level.sort(lambda x, y: cmp(x['page'].title, y['page'].title))
        return tree_first_level

    security.declareProtected(ModifyPortalContent, 'clearCaches')
    def clearCaches(self):
        """Clear all the caches contained in this wiki, including those of the
        pages.
        """
        for id, object in self.objectItems():
            if object.portal_type != WikiPage.portal_type:
                continue
            page = self[id]
            page.clearCache()

    security.declareProtected(ModifyPortalContent, 'changeProperties')
    def changeProperties(self, REQUEST=None, **kw):
        """ let the user change global properties """
        if hasattr(REQUEST, 'form'):
            for element in REQUEST.form:
                kw[element] = REQUEST.form[element]

        self.manage_changeProperties(**kw)

        if REQUEST is not None:
            psm = 'psm_properties_changed'
            REQUEST.RESPONSE.redirect(self.absolute_url()+\
                '/cps_wiki_properties?portal_status_message=%s' % psm)

    #
    # ZMI
    #

    manage_options = CPSBaseFolder.manage_options[:1] + (
        {'label': "Cache",
         'action': 'manage_cacheForm'
         },
        ) + CPSBaseFolder.manage_options[1:]

    security.declareProtected(ManagePortal, 'manage_cacheForm')
    manage_cacheForm = PageTemplateFile('zmi/clear_cache', globals(),
                                           __name__='manage_cacheForm')

    security.declareProtected(ManagePortal, 'manage_clearCache')
    def manage_clearCache(self, REQUEST=None):
        """Clear all the caches of the wiki."""
        self.clearCaches()
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(self.absolute_url()
                                      + '/manage_cacheForm'
                                      '?manage_tabs_message=Modified.')

InitializeClass(Wiki)


manage_addWikiForm = PageTemplateFile('zmi/wikiAdd', globals(),
                                      __name__='manage_addWikiForm')

def manage_addWiki(self, id, title='wiki', REQUEST=None):
    """Add the simple content."""
    wiki = Wiki(id)
    wiki.title = title

    id = self._setObject(id, wiki)

    if REQUEST is None:
        return
    try:
        u = self.DestinationURL()
    except AttributeError:
        u = REQUEST['URL1']
    if REQUEST.has_key('submit_edit'):
        u = "%s/%s" % (u, urllib.quote(id))
    REQUEST.RESPONSE.redirect(u+'/manage_main')
