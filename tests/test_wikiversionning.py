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
from Products.CPSWiki.wikiversionning import VersionContent

class VersionContentTest(unittest.TestCase):

    def test_versionning(self):
        vc = VersionContent('srdcftgyvbuhjnkl')

        self.assertNotEquals(vc, None)

        self.assertEquals(vc._primary, (['srdcftgyvbuhjnkl'], {}))
        self.assertEquals(vc.getLastVersion(), ('srdcftgyvbuhjnkl', {}))

        vc.appendVersion('srdcf      tgyvbuhjnkl')
        self.assertEquals(len(vc._versions), 1)
        self.assertEquals(vc.getLastVersion(), ('srdcf      tgyvbuhjnkl', {}))

        vc.appendVersion('srdcf      tgyvbdfzfeef uhjnkl')
        self.assertEquals(vc.getLastVersion(), ('srdcf      tgyvbdfzfeef uhjnkl', {}))

        vc.appendVersion('srdcDznkl')
        self.assertEquals(vc.getLastVersion(), ('srdcDznkl', {}))
        self.assertEquals(vc.getVersion(3), ('srdcDznkl', {}))

        self.assertEquals(vc.getVersion(0), ('srdcftgyvbuhjnkl', {}))
        self.assertEquals(vc.getVersion(1), ('srdcf      tgyvbuhjnkl', {}))
        self.assertEquals(vc.getVersion(2), ('srdcf      tgyvbdfzfeef uhjnkl', {}))


        for i in range(40):
            vc.appendVersion(str(i))

        self.assert_(len(vc._versions), 30)
        self.assertEquals(vc.getVersion(0), ('9', {}))
        self.assertEquals(vc.getVersion(29), ('38', {}))

    def test_getDifferences(self):
        vc = VersionContent('first line')
        vc.appendVersion('first line added part\r\none more line')
        vc.appendVersion('first line yes added part\r\none line')
        vc.appendVersion('first line \r\nsecond line yes added part\r\none ine')
        diff = vc.getDifferences(0, 1)
        self.assertEquals(diff, '+  added part\r\none more line')
        diff = vc.getDifferences(1, 2)
        self.assertEquals(diff, '+  yes\r\n- more ')
        diff = vc.getDifferences(2, 3)
        self.assertEquals(diff, '+  line \r\nsecond\r\n- l')
        diff = vc.getDifferences(0, 3)
        self.assertEquals(diff, '+  \r\nsecond line yes added part\r\none ine')
        diff = vc.getDifferences(1, 3)
        self.assertEquals(diff, '+  \r\nsecond line yes\r\n- more l')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(VersionContentTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')