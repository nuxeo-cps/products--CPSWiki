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
import urllib

from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import \
     View, ModifyPortalContent, AddPortalContent, DeleteObjects, \
     ChangePermissions
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.CPSCore.CPSBase import CPSBaseFolder

from utils import makeId
from wikipage import WikiPage
from wikiparsers import parsers, generateParser
from wikilocker import LockerList, ILockableItem

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
                 {'id': 'add_page',
                   'name': 'action_add_page',
                   'action': 'cps_wiki_pageadd',
                   'permissions': (AddPortalContent,),
                   },
                  {'id': 'localroles',
                   'name': 'action_local_roles',
                   'action': 'folder_localrole_form',
                   'permissions': (ChangePermissions,)
                   },
                  ),
      'cps_display_as_document_in_listing' : 1,
      },
    )

class WikiLockablePage:
    __implements__ = (ILockableItem, )

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
                raise str(info) + ' <-> ' + str(li)
                return False

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

    security.declareProtected(View, 'getWikiPage')
    def getWikiPage(self, title_or_id):
        wikipage_id = makeId(title_or_id)
        if wikipage_id in self.objectIds():
            return self[wikipage_id]
        return None

    security.declareProtected(DeleteObjects, 'deleteWikiPage')
    def deleteWikiPage(self, title_or_id, REQUEST=None):
        """ deletes a page, given its id or title """
        page = self.getWikiPage(title_or_id)
        if page is not None:
            self.manage_delObjects([page.id])

        if REQUEST is not None:
            psm = 'page_deleted'
            REQUEST.RESPONSE.redirect(self.absolute_url()+\
                '?portal_status_message=%s' % psm)

    security.declareProtected(AddPortalContent, 'addWikiPage')
    def addWikiPage(self, title, REQUEST=None):
        """ creates and adds a wiki page """
        wikipage_id = makeId(title)
        stepper = 1

        while wikipage_id in self.objectIds():
            wikipage_id = wikipage_id + str(stepper)
            stepper += 1

        # creates the instance
        wikipage = WikiPage(wikipage_id, '')
        wikipage.title = title
        wikipage_id = self._setObject(wikipage_id, wikipage)
        wikipage = self[wikipage_id]

        # returns to the TOC
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(wikipage.absolute_url() + '/cps_wiki_pageedit')
        else:
            return self[wikipage_id]

manage_addWikiForm = PageTemplateFile("www/zmi_wikiAdd", globals(),
    __name__ = 'manage_addWikiForm')

def manage_addWiki(self, id, title='wiki', REQUEST=None):
    """Add the simple content."""
    wiki = Wiki(id)
    id = self._setObject(id, wiki)

    if REQUEST is None:
        return
    try:
        u = self.DestinationURL()
    except:
        u = REQUEST['URL1']
    if REQUEST.has_key('submit_edit'):
        u = "%s/%s" % (u, urllib.quote(id))
    REQUEST.RESPONSE.redirect(u+'/manage_main')
