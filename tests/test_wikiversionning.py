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

    def test_getDiffs(self):
        vc = VersionContent('first line')
        vc.appendVersion('first line added part\n one more line')
        vc.appendVersion('first line yes added part\n one line')
        vc.appendVersion('first line \n second line yes added part\n one ine')
        diff = vc.getDiffs(0, 1)
        self.assertEquals(diff, '- first line+ first line added part\n+  one more line')
        diff = vc.getDiffs(1, 2)
        self.assertEquals(diff, '- first line added part\n+ first line yes added part\n?           ++++\n-  one more line?    -----\n+  one line')
        diff = vc.getDiffs(2, 3)
        self.assertEquals(diff, '+ first line \n- first line yes added part\n? ^^^ ^\n+  second line yes added part\n? ^ ^^^^^\n-  one line?      -\n+  one ine')
        diff = vc.getDiffs(0, 3)
        self.assertEquals(diff, '- first line+ first line \n?           ++\n+  second line yes added part\n+  one ine')
        diff = vc.getDiffs(1, 3)
        self.assertEquals(diff, '- first line added part\n-  one more line+ first line \n+  second line yes added part\n+  one ine')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(VersionContentTest),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
