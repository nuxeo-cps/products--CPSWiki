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
from Products.CPSWiki.htmlsanitizer import sanitize, remove_attributes

class HTMLSanitizerTests(unittest.TestCase):


    def tests(self):
        res = sanitize('<html>ftgyuhjik</html>')
        self.assertEquals(res, 'ftgyuhjik')

        res = sanitize('<html>ftg<b>yuh  </b>jik</html>')
        self.assertEquals(res, 'ftg<b>yuh  </b>jik')

        res = sanitize('yu<script langage="javascript">h</script></c>')
        self.assertEquals(res, 'yuh')

        res = remove_attributes('dfrtgyhju<span class="myclass" >ghj</span>', ('class',))
        self.assertEquals(res, 'dfrtgyhju<span >ghj</span>')

        res = remove_attributes('<a href="../../../../../../../view" accesskey="U" title="wii" _base_href="http://localhost:29980/cps2/sections/wii/we/">wii</a>', ('accesskey',))

        self.assertEquals(res, '<a href="../../../../../../../view"  title="wii" _base_href="http://localhost:29980/cps2/sections/wii/we/">wii</a>')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(HTMLSanitizerTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')