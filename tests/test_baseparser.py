# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziade <tz@nuxeo.com>
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

import unittest
import re
from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.baseparser import BaseParser, WIKILINK_REGEXP
from Products.CPSWiki.wiki import Wiki

class WikiParserTest(ZopeTestCase):
    def _wiki_url(self):
        return 'http://xxx'

    def test_parsing(self):
        wiki = Wiki('wiki')
        wiki.absolute_url = self._wiki_url

        parser = BaseParser()

        # Testing no links
        res = parser.parseContent('qzpijdspjvdspdsvjpdsovj', wiki)
        self.assertEquals(res, ('qzpijdspjvdspdsvjpdsovj', [], []))

        # Testing potential links
        res = parser.parseContent('I want to create MyPage', wiki)
        self.assertEquals(res,
          ('I want to create MyPage<a href="http://xxx/addPage?title=MyPage">?</a>',
           [], ['MyPage']))

        res = parser.parseContent('I want to create MyPage I said.', wiki)
        self.assertEquals(res,
          ('I want to create MyPage<a href="http://xxx/addPage?title=MyPage">?</a> I said.',
           [], ['MyPage']))

        res = parser.parseContent('MyPage\n\nAnotherProduct\n\nTryMe.', wiki)
        self.assertEquals(res,
          ('MyPage<a href="http://xxx/addPage?title=MyPage">?</a>\n\n'
           'AnotherProduct<a href="http://xxx/addPage?title=AnotherProduct">?</a>\n\n'
           'TryMe<a href="http://xxx/addPage?title=TryMe">?</a>.',
           [], ['MyPage', 'AnotherProduct', 'TryMe']))

        res = parser.parseContent('qzpijdspjvd [spds] vjpdsovj', wiki)
        self.assertEquals(res,
          ('qzpijdspjvd [spds]<a href="http://xxx/addPage?title=spds">?</a> vjpdsovj',
           [], ['spds']))

        # Testing found links
        wiki.addPage('spds')
        res = parser.parseContent('qzpijdspjvd [spds] vjpdsovj', wiki)
        self.assertEquals(res,
          ('qzpijdspjvd <a href="http://xxx/spds/cps_wiki_pageview">spds</a> vjpdsovj',
           ['spds'], []))


    def test_weirdParsingCases(self):
        # Checking that weird characters and expressions dont' break the
        # rendering.
        # trac ticket #698
        wiki = Wiki('wiki')
        wiki.absolute_url = self._wiki_url

        parser = BaseParser()

        res = parser.parseContent('qzpijd [***] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [***]<a href="http://xxx/addPage?title=%2A%2A%2A">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [???] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [???]<a href="http://xxx/addPage?title=%3F%3F%3F">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [?a?] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [?a?]<a href="http://xxx/addPage?title=%3Fa%3F">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [[junk] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [[junk]<a href="http://xxx/addPage?title=junk">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [[Junk] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [[Junk]<a href="http://xxx/addPage?title=Junk">?</a> dsvjpdsovj')

        res = parser.parseContent('qzpijd [[Detaxe]] dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd [[Detaxe]<a href="http://xxx/addPage?title=Detaxe">?</a>] dsvjpdsovj')

        res = parser.parseContent("""
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/

CpsProject
""", wiki)
        self.assertEquals(res[1], [])
        self.assertEquals(res[2], ['CpsProject'])

        res = parser.parseContent("""
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/
http://www.cps-project.org/

CpsProject
""", wiki)
        self.assertEquals(res[1], [])
        self.assertEquals(res[2], ['CpsProject'])


    def test_triple_parsing(self):
        wiki = Wiki('wiki')
        parser = BaseParser()
        res = parser.parseContent('qzpijd {{{Dezd \n\n [triple] taxe}}} dsvjpdsovj', wiki)
        self.assertEquals(res[0],
          'qzpijd {{{Dezd \n\n [triple] taxe}}} dsvjpdsovj')

        text = ("{{{pycode: class BaseParser: __implements__ = (WikiParserInte"
        "rface,) wiki = None linked_pages = ['d'] def getId(self): return 'bas"
        "eparser' def parseContent(self, content, wiki): \"\"\"Return the render o"
        "df the provided content along with references on the linked pages and"
        " potentially linked pagesd. \"\"\" self.wiki = wiki self.linked_pa"
        "ges = [] self.potential_linked_pages = [] # A regexp can be with e"
        "ither a replacement string or a replacement # function. render ="
        "WIKILINK_REGEXP.sub(self._wikilinkReplace, content, re.M) return "
        "render, self.linked_pages, self.potential_linked_pages}}}")

        res = parser.parseContent(text, wiki)
        self.assert_(len(res[0]) >= len(text))


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
