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
# $Id: test_wikiversionning.py 28598 2005-10-25 10:05:37Z lregebro $

import unittest
from Products.CPSWiki.wikirelations import WikiRelation, DummyBackEnd

class FakeWikiPage:
    id = 'ok'

class WikiRelationsTest(unittest.TestCase):

    def test_DummyBackEnd(self):
        backend = DummyBackEnd()
        rel = backend.getRelationsFor('page1', 'linked_to')
        self.assertEquals(rel, [])

        backend.addRelationFor('page1', 'linked_to', 'page2')
        rel = backend.getRelationsFor('page1', 'linked_to')
        self.assertEquals(rel, ['page2'])

        backend.addRelationFor('page1', 'linked_to', 'page3')
        rel = backend.getRelationsFor('page1', 'linked_to')
        rel.sort()
        self.assertEquals(rel, ['page2', 'page3'])

        backend.deleteRelationFor('page1', 'linked_to', 'page3')
        rel = backend.getRelationsFor('page1', 'linked_to')
        self.assertEquals(rel, ['page2'])

    def test_WikiRelationsLinkedTo(self):

        rel = WikiRelation(FakeWikiPage())
        self.assertEquals(rel.isLinkedTo(), [])

        rel.addLinksTo(['1', '2', '3'])
        links = rel.isLinkedTo()
        links.sort()
        self.assertEquals(links, ['1', '2', '3'])

        rel.removeLinksTo(['nope', '2'])
        links = rel.isLinkedTo()
        links.sort()
        self.assertEquals(links, ['1', '3'])

    def test_WikiRelationsLinkableTo(self):

        rel = WikiRelation(FakeWikiPage())
        self.assertEquals(rel.isLinkableTo(), [])

        rel.addLinkablesTo(['1', '2', '3'])
        links = rel.isLinkableTo()
        links.sort()
        self.assertEquals(links, ['1', '2', '3'])

        rel.removeLinkablesTo(['nope', '2'])
        links = rel.isLinkableTo()
        links.sort()
        self.assertEquals(links, ['1', '3'])

    def test_WikiRelationsBLinkedTo(self):
        rel = WikiRelation(FakeWikiPage())
        self.assertEquals(rel.isBackLinkedTo(), [])

        rel.addBackLinksTo(['1', '2', '3'])
        links = rel.isBackLinkedTo()
        links.sort()
        self.assertEquals(links, ['1', '2', '3'])

        rel.removeBackLinksTo(['nope', '2'])
        links = rel.isBackLinkedTo()
        links.sort()
        self.assertEquals(links, ['1', '3'])

    def test_WikiRelationsisAbout(self):
        rel = WikiRelation(FakeWikiPage())
        self.assertEquals(rel.isAbout(), [])

        rel.addTopics(['1', '2', '3'])
        links = rel.isAbout()
        links.sort()
        self.assertEquals(links, ['1', '2', '3'])

        rel.removeTopics(['nope', '2'])
        links = rel.isAbout()
        links.sort()
        self.assertEquals(links, ['1', '3'])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WikiRelationsTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
