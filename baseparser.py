# (C) Copyright 2005-2009 Nuxeo SARL <http://nuxeo.com>
# (C) Copyright 2010 AFUL <http://aful.org>
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
"""A base parser that takes the content and create internal and external links.

In this module we don't use UTF-8 in regular expressions. UTF-8 being a
multibyte encoding, where some unicode code points are encoded by 2 or more
bytes, using it would make parts of string - that we don't plan to match -
actually match. Instead we use unicode strings everywhere.

Parsing methods taken from ZWiki and refactored for CPSWiki needs.
"""

from urllib import quote, unquote
import re

from Products.CPSUtil.id import generateId

from interfaces import IWikiParser
from wikitags import renderBrackets

LOG_KEY = 'CPSWiki.baseparser'

# All the characters that can be found in a URL
URL_CHARS = r'[A-Za-z0-9/:@_%~#=&\.\-\?\+\$,]+'
# All the kinds of URLs
URL = r'["=]?((about|http|https|ftp|mailto|file):%s)' % URL_CHARS
URL_REGEXP = re.compile(URL)

# All the letters ASCII and UTF-8 in upper-case
U = 'A-Z\xc0-\xdf'
# All the letters ASCII and UTF-8 in lower-case
L = 'a-z\xe0-\xff'
# Word boundary
# Using a negative lookbehind assertion (?<!...)
B = '(?<![%s0-9])' % (U + L)

# TODO: Give some examples
WIKINAME1 = r'(?L)%s[%s]+[%s]+[%s][%s]*[0-9]*' % (B, U, L, U, U + L)
# TODO: Give some examples
WIKINAME2 = r'(?L)%s[%s][%s]+[%s][%s]*[0-9]*'  % (B, U, U, L, U + L)

# [xxx] but not [[xxx]] or [xxx[xxx] or [xxx]xxx]
BRACKETED_CONTENT = r'(?s)\[.*?\]'
STRICT_BRACKETED_CONTENT = r'\[([^][\n]+)\]'
TRIPLE_BRACKETED_CONTENT = r'(?s)\{\{\{.*?\}\}\}'

# Proposed more restrictive expression
#BRACKETED_CONTENT = r'\[((%s.-_ )+)\]' % (U + L)

# WIKILINK is just a combitation of the possibilities of WIKINAME1, WIKINAME2,
# BRACKETED_CONTENT and URL.
#
# ! is to escape wiki names.
# Examples:
# OpenMind
# !OpenMind
# etc.
WIKILINK  = r'!?(%s|%s|%s|%s|%s)' % (WIKINAME1, WIKINAME2, TRIPLE_BRACKETED_CONTENT,
                                     BRACKETED_CONTENT, URL)
WIKILINK_REGEXP = re.compile(WIKILINK, re.DOTALL | re.UNICODE)
BRACKETED_CONTENT_REGEXP = re.compile(BRACKETED_CONTENT)
TRIPLE_BRACKETED_CONTENT = re.compile(TRIPLE_BRACKETED_CONTENT)
STRICT_BRACKETED_CONTENT_REGEXP = re.compile(STRICT_BRACKETED_CONTENT)

class BaseParser:
    __implements__ = (IWikiParser,)

    wiki = None
    linked_pages = []

    def getId(self):
        return 'baseparser'

    def parseContent(self, content, wiki):
        """Returns the render of the provided content along with references on
        the linked pages and potentially linked pages.

        content may be either a unicode string or an UTF-8 encoded string.
        Of course it's best to use unicode strings whenever possible, but the
        ReST parser generates only UTF-8 encoded string so we have to able to
        process that type too.
        """
        self.wiki = wiki
        self.linked_pages = []
        self.potential_linked_pages = []

        if isinstance(content, str):
            content = unicode(content, 'utf-8')

        # A regexp can either have a replacement string or a replacement
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

        # If it's a bracketed expression

        if TRIPLE_BRACKETED_CONTENT.match(m):
            unbracketed_m = m[3:-3]
            handled, value = renderBrackets(unbracketed_m, self, self.wiki)
            if handled:
                return value
            else:
                return m

        elif BRACKETED_CONTENT_REGEXP.match(m):
            # Strip the enclosing []'s
            unbracketed_m = m[1:-1]

            handled, value = renderBrackets(unbracketed_m, self, self.wiki)

            if handled:
                return value

            if STRICT_BRACKETED_CONTENT_REGEXP.match(m):
                # extract a (non-url) path if there is one
                pathmatch = re.match(r'(([^/]*/)+)([^/]+)', unbracketed_m)
                if pathmatch:
                    path, id = pathmatch.group(1), pathmatch.group(3)
                else:
                    path, id = '', unbracketed_m

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
        stripped_label = m.strip('[').strip(']')
        m_nospace = generateId(stripped_label, lower=False)

        wiki_url = self.wiki.absolute_url()

        if (wiki is not None) and (m_nospace in wiki.objectIds()):
            if m_nospace not in self.linked_pages:
                self.linked_pages.append(m_nospace)

            return '<a href="%s/%s/cps_wiki_pageview">%s</a>' % (wiki_url, quote(m_nospace),
                                                                 stripped_label)
        else:
            # Adding a potential page
            if m_nospace not in self.potential_linked_pages:
                self.potential_linked_pages.append(m_nospace)

            # Providing a "?" creation link
            root = self.wiki.absolute_url()

            # In Python 2.x quote does not support unicode string
            stripped_label = stripped_label.encode('utf-8')
            return '%s<a href="%s/addPage?title=%s">?</a>' % (morig, wiki_url,
                                                              quote(stripped_label))
