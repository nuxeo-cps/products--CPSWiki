# (C) Copyright 2005-2009 Nuxeo SA <http://nuxeo.com>
# Authors:
# Tarek Ziade <tz@nuxeo.com>
# M.-A. Darche
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

from logging import getLogger
import os
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

from Products.CPSUtil.id import generateId
from Products.CPSCore.EventServiceTool import getPublicEventService
from Products.CPSCore.CPSBase import CPSBaseFolder

from wikipage import WikiPage
from wikiparsers import parsers, generateParser
from wikilocker import LockerList, ILockableItem
from wikitags import getRegisteredTags as _getRegisteredTags

LOG_KEY = 'CPSWiki.wiki'

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
        {'id': 'send_diff', 'type': 'boolean', 'mode': 'w',
         'label': "Sending of the diff in the notifications"},
        )

    all_parsers = parsers
    parser = all_parsers[0]
    _parser = None
    send_diff = False
    lock_duration = 30

    security = ClassSecurityInfo()

    def __init__(self, id, **kw):
        CPSBaseFolder.__init__(self, id, **kw)
        self.locker = LockerList()
        self.version = (0, 7)

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

    security.declareProtected(View, 'getPages')
    def getPages(self):
        pages = []
        for id, object in self.objectItems():
            if object.portal_type == WikiPage.portal_type:
                pages.append((id, object))
        return pages

    security.declareProtected(DeleteObjects, 'manage_delObjects')
    def manage_delObjects(self, ids=[], REQUEST=None):
        """Used by regular views and for deletion in the ZMI too.
        """
        for id in ids:
            page = self.getPage(id)
            if page is not None:
                backlinks = page.getBackedLinkedPages()
                links = page.getLinkedPages()
            else:
                backlinks = []
                links = []

            CPSBaseFolder.manage_delObjects(self, ids=[id])
            for backlink in backlinks + links:
                linked_page = self.getPage(backlink)
                if linked_page is not None:
                    linked_page.removeReference(id)

        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)

    security.declareProtected(DeleteObjects, 'deletePage')
    def deletePage(self, title_or_id, REQUEST=None):
        """ deletes a page, given its id or title and clean the caches
        """
        page = self.getPage(title_or_id)
        if page is not None:
            page_id = page.id
            backlinks = page.getBackedLinkedPages()
            links = page.getLinkedPages()
            CPSBaseFolder.manage_delObjects(self, [page_id])
            for backlink in backlinks + links:
                linked_page = self.getPage(backlink)
                if linked_page is not None:
                    linked_page.removeReference(page_id)

            getPublicEventService(self).notifyEvent('workflow_delete', page,
                                                    {'comments': '',
                                                     })
        if REQUEST is not None:
            psm = 'psm_page_deleted'
            REQUEST.RESPONSE.redirect(self.absolute_url()
                                      + '?portal_status_message=%s' % psm)

    security.declareProtected(AddPortalContent, 'addPage')
    def addPage(self, title, REQUEST=None):
        """Create and add a wiki page."""
        wikipage_id = generateId(title, lower=False)
        if wikipage_id in self.objectIds():
            raise ValueError("The ID \"%s\" is already in use." % wikipage_id)

        # Creating the actual page
        wikipage = WikiPage(wikipage_id)
        wikipage.title = title
        wikipage_id = self._setObject(wikipage_id, wikipage)
        wikipage = self[wikipage_id]

        # Clearing the cache of the pages that have a reference to this page.
        for id, page in self.getPages():
            potential_links = page.getPotentialLinkedPages()
            if wikipage_id in potential_links:
                page.addLinksTo([wikipage_id])
                wikipage.addBackLinksTo([id])

        getPublicEventService(self).notifyEvent('workflow_create', wikipage,
                                                {'comments': '',
                                                 })

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
            object = getattr(self, cpage, None)
            if object is None:
                continue
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
        def _visitPage(child, list_):
            if child['page'] not in list_:
                list_.append(child['page'])
            for grandchild in child['children']:
                if grandchild['page'] not in list_:
                    _visitPage(grandchild, list_)

        sorted_list = []
        pages_to_visit = len(self.getPages())
        for id, page in self.getPages():
            element = (len(page.getLinkedPages()),
                       len(page.getBackedLinkedPages()), page)
            sorted_list.append(element)

        if len(sorted_list) == 0:
            return []
        sorted_list.sort()
        sorted_list.reverse()

        # Now constructing the tree
        tree = []
        level = 0
        pages_visited = []

        while len(pages_visited) < pages_to_visit:
            for item in sorted_list:
                if item[2] in pages_visited:
                    continue
                element = {}
                element['page'] = item[2]
                children = self._recursiveGetLinks(item[2], [])
                kept_children = []
                for child in children:
                    if child['page'] not in pages_visited:
                        kept_children.append(child)
                        _visitPage(child, pages_visited)

                element['children'] = kept_children
                tree.append((len(kept_children), element))
                pages_visited.append(item[2])


        tree_first_level = [node[1] for node in tree]
        tree_first_level.sort(lambda x, y: cmp(x['page'].title, y['page'].title))
        return tree_first_level

    security.declareProtected(ModifyPortalContent, 'clearCaches')
    def clearCaches(self, ids=[]):
        """Clear all the caches contained in this wiki, including those of the
        pages.
        """
        if ids == []:
            elements = [page for id, page in self.getPages()]
        else:
            elements = []
            for id in ids:
                back_page = self.getPage(id)
                if back_page is not None:
                    elements.append(back_page)

        for page in elements:
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

    security.declareProtected(View, 'getRegisteredTags')
    def getRegisteredTags(self):
        return _getRegisteredTags()

    #
    # ajax - XXX need to be moved in a view
    #
    def _Utf8ToIso(self, value, codec='ISO-8859-15'):
        if isinstance(value, str):
            uvalue = value.decode('utf-8', 'replace')
            return uvalue.encode(codec)
        else:
            return value


    security.declareProtected(AddPortalContent, 'jaddPage')
    def jaddPage(self, title, REQUEST=None):
        """ prevents uf8 junk

        if edited from AJAX for example, we get a string
        that contains unicode"""
        REQUEST.response.setHeader('content-type',
                                   'text/plain; charset=ISO-8859-15')
        if title is not None:
            title = self._Utf8ToIso(title)
        if self.addPage(title) is not None:
            return 'OK'
        else:
            return 'KO'

    def _node_render(self, item):
        page = item['page']
        content = '<a href="%s">' % page.absolute_url()
        content += page.title_or_id()
        content += '</a>'

        children = item['children']
        if len(children) > 0:
            content += '<ul>'
            for child in children:
                content += '<li>'
                content += self._node_render(child)
                content += '</li>'
            content += '</ul>'
        return content

    security.declareProtected(View, 'jrender')
    def jrender(self, REQUEST=None):
        """ renders the page content """
        REQUEST.response.setHeader('content-type',
                                   'text/plain; charset=ISO-8859-15')
        content = '<ul>'
        items = self.getSummary()
        for item in items:
            content += '<li>'
            content += self._node_render(item)
            content += '</li>'
        content += '</ul>'
        return content

    security.declareProtected(View, 'getDetailedHtmlHelp')
    def getDetailedHtmlHelp(self, lang):
        """Return a HTML formated string that provides a detailed help.

        The PO i18n framework is not very handy for providing an HTML document
        with a precise layout, so we have to rely on a dedicated method.
        """
        # Typical names are of the form wiki_help.restructuredtext.fr.html
        file_name = 'wiki_help.%s.%s.html' % (self.parser, lang)
        file_path = os.path.join(INSTANCE_HOME,
                                 'Products', 'CPSWiki', 'doc', file_name)
        try:
            f = open(file_path, 'rb')
            html_content = f.read()
            f.close()
        except IOError:
            html_content = ''
        return html_content

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
