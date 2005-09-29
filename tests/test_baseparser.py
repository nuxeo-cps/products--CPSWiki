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
import unittest
#from Testing.ZopeTestCase.doctest import DocTestSuite
from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.baseparser import BaseParser
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):

    def test_parsing(self):
        wiki = Wiki('wiki')

        parser = BaseParser()

        # Testing no links
        res = parser.parseContent('qzpijdspjvdspdsvjpdsovj', wiki)
        self.assertEquals(res, ('qzpijdspjvdspdsvjpdsovj', [], []))

        # Testing potential links
        res = parser.parseContent('I want to create MyPage', wiki)
        self.assertEquals(res,
          ('I want to create MyPage<a href="../addPage?title=MyPage">?</a>',
           [], ['MyPage']))

        res = parser.parseContent('I want to create MyPage I said.', wiki)
        self.assertEquals(res,
          ('I want to create MyPage<a href="../addPage?title=MyPage">?</a> I said.',
           [], ['MyPage']))

        res = parser.parseContent('MyPage\n\nAnotherProduct\n\nTryMe.', wiki)
        self.assertEquals(res,
          ('MyPage<a href="../addPage?title=MyPage">?</a>\n\n'
           'AnotherProduct<a href="../addPage?title=AnotherProduct">?</a>\n\n'
           'TryMe<a href="../addPage?title=TryMe">?</a>.',
           [], ['MyPage', 'AnotherProduct', 'TryMe']))

        res = parser.parseContent('qzpijdspjvd [spds] vjpdsovj', wiki)
        self.assertEquals(res,
          ('qzpijdspjvd [spds]<a href="../addPage?title=spds">?</a> vjpdsovj',
           [], ['spds']))

        # Testing found links
        wiki.addPage('spds')
        res = parser.parseContent('qzpijdspjvd [spds] vjpdsovj', wiki)
        self.assertEquals(res,
          ('qzpijdspjvd <a href="../spds/cps_wiki_pageview">spds</a> vjpdsovj',
           ['spds'], []))


    def test_weirdParsingCases(self):
        # Checking that weird characters and expressions dont' break the
        # rendering.
        # trac ticket #698
        wiki = Wiki('wiki')
        parser = BaseParser()

        res = parser.parseContent('qzpijd [***] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [***]<a href="../addPage?title=%2A%2A%2A">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [???] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [???]<a href="../addPage?title=%3F%3F%3F">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [?a?] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [?a?]<a href="../addPage?title=%3Fa%3F">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [[junk] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [[junk]<a href="../addPage?title=junk">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [[Junk] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [[Junk]<a href="../addPage?title=Junk">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [[Detaxe]] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [[Detaxe]<a href="../addPage?title=Detaxe">?</a>] dsvjpdsovj')


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
