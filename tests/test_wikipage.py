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
from Products.CPSWiki.wikiversionning import VersionContent

class WikiPageTests(ZopeTestCase):

    def test_instance(self):
        wikipage = WikiPage('page')
        self.assertNotEquals(wikipage, None)

    def test_rendering(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        page = wiki.addWikiPage('my page')
        page.source = VersionContent('once again')
        self.assertEquals(page.getParserType(), 'zwiki')
        self.assertEquals(page.render(), 'once again')

        page.source = VersionContent('once[again] again')
        self.assertEquals(page.render(),
            'once[again]<a href="../addWikiPage?title=again">?</a> again')

        wiki.parser = 'dummy'
        page = wiki.addWikiPage('my page')
        page.source = VersionContent('once again')
        self.assertEquals(page.getParserType(), 'dummy')
        self.assertEquals(page.render(), 'once again')

    def test_rendering_bad_content(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        page = wiki.addWikiPage('')
        page.source = VersionContent('<ba>my dcds</ba>dcdscdscdscsd')
        self.assertEquals(page.render(), '<ba>my dcds</ba>dcdscdscdscsd')

    def test_renderLinks(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        page = wiki.addWikiPage('my page')
        res = page.renderLinks('once [my link] again')
        self.assertEquals(res, 'once [my link]<a href="../addWikiPage?title=my%20link">?</a> again')

    def test_deletePage(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        page = wiki.addWikiPage('my page')
        page.deletePage()
        self.assert_(wiki.getWikiPage('my page') is None)

    def test_versionning(self):
        wiki = Wiki('wiki')
        wiki.parser = 'zwiki'
        page = wiki.addWikiPage('my page')
        page.editPage(source='hello')
        page.editPage(source='hello, how are you doing ?')
        page.editPage(source='hello, how are you doing ?\r\nMe fine.')
        res = page.getAllDiffs()
        self.assertEquals(res, ['+ hello', '+ , how are you doing ?',
                                '+ \r\nMe fine.'])
        page.editPage(source='hello, how do you do ?\r\nMe fine.')
        res = page.getAllDiffs()
        self.assertEquals(res, ['+ hello', '+ , how are you doing ?',
                                '+ \r\nMe fine.', '+ do\r\n- areing'])

        page.restoreVersion(1)
        self.assertEquals(page.source.getLastVersion(),
                          ('hello, how are you doing ?', {}))

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