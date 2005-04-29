# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
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

""" parsing method taken from ZWiki
    and refactored for CPSWiki needs

    this parser takes the content and create
    internal and external links
"""
import urllib
from urllib import quote, unquote
import re

from Products.CPSUtil.id import generateId

from wikiparserinterface import WikiParserInterface

# constants
urlchars = r'[A-Za-z0-9/:@_%~#=&\.\-\?\+\$,]+'
urlendchar  = r'[A-Za-z0-9/]'
url = r'["=]?((about|gopher|http|https|ftp|mailto|file):%s)' % urlchars
U = 'A-Z\xc0-\xdf'
L = 'a-z\xe0-\xff'
b = '(?<![%s0-9])' % (U+L)
bracketedexpr = r'\[([^\n\]]+)\]'
wikiname1 = r'(?L)%s[%s]+[%s]+[%s][%s]*[0-9]*' % (b,U,L,U,U+L)
wikiname2 = r'(?L)%s[%s][%s]+[%s][%s]*[0-9]*'  % (b,U,U,L,U+L)
wikilink  = r'!?(%s|%s|%s|%s)' % (wikiname1,wikiname2,bracketedexpr,url)

class BaseParser:
    __implements__ = (WikiParserInterface, )

    wiki = None
    linked_pages = []

    def getId(self):
        return 'baseparser'

    def parseContent(self, wiki, content):
        """ creates link with founded [pages]
        """
        self.wiki = wiki
        self.linked_pages = []
        rendered = re.sub(wikilink, self._wikilinkReplace, content)
        return self.linked_pages, rendered

    def _wikilinkReplace(self, match, text=''):
        # tasty spaghetti regexps! better suggestions welcome ?
        """
        Replace an occurrence of the wikilink regexp or one of the
        special [] constructs with a suitable hyperlink

        To be used as a re.sub repl function *and* get a proper value
        for literal context, 'allowed', etc, enclose this function
        with the value using 'thunk_substituter'.
        """
        # matches beginning with ! should be left alone
        if re.match('^!', match.group(0)):
            return match.group(1)

        m = morig = match.group(1)

        m_nospace = m.strip('[').strip(']')
        m_nospace = generateId(m_nospace)

        # if it's a bracketed expression,
        if re.match(bracketedexpr, m):

            # strip the enclosing []'s
            m = re.sub(bracketedexpr, r'\1', m)

            # extract a (non-url) path if there is one
            pathmatch = re.match(r'(([^/]*/)+)([^/]+)', m)
            if pathmatch:
                path, id = pathmatch.group(1), pathmatch.group(3)
            else:
                path, id = '', m

            # or if there was a path assume it's to some non-wiki
            # object and skip the usual existence checking for
            # simplicity. Could also attempt to navigate the path in
            # zodb to learn more about the destination
            if path:
                return '<a href="%s%s">%s%s</a>' % (path, id, path, id)

            # otherwise fall through to normal link processing

        wiki = self.wiki
        # if it's an ordinary url, link to it
        if re.match(url,m):
            # except, if preceded by " or = it should probably be left alone
            if re.match('^["=]', m):     # "
                return m
            else:
                return '<a href="%s">%s</a>' % (m, m)

        # it might be a structured text footnote ?
        elif re.search(r'(?si)<a name="%s"' % (m),text):
            return '<a href="#%s">[%s]</a>' % (m,m)

        # a wikiname - if a page (or something) of this name exists, link to
        # it

        elif (wiki is not None) and (m_nospace in wiki.objectIds()):
            if m_nospace not in self.linked_pages:
                self.linked_pages.append(m_nospace)
            return '<a href="../%s/cps_wiki_pageview">%s</a>' % (quote(m_nospace), m)

        # otherwise, provide a "?" creation link
        else:
            return '%s<a href="../addPage?title=%s">?</a>' % (morig, quote(m))
