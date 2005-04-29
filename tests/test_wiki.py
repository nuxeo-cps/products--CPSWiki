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
from Products.CPSWiki.wiki import Wiki


class WikiTests(ZopeTestCase):

    def _getCurrentUser(self):
        return 'the user'

    def test_instance(self):
        wiki = Wiki('wiki')
        self.assertNotEquals(wiki, None)

    def test_addPage(self):
        wiki = Wiki('wiki')
        page = wiki.addPage('my page')
        self.assertNotEquals(page, None)
        self.assert_(page.title == 'my page')

    def test_deletePage(self):
        wiki = Wiki('wiki')
        page = wiki.addPage('my page')
        self.assertNotEquals(page, None)
        self.assert_(page.title == 'my page')
        wiki.deletePage('my page')
        self.assertEquals(wiki.objectIds(), [])

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
        self.assertEquals(len(summary), 1)


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

