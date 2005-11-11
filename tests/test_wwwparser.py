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
from Products.CPSWiki.wwwparser import WwwParser
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):

    def test_parsing(self):
        parser = WwwParser()

        res = parser.parseContent("qzp '''strong''' ideee", None)
        self.assertEquals(res, ('qzp <STRONG>strong</STRONG> ideee', [], []))

        res = parser.parseContent("qzpijdspjvd http://foo.bar vjpdsovj", None)
        self.assertEquals(res,
          ('qzpijdspjvd <a href="http://foo.bar">http://foo.bar</a> vjpdsovj',
           [], []))


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
