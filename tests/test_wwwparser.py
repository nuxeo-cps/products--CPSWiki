# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziade <tz@nuxeo.com>
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

import unittest
#from Testing.ZopeTestCase.doctest import DocTestSuite
from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.wwwparser import WwwParser
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):

    def test_parsing(self):
        wiki = Wiki('wiki')
        parser = WwwParser()

        res = parser.parseContent("qzp '''strong''' ideee", wiki)
        self.assertEquals(res, ('qzp <STRONG>strong</STRONG> ideee', [], []))

        res = parser.parseContent("qzpijdspjvd http://foo.bar vjpdsovj", wiki)
        self.assertEquals(res,
          ('qzpijdspjvd <a href="http://foo.bar">http://foo.bar</a> vjpdsovj',
           [], []))

        waited = ('http://www.cps-project.org/\n'
                  'http://www.cps-project.org/\n'
                  'http://www.cps-project.org/\n'
                  'http://www.cps-project.org/\n'
                  'http://www.cps-project.org/\n'
                  'http://www.cps-project.org/\n'
                  'http://www.cps-project.org/\n'
                  '\n'
                  'CpsProject\n')

        res = parser.parseContent(waited, wiki)

        self.assertEquals(res[1], [])
        self.assertEquals(res[2], ['CpsProject'])

        res = parser.parseContent(waited, wiki)
        self.assertEquals(res[1], [])
        self.assertEquals(res[2], ['CpsProject'])


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
