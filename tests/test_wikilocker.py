# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziade <tz@nuxeo.com>
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

import unittest
from Products.CPSWiki.wikilocker import LockerList, ILockableItem
import Interface
from time import time, sleep

class LockItem:
    __implements__ = (ILockableItem, )

    def __init__(self, uri, info, duration):
        self.uri = uri
        self.info = info
        self.duration = duration

    def getURI(self):
        return self.uri

    def getLockInfo(self):
        return self.info

    def getLockDuration(self):
        return self.duration


class WikiLockingTests(unittest.TestCase):

    def test_locking(self):
        locker = LockerList()

        # locker checks if the object is lockable
        self.assertRaises(Exception, locker.addItem, 'nope')

        # locker returns non when asking an unknown item
        infos = locker.getItemInfo('hey')
        self.assertEquals(infos, None)

        # now adding a lockable item - 0.5 seconds
        item = LockItem('URI', 'INFO', 0.5)
        now = time()

        locker.addItem(item)

        self.assert_(locker.has_key('URI'))    # low-level check

        # check access
        infos = locker.getItemInfo('URI')
        self.assertNotEquals(infos, None)
        self.assertEquals(infos[1], 'INFO')

        # check expiration
        TTL = infos[2]

        # time to live is between 0 and 1
        self.assert_(TTL >= 0.0)
        self.assert_(TTL <= 0.5)

        # sleep
        sleep(1)

        infos = locker.getItemInfo('URI')

        # should be gone
        self.assert_(locker.getItemInfo('URI') is None)

        locker.addItem(item)
        # manual remove
        locker.removeItem('URI')
        # should be gone
        self.assert_(locker.getItemInfo('URI') is None)



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WikiLockingTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
