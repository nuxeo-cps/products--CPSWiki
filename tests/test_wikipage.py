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

from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.wikipage import WikiPage
from Products.CPSWiki.wiki import Wiki
from Products.CPSWiki.wikiversionning import VersionContent
from Products.CPSWiki.wikiparsers import parsers

class WikiPageTests(ZopeTestCase):

    def _getCurrentUser(self):
        return 'the user'

    def _getCurrentUser2(self):
        return 'the second user'

    def test_instance(self):
        wikipage = WikiPage('page')
        self.assertNotEquals(wikipage, None)

    def test_rendering(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser

        wiki.parser = 'zwiki'
        page = wiki.addWikiPage('my page')
        page.source = VersionContent('once again')
        self.assertEquals(page.getParserType(), 'zwiki')
        self.assertEquals(page.render(), 'once again')

        page.source = VersionContent('once[again] again')
        self.assertEquals(page.render(),
            'once[again]<a href="../addWikiPage?title=again">?</a> again')

        wiki.parser = 'restructuredtext'
        page = wiki.addWikiPage('my page')
        page.source = VersionContent('once again')
        self.assertEquals(page.getParserType(), 'restructuredtext')
        # XXX: (madarche) Why does this tests give different results on my
        # machine and while run as a part of the Nuxeo unit tests suites?
        #self.assertEquals(page.render(), '<p>once again</p>\n')
        self.assertEquals(page.render(), '<div class="document">\nonce again</div>\n')

    def test_rendering_bad_content(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addWikiPage('')
        page.source = VersionContent('<ba>my dcds</ba>dcdscdscdscsd')
        self.assertEquals(page.render(), '<ba>my dcds</ba>dcdscdscdscsd')

    def test_renderLinks(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addWikiPage('my page')
        res = page.renderLinks('once [my link] again')
        self.assertEquals(res, 'once [my link]<a href="../addWikiPage?title=my%20link">?</a> again')

    def test_deletePage(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addWikiPage('my page')
        page.deletePage()
        self.assert_(wiki.getWikiPage('my page') is None)

    def test_versionning(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addWikiPage('my page')
        page.editPage(source='hello')
        page.editPage(source='hello, how are you doing ?')
        page.editPage(source='hello, how are you doing ?\nMe fine.')

        res = page.getAllDiffs()
        self.assertEquals(len(res), 4)

        page.editPage(source='hello, how do you do ?\nMe fine.')

        res = page.getAllDiffs()
        self.assertEquals(len(res), 5)

        page.restoreVersion(1)
        self.assertEquals(page.source.getLastVersion()[0],
                          'hello, how are you doing ?')

    def test_getDifferences(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addWikiPage('my page')
        page.editPage(source='hello')
        page.editPage(source='hello, how are you doing ?')

        res = page.getDifferences(0, 1)
        self.assertEquals(res, '+ hello')

        res = page.getDifferences(1, 2)
        self.assertEquals(res, '- hello+ hello, how are you doing ?')

    def test_locking(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addWikiPage('my page')
        self.assert_(page.editPage(source='hello'))
        page.lockPage()    # user locks the page (done by template)

        # second user comes
        wiki._getCurrentUser = self._getCurrentUser2
        self.assert_(not page.editPage(source='hello all')) # uneditable
        self.assertEquals(page.render(), 'hello')

        # first user finish his work
        wiki._getCurrentUser = self._getCurrentUser
        self.assert_(page.editPage(source='hello all you'))  # unlocks
        self.assertEquals(page.render(), 'hello all you')

        #second user is good to go now
        wiki._getCurrentUser = self._getCurrentUser2
        self.assert_(page.editPage(source='hello all'))
        self.assertEquals(page.render(), 'hello all')

        # check history
        res = page.getAllDiffs()
        self.assertEquals(len(res), 4)

    def test_encoding(self):
        for parser in parsers:
            wiki = Wiki('wiki for parser "%s"' % parser)
            wiki.parser = parser
            wiki._getCurrentUser = self._getCurrentUser

            # Testing edit and rendering of a page using default encoding,
            # typically ISO-8859-15.
            content = "C'est éeéfffélo là et où donc ?"
            page = wiki.addWikiPage('Page 1: with default encoding')
            self.assert_(page.editPage(source=content))
            if parser == 'restructuredtext':
                self.assertEquals(page.render(), '<p>%s</p>\n' % content)
            else:
                self.assertEquals(page.render(), content)

            # TODO: When CPS accepts unicode we will decomment this test
            # Testing edit and rendering of a page using unicode encoding
##             content = u"C'est éeéfffélo là et où donc ?"
##             page = wiki.addWikiPage('Page 2: with Unicode')
##             self.assert_(page.editPage(source=content))
##             if parser == 'restructuredtext':
##                 self.assertEquals(page.render(), '<p>%s</p>\n' % content)
##             else:
##                 self.assertEquals(page.render(), content)

            # Testing the creation of a page with accented characters
            page = wiki.addWikiPage('éeedzzzzzzzzéé à doù !')


def test_suite():
    """
    return unittest.TestSuite((
        DocTestSuite('Products.CPSWiki.wikipage'),
        unittest.makeSuite(WikiPageTests),
        ))
    """
    return unittest.TestSuite((
        unittest.makeSuite(WikiPageTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
