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

from ZPublisher.HTTPRequest import FileUpload

from Products.CPSWiki.tests.wiki_test_case import WikiTestCase
from Products.CPSWiki.wikipage import WikiPage
from Products.CPSWiki.wiki import Wiki
from Products.CPSWiki.wikiparsers import parsers

try:
    from reStructuredText import HTML
    has_rst = True
except ImportError:
    has_rst = False

class FakeFieldStorage:
    file = None
    filename = ''
    headers = []

class WikiPageTests(WikiTestCase):

    def test_instance(self):
        wikipage = WikiPage('page')
        self.assertNotEquals(wikipage, None)

    def _wiki_url(self):
        return 'http://xxx'

    def test_rendering(self):
        wiki = Wiki('wiki')
        wiki.absolute_url = self._wiki_url
        wiki._getCurrentUser = self._getCurrentUser

        wiki.parser = 'zwiki'
        page = wiki.addPage('my page')
        page.edit(source='once again')
        self.assertEquals(page.getParserType(), 'zwiki')
        self.assertEquals(page.render(), 'once again')

        page.edit(source='once[again] again')
        self.assertEquals(page.render(),
                          'once[again]<a href="http://xxx/addPage?title=again">?</a> again')

        if has_rst:
            wiki.parser = 'restructuredtext'
            page = wiki.addPage('another page')
            page.edit(source='once again')
            self.assertEquals(page.getParserType(), 'restructuredtext')
            self.assertEquals(page.render(), '<p>once again</p>\n')

    def test_renderingBadHtmlContent(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('')
        page.edit(source='<ba>my dcds</ba> dcdscdscdscsd')
        self.assertEquals(page.render(), 'my dcds dcdscdscdscsd')

    def test_links(self):
        wiki = Wiki('wiki')
        wiki.absolute_url = self._wiki_url
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('my page')
        page.edit(source='once[again] again')
        page.clearCache()
        self.assertEquals(page.render(),
                          'once[again]<a href="http://xxx/addPage?title=again">?</a> again')
        self.assertEquals(page.getLinkedPages(), [])
        self.assertEquals(page.getPotentialLinkedPages(), ['again'])


    def test_delete(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('my page')
        page.delete()
        self.assert_(wiki.getPage('my page') is None)
        self.assert_(wiki.getSummary() is not None)


    def test_versionning(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('my page')
        page.edit(source='hello')
        page.edit(source='hello, how are you doing ?')
        page.edit(source='hello, how are you doing ?\nMe fine.')

        res = page.getAllDiffs()
        self.assertEquals(len(res), 4)

        page.edit(source='hello, how do you do ?\nMe fine.')

        res = page.getAllDiffs()
        self.assertEquals(len(res), 5)

        page.restoreVersion(1)
        self.assertEquals(page.source.getLastVersion()[0],
                          'hello, how are you doing ?')

    def test_getDiffs(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('my page')
        page.edit(source='hello')
        page.edit(source='hello, how are you doing ?')

        res = page.getDiffs(0, 1)
        self.assertEquals(res, '+ hello\n')

        res = page.getDiffs(1, 2)
        self.assertEquals(res, '- hello\n+ hello, how are you doing ?\n')

    def test_locking(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('my page')
        self.assert_(page.edit(source='hello'))
        page.lockPage()    # user locks the page (done by template)

        # second user comes
        wiki._getCurrentUser = self._getCurrentUser2
        self.assert_(not page.edit(source='hello all')) # uneditable
        self.assertEquals(page.render(), 'hello')

        # first user finish his work
        wiki._getCurrentUser = self._getCurrentUser
        self.assert_(page.edit(source='hello all you'))  # unlocks
        self.assertEquals(page.render(), 'hello all you')

        #second user is good to go now
        wiki._getCurrentUser = self._getCurrentUser2
        self.assert_(page.edit(source='hello all'))
        self.assertEquals(page.render(), 'hello all')

        # check history
        res = page.getAllDiffs()
        self.assertEquals(len(res), 4)

    def test_encoding(self):
        tested_parsers = parsers
        if not has_rst:
            if 'restructuredtext' in  tested_parsers:
                tested_parsers.remove('restructuredtext')

        for parser in tested_parsers:
            # if the test machine has no rst, we skip it here
            wiki = Wiki('wiki for parser "%s"' % parser)
            wiki.parser = parser
            wiki._getCurrentUser = self._getCurrentUser

            # Testing edit and rendering of a page using default encoding,
            # typically ISO-8859-15.
            content = "C'est éeéfffélo là et où donc ?"
            page = wiki.addPage('Page 1: with default encoding')
            self.assert_(page.edit(source=content))
            if parser == 'restructuredtext':
                self.assertEquals(page.render(), '<p>%s</p>\n' % content)
            else:
                self.assertEquals(page.render(), content)

            # just checking that given parser support unicoding as well
            content = u"C'est éeéfffélo là et où donc ?"
            page = wiki.addPage(u'Page 2: with Unicode')
            self.assert_(page.edit(source=content))
            if parser == 'restructuredtext':
                render = page.render()
                expected_render = ('<p>%s</p>\n'
                                   % content).encode(wiki.getParser()
                                                     .output_encoding)
                self.assertEquals(render, expected_render)
            else:
                self.assertEquals(page.render(), content)

            # Testing the creation of a page with accented characters
            page = wiki.addPage('éeedzzzzzzzzéé à doù !')

    def test_getLinkedPages(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('page1')
        page1.edit(source=' page 1 ')
        page3 = wiki.addPage('page3')
        page3.edit(source=' page 1 ')
        page2 = wiki.addPage('page2')
        page2.edit(source=
            ' link to [page1] again [page1] and [page3] and [page6]')
        self.assertEquals(page2.getLinkedPages(), ['page1', 'page3'])
        self.assertEquals(page1.getLinkedPages(), [])

    def test_getBackedLinkedPages(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('page1')
        page1.edit(source=' page 1 ')
        page3 = wiki.addPage('page3')
        page3.edit(source=' page 1 ')
        page2 = wiki.addPage('page2')
        page2.edit(source=
            ' link to [page1] again [page1] and [page3] and [page6]')

        self.assertEquals(page1.getBackedLinkedPages(), ['page2'])
        self.assertEquals(page2.getBackedLinkedPages(), [])

    def test_uploadFile(self):
        # using current file for tests
        file = open(__file__, 'r')
        storage = FakeFieldStorage()
        storage.file = file
        storage.filename = 'yopla'

        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('page1')
        self.assertEquals(page1.objectIds(), [])
        upload = FileUpload(storage)
        page1.uploadFile(upload)
        self.assertEquals(page1.objectIds(), ['yopla'])
        file.close()

        self.assert_(page1.uploadFile('nnn', None) == False)
        self.assert_(page1.uploadFile(None, None) == False)

    def test_jedit(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('page1')
        page1.jedit(source='tÃ©tÃ©tÃ©')
        self.assertEquals(page1.render(), '<p>tétété</p>\n')


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
