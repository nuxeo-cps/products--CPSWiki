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

from utils import makeId
from Products.CPSCore.CPSBase import CPSBaseFolder
#from reStructuredText import HTML
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.CMFCorePermissions import View, ViewManagementScreens
from Products.CPSCore.CPSBase import CPSBaseDocument

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
                   'permissions': (View,),
                   },
                  {'id': 'edit',
                   'name': 'action_edit',
                   'action': 'cps_wiki_pageedit',
                   'permissions': (View,),
                   },
                  {'id': 'localroles',
                   'name': 'action_local_roles',
                   'action': 'cps_chat_localrole_form',
                   'permissions': (ViewManagementScreens,)
                   },
                  ),
      'cps_display_as_document_in_listing' : 1,
      },
    )

class WikiPage(CPSBaseFolder):
    """A persistent WikiPage Page implementation.

    Here is an example of changing the title and description of the wiki:

    >>> wp = WikiPage()
    >>> wp.title
    ''
    >>> wp.title = 'WikiPage Title'
    >>> wp.title
    'WikiPage Title'
    >>> wp.source
    ''
    >>> wp.source = 'Source'
    >>> wp.source
    'Source'
    """
    meta_type = "CPS Wiki Page"
    portal_type = meta_type
    parent = None

    _properties = CPSBaseFolder._properties

    def __init__(self, id, source='', **kw):
        CPSBaseFolder.__init__(self, id, **kw)
        self.source = source

    def getParent(self):
        return self.aq_inner.aq_parent

    def toolbar(self):
        res = '<div><a href="cps_wiki_pageedit">Edit</a> \
            | <a href="../cps_wiki_pageview">TOC</a></div><br/>'
        return res

    def render(self):
        """Render the wiki page source."""
        #result = HTML(self.source)
        result = self.source
        result = self.renderLinks(result)
        # adding toolbar
        #result = self.toolbar() + result
        return result

    def editPage(self, title=None, source=None, REQUEST=None):
        """Edits the stuff"""
        if source is not None:
            self.source = source
        if title is not None:
            self.title = title
        if REQUEST is not None:
            psm = 'Content changed.'
            REQUEST.RESPONSE.redirect("cps_wiki_pageedit?portal_status_message=%s" % psm)

    def renderLinks(self, content):
        """ creates link with founded [pages]
        """
        wiki = self.getParent()
        parser = wiki.parser
        return parser.parseContent(content)

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
