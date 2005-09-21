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
import unittest
#from Testing.ZopeTestCase.doctest import DocTestSuite
from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.baseparser import BaseParser
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):

    def test_parsing(self):
        wiki = Wiki('wiki')

        parser = BaseParser()

        res = parser.parseContent(wiki, 'qzpijdspjvdspdsvjpdsovj')
        self.assertEquals(res, ([], 'qzpijdspjvdspdsvjpdsovj'))
        res = parser.parseContent(wiki, 'qzpijdspjvd [spds] vjpdsovj')
        self.assertEquals(res, ([],
            'qzpijdspjvd [spds]<a href="../addPage?title=spds">?</a> vjpdsovj'))

        wiki.addPage('spds')

        res = parser.parseContent(wiki, 'qzpijdspjvd [spds] vjpdsovj')
        self.assertEquals(res, (['spds'],
            'qzpijdspjvd <a href="../spds/cps_wiki_pageview">spds</a> vjpdsovj'))


    def test_weirdParsingcases(self):
        # Protect regexpr searches from weird characters.
        # trac ticket #698
        wiki = Wiki('wiki')
        parser = BaseParser()

        res = parser.parseContent(wiki, 'qzpijd [***] dsvjpdsovj')
        self.assertEquals(res, ([],
          'qzpijd [***]<a href="../addPage?title=%2A%2A%2A">?</a> dsvjpdsovj'))

        res = parser.parseContent(wiki, 'qzpijd [???] dsvjpdsovj')
        self.assertEquals(res, ([],
          'qzpijd [???]<a href="../addPage?title=%3F%3F%3F">?</a> dsvjpdsovj'))

        res = parser.parseContent(wiki, 'qzpijd [?a?] dsvjpdsovj')
        self.assertEquals(res, ([],
          'qzpijd [?a?]<a href="../addPage?title=%3Fa%3F">?</a> dsvjpdsovj'))

        res = parser.parseContent(wiki, 'qzpijd [[junk] dsvjpdsovj')
        self.assertEquals(res, ([],
          'qzpijd [[junk]<a href="../addPage?title=junk">?</a> dsvjpdsovj'))

        res = parser.parseContent(wiki, 'qzpijd [[Junk] dsvjpdsovj')
        self.assertEquals(res, ([],
          'qzpijd [[Junk]<a href="../addPage?title=Junk">?</a> dsvjpdsovj'))

        res = parser.parseContent(wiki, 'qzpijd [[Detaxe]] dsvjpdsovj')
        self.assertEquals(res, ([],
          'qzpijd [[Detaxe]<a href="../addPage?title=Detaxe">?</a>] dsvjpdsovj'))


def test_suite():
    """
    return unittest.TestSuite((
        DocTestSuite('Products.CPSWiki.wiki'),
        unittest.makeSuite(Test),
        ))
    """
    return unittest.TestSuite((
        unittest.makeSuite(WikiParserTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
