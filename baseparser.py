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
"""A base parser that takes the content and create internal and external links.

Parsing methods taken from ZWiki and refactored for CPSWiki needs.
"""

from urllib import quote, unquote
import re

from Products.CPSUtil.id import generateId

from wikiparserinterface import WikiParserInterface
from wikitags import renderBrackets

from zLOG import LOG, DEBUG

LOG_KEY = 'CPSWiki.baseparser'

# All the characters that can be found in a URL
URL_CHARS = r'[A-Za-z0-9/:@_%~#=&\.\-\?\+\$,]+'
# All the kinds of URLs
URL = r'["=]?((about|http|https|ftp|mailto|file):%s)' % URL_CHARS
URL_REGEXP = re.compile(URL)

# All the letters ASCII and unicode in upper-case
U = 'A-Z\xc0-\xdf'
# All the letters ASCII and unicode in lower-case
L = 'a-z\xe0-\xff'
# Using a negative lookbehind assertion (?<!...)
B = '(?<![%s0-9])' % (U + L)
# XXX: Give some examples
WIKINAME1 = r'(?L)%s[%s]+[%s]+[%s][%s]*[0-9]*' % (B, U, L, U, U + L)
# XXX: Give some examples
WIKINAME2 = r'(?L)%s[%s][%s]+[%s][%s]*[0-9]*'  % (B, U, U, L, U + L)
# [xxx] but not [[xxx]] or [xxx[xxx] or [xxx]xxx]
BRACKETED_CONTENT = r'\[([^][\n]+)\]'
# Proposed more restrictive expression
#BRACKETED_CONTENT = r'\[((%s.-_ )+)\]' % (U + L)

# WIKILINK is just a combitation of the possibilities of WIKINAME1, WIKINAME2,
# BRACKETED_CONTENT and URL.
WIKILINK  = r'!?(%s|%s|%s|%s)' % (WIKINAME1, WIKINAME2, BRACKETED_CONTENT, URL)
WIKILINK_REGEXP = re.compile(WIKILINK)
BRACKETED_CONTENT_REGEXP = re.compile(BRACKETED_CONTENT)

class BaseParser:
    __implements__ = (WikiParserInterface,)

    wiki = None
    linked_pages = []

    def getId(self):
        return 'baseparser'


    def parseContent(self, content, wiki):
        """Return the render of the provided content along with references on
        the linked pages and potentially linked pages.
        """
        self.wiki = wiki
        self.linked_pages = []
        self.potential_linked_pages = []
        # A regexp can be with either a replacement string or a replacement
        # function.
        render = WIKILINK_REGEXP.sub(self._wikilinkReplace, content)
        return render, self.linked_pages, self.potential_linked_pages


    def _wikilinkReplace(self, match):
        """Replace an occurrence of the wikilink regexp or one of the
        special [] constructs with a suitable hyperlink.

        The argument match is a re MatchObject.
        """
        # matches beginning with ! should be left alone
        if re.match('^!', match.group(0)):
            return match.group(1)

        m = morig = match.group(1)

        stripped_label = m.strip('[').strip(']')
        m_nospace = generateId(stripped_label, lower=False)

        # If it's a bracketed expression
        if BRACKETED_CONTENT_REGEXP.match(m):
            # Strip the enclosing []'s
            m = BRACKETED_CONTENT_REGEXP.sub(r'\1', m)

            handled, value = renderBrackets(m, self, self.wiki)

            if handled:
                return value

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

        # If it's an ordinary url, link to it
        if URL_REGEXP.match(m):
            # except, if preceded by " or = it should probably be left alone
            if re.match('^["=]', m):     # "
                return m
            else:
                return '<a href="%s">%s</a>' % (m, m)

        # It might be a structured text footnote?
        search_m = m
        for re_specialchar in '.^$*+?':
            search_m = search_m.replace(re_specialchar, '\%s' % re_specialchar)

        # If a page (or something) of this name exists, link to it
        if (wiki is not None) and (m_nospace in wiki.objectIds()):
            if m_nospace not in self.linked_pages:
                self.linked_pages.append(m_nospace)
            return '<a href="../%s/cps_wiki_pageview">%s</a>' % (quote(m_nospace), m)
        else:
            # Adding a potential page
            if m_nospace not in self.potential_linked_pages:
                self.potential_linked_pages.append(m_nospace)
            # Providing a "?" creation link
            return '%s<a href="../addPage?title=%s">?</a>' % (morig, quote(m))
