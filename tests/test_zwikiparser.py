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
from Products.CPSWiki.zwikiparser import ZWikiParser
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):


    def test_parsing(self):
        wiki = Wiki('wiki')

        parser = ZWikiParser()

        res = parser.parseContent(wiki, 'qzpijdspjvdspdsvjpdsovj')
        self.assertEquals(res, 'qzpijdspjvdspdsvjpdsovj')
        res = parser.parseContent(wiki, 'qzpijdspjvd [spds] vjpdsovj')
        self.assertEquals(res,
            'qzpijdspjvd [spds]<a href="../addWikiPage?title=spds">?</a> vjpdsovj')

        wiki.addWikiPage('spds')

        res = parser.parseContent(wiki, 'qzpijdspjvd [spds] vjpdsovj')
        self.assertEquals(res,
            'qzpijdspjvd <a href="../spds/cps_wiki_pageview">spds</a> vjpdsovj')



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