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
from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.wikipage import WikiPage
from Products.CPSWiki.wiki import Wiki

class WikiPageTests(ZopeTestCase):

    def test_instance(self):
        wikipage = WikiPage('page')
        self.assertNotEquals(wikipage, None)

    def test_rendering(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'

        page = wiki.addWikiPage('my page')
        page.source = 'once again'

        self.assertEquals(page.render(), 'once again')

        page.source = 'once[again] again'
        self.assertEquals(page.render(),
            'once[again]<a href="../addWikiPage?title=again">?</a> again')

        wiki.parser = 'dummy'

        page = wiki.addWikiPage('my page')
        page.source = 'once again'

        self.assertEquals(page.render(), 'once again')


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