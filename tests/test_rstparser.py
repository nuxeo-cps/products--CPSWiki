# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
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
from Products.CPSWiki.rstparser import RstParser
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):

    def testParsing(self):
        parser = RstParser()
        res = parser.parseContent("""
Title
-----

Some content.

""", None)
        self.assertEquals(res, ("""<h2 class="title">Title</h2>\n<p>Some content.</p>\n""", [], []))

        res = parser.parseContent("This web site http://foo.bar that is", None)
        self.assertEquals(res,
          ("""<p>This web site <a class="reference" href="http://foo.bar"><a href="http://foo.bar">http://foo.bar</a></a> that is</p>\n""",
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
