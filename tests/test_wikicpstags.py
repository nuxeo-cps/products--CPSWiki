# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziadé <tz@nuxeo.com>
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
# $Id: test_baseparser.py 27709 2005-09-29 12:11:14Z madarche $
import unittest
from Testing.ZopeTestCase import ZopeTestCase, _print
from Products.CPSWiki.wikicpstags import MemberInfos

class FakePortalUrl:
    def getPortalPath(self):
        return 'cps'

    def getRelativeUrl(self, element):
        return 'http://xxx/' + element.absolute_url()

    def __call__(self):
        return 'http://xxx/'

class FakePortal:
    portal_url = FakePortalUrl()

class MemberInfosTests(ZopeTestCase):
    portal = FakePortal()

    def test_parsing(self):
        mi = MemberInfos()
        link = 'cps/cpsdirectory_entry_view?dirname=members&id=tarek'

        result = mi.render(self.portal, 'tarek')
        self.assertEquals(result, '<a href="%s">tarek</a>' % link)

        result = mi.render(self.portal, 'tarek, title')
        self.assertEquals(result, '<a href="%s">title</a>' % link)

        result = mi.render(self.portal, '')
        self.assertEquals(result, '')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(MemberInfosTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
