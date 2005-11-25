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

from cStringIO import StringIO
from OFS.Image import Image, File
from OFS.Folder import Folder

from Products.CPSWiki.tests.wiki_test_case import WikiTestCase
from Products.CPSWiki.wiki import Wiki


class WikiTests(WikiTestCase):

    def _wiki_url(self):
        return 'http://xxx'

    def test_instance(self):
        wiki = Wiki('wiki')
        self.assertNotEquals(wiki, None)

    def test_addPage(self):
        wiki = Wiki('wiki')
        page = wiki.addPage('my page')
        self.assertNotEquals(page, None)
        self.assertEquals(page.title, 'my page')

        # It should be impossible to create a page with the same title
        try:
            page = wiki.addPage('my page')
        except ValueError, exception:
            self.assertEquals(str(exception),
                              "The ID \"my-page\" is already in use.")


    def test_wikiWithPagesAndObjects(self):
        # Testing that the wiki is not broken if it contains not only wiki pages
        # but also images and files as a real life wiki does.
        wiki = Wiki('wiki')

        page1 = wiki.addPage('my page 1')
        page2 = wiki.addPage('my page 2')
        obj1 = File('my file id', 'my file title', StringIO())
        wiki._setObject('my file', obj1)
        obj2 = File('my image id', 'my image title', StringIO())
        wiki._setObject('my image', obj2)
        obj3 = Folder('my folder id')
        wiki._setObject('my folder', obj3)

        # There are now 5 objects in the wiki
        self.assertEquals(len(wiki.objectItems()), 5)

        # No operations should break
        self.assertNotEquals(wiki.getSummary(), None)
        self.assertEquals(wiki.clearCaches(), None)
        for page in (page1, page2):
            self.assertNotEquals(page.render(), None)
            self.assertNotEquals(page.getLinkedPages(), None)
            self.assertNotEquals(page.getPotentialLinkedPages(), None)
            self.assertNotEquals(page.getBackedLinkedPages(), None)


    def test_renderingAfterAddPage(self):
        # Testing the fix for #833
        # XXX need to take care of boxes that does not have rest installed
        wiki = Wiki('wiki')
        wiki.absolute_url = self._wiki_url

        wiki._getCurrentUser = self._getCurrentUser

        page1 = wiki.addPage('MyPage')
        page1.edit(source='AnotherPage')
        self.assertEquals(page1.render(),
          '<p>AnotherPage<a href="http://xxx/addPage?title=AnotherPage">?</a></p>\n')
        self.assertEquals(page1.getLinkedPages(), [])
        self.assertEquals(page1.getPotentialLinkedPages(), ['AnotherPage'])
        page2 = wiki.addPage('AnotherPage')
        # The potential link has become an actual link
        self.assertEquals(page1.render(),
          '<p><a href="http://xxx/AnotherPage/cps_wiki_pageview">AnotherPage</a></p>\n')
        self.assertEquals(page1.getLinkedPages(), ['AnotherPage'])
        self.assertEquals(page1.getPotentialLinkedPages(), [])


    def test_deletePage(self):
        wiki = Wiki('wiki')
        page = wiki.addPage('my page')
        self.assertNotEquals(page, None)
        self.assertEquals(page.title, 'my page')
        wiki.deletePage('my page')
        self.assertEquals(wiki.objectIds(), [])

    def test_deletePageCleanCache(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('my page')
        page1.edit(source='AnotherPage')
        page2 = wiki.addPage('AnotherPage')
        self.assertEquals(page1.getLinkedPages(), ['AnotherPage'])
        wiki.deletePage('AnotherPage')
        self.assertEquals(page1.getLinkedPages(), [])

    def test_deletePageCleanCache2(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('my page')
        page1.edit(source='AnotherPage')
        page2 = wiki.addPage('AnotherPage')
        self.assertEquals(page1.getLinkedPages(), ['AnotherPage'])
        wiki.manage_delObjects(['AnotherPage'])
        self.assertEquals(page1.getLinkedPages(), [])

    def test_locking(self):
        wiki = Wiki('wiki')

        wiki._getCurrentUser = self._getCurrentUser

        page = wiki.addPage('my page')
        li = wiki.pageLockInfo(page)
        self.assertEquals(li, None)

        wiki.lockPage(page)
        li = wiki.pageLockInfo(page)
        self.assertEquals(li[1], 'the user')

        wiki.unLockPage(page)
        li = wiki.pageLockInfo(page)
        self.assertEquals(li, None)


    def test_getSummary(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser

        page1 = wiki.addPage('page1')
        page2 = wiki.addPage('page2')
        page3 = wiki.addPage('page3')
        page3.edit(source=' dddddd [page2] zaaaaaza ')
        page4 = wiki.addPage('page4')
        page5 = wiki.addPage('page5')
        page5.edit(source=' dddddd [page2] za [page1] aaaaza ')

        summary = wiki.getSummary()

        self.assertEquals(len(summary), 3)

        # adding a circular link to make sure wiki summary knows ho to deal it
        page2.edit(source=' dddddd [page5] za [page3] aaaaza ')

        summary = wiki.getSummary()
        self.assertEquals(len(summary), 2)

    def test_getSummary2(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser
        page1 = wiki.addPage('page1')
        page1.edit(source=' dddddd [page2] zaaaaaza [page3]')
        page2 = wiki.addPage('page2')
        page1.edit(source=' dddddd [page4] zaaaaaza [page7]')
        page3 = wiki.addPage('page3')
        page3.edit(source=' dddddd [page1] zaaaaaza [page7]')
        page4 = wiki.addPage('page4')
        page7 = wiki.addPage('page7')
        page7.edit(source=' dddddd [page1] zaaaaaza')

        summary = wiki.getSummary()
        self.assertEquals(len(summary), 3)




    def test_recursiveGetLinks(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser

        page1 = wiki.addPage('page1')
        page1.edit(source=' dddddd [page2]')
        page2 = wiki.addPage('page2')
        page2.edit(source=' dddddd [page3]')
        page3 = wiki.addPage('page3')

        content = wiki._recursiveGetLinks(page1)
        sub = content[0]
        self.assertEquals(sub['page'], page2)


    def test_clearCaches(self):
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser

        page1 = wiki.addPage('page1')
        page1.edit(source=' dddddd [page2]')
        page2 = wiki.addPage('page2')
        page2.edit(source=' dddddd [page3]')
        page3 = wiki.addPage('page3')

        page1.render()
        page2.render()

        summary = wiki.getSummary()

        self.assert_(page1._render is not None)
        self.assert_(page2._render is not None)

        wiki.clearCaches()

        self.assert_(page1._render is None)
        self.assert_(page2._render is None)

    def test_recursiveGetLinks_circular(self):
        # this would lead to a maximum recursion depth exceeded
        # when a page is refering to itself
        wiki = Wiki('wiki')
        wiki._getCurrentUser = self._getCurrentUser

        page1 = wiki.addPage('page1')
        page1.edit(source=' dddddd [page1] [page 2] ezfezf')

        page2 = wiki.addPage('page2')
        page2.edit(source=' dddddd [page 3] ezfezf')

        page3 = wiki.addPage('page3')
        page3.edit(source=' dddddd [page1] [page 2] ezfezf')

        summary = wiki.getSummary()

    def test_changeProperties(self):
        wiki = Wiki('wiki')
        wiki.changeProperties(parser='wikiwikiweb')
        self.assertEquals(wiki.parser, 'wikiwikiweb')
        wiki.changeProperties(parser='html')
        self.assertEquals(wiki.parser, 'html')

    def test_instanceversion(self):
        # making sure wiki versions are independant
        wiki_1 = Wiki('wiki1')
        wiki_1.version= (0, 6)
        wiki_2 = Wiki('wiki2')
        wiki_2.version = (0, 3)
        self.assertNotEquals(wiki_1.version, wiki_2.version)

def test_suite():
    """
    return unittest.TestSuite((
        DocTestSuite('Products.CPSWiki.wiki'),
        unittest.makeSuite(Test),
        ))
    """
    return unittest.TestSuite((
        unittest.makeSuite(WikiTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
