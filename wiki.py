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
import urllib
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CPSCore.CPSBase import CPSBaseFolder
from Products.CMFCore.CMFCorePermissions import View, ViewManagementScreens
from utils import makeId
from wikipage import WikiPage
from wikiparsers import parsers, generateParser
from wikipermissions import addWikiPage

factory_type_information = (
    { 'id': 'CPS Wiki',
      'meta_type': 'CPS Wiki',
      'description': 'portal_type_CPSWiki_description',
      'icon': 'wiki.png',
      'title': "portal_type_CPSWiki_title",
      'product': 'CPSWiki',
      'factory': 'manage_addWiki',
      'immediate_view': 'cps_wiki_view',
      'filter_content_types': 0,
      'allowed_content_types': ('CPS Wiki Page',),
      'allow_discussion': 0,
      'actions': ({'id': 'view',
                   'name': 'action_view',
                   'action': 'cps_wiki_view',
                   'permissions': (View,),
                   },
                 {'id': 'add_page',
                   'name': 'action_add_page',
                   'action': 'cps_wiki_pageadd',
                   'permissions': (addWikiPage,),
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

class Wiki(CPSBaseFolder):
    """
    >>> wiki = Wiki()
    >>> wiki.title
    ''
    >>> wiki.title = 'Wiki Title'
    >>> wiki.title
    'Wiki Title'
    """
    meta_type = "CPS Wiki"
    portal_type = meta_type
    _properties = CPSBaseFolder._properties + (
        {'id': 'parser', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_parsers',
         'label': 'Parser'},)


    all_parsers = parsers
    parser = all_parsers[0]
    _parser = None

    security = ClassSecurityInfo()

    def __init__(self, id, **kw):
        CPSBaseFolder.__init__(self, id, **kw)

    def getParser(self):
        """ returns a parser instance
        """
        _parser = self._parser
        if _parser is None or _parser.getPID() <> parser:
            _parser = generateParser(self.parser)
        return _parser

    security.declareProtected(addWikiPage, 'addWikiPage')
    def addWikiPage(self, title, REQUEST=None):
        """ creates and adds a wiki page
        """
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
            REQUEST.RESPONSE.redirect(wikipage.absolute_url()+'/cps_wiki_pageedit')
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
