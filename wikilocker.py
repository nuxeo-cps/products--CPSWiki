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

""" When someone is editing a page, we need to prevent
    other users to edit it simultaenously.

    wikilocker provides a multi-read single-write synchronizer
    mechanisme with a timeout.

    It has to be thread-safe for multiple access

    it keeps a list of locked uri given a id
    the id is unique by client

    scenarii :
        o A edits the page, B can read it but can't edit it
        o A edits the page, a timeout occurs. B edits the page and post it
          A then post the page. A has to resolve the conflict.

"""
import time
import thread
from UserDict import UserDict

import Interface

class ILockableItem(Interface.Base):
    """ ILockableItem is the interface used by locker list
        to lock an object, it has to be adapted to this interface
    """
    def getURI():
        """ return a unique id

        Often based on the url
        """

    def getLockInfo():
        """ provide info on lock

        When an item is locked, this gives info
        about the lock. For example, the user IP
        or mac address.
        """

    def getLockDuration():
        """ tells how long the lock lasts in seconds """

class LockerList(UserDict):

    def __init__(self, initlist=None):
        UserDict.__init__(self, initlist)

    def _verifyItem(self, item):
        """ check if item is ok to work with """
        if not ILockableItem.isImplementedBy(item):
            raise Exception('this item does not provide ILockableItem')


    def _calculateTTL(self, expires):
        """ calculates a ttl given an expire """
        now = time.time()
        return expires - now

    def getItemInfo(self, uri):
        """ find an item """
        if self.has_key(uri):
            item = self[uri]
            TTL = self._calculateTTL(item[0])
            if TTL <= 0:
                del self[uri]        # cleans expired items
                return None
            else:
                return item
        else:
            return None

    def addItem(self, item, locker=thread.allocate_lock()):
        """ add an item,or refresh it """
        self._verifyItem(item)
        uri = item.getURI()
        lock_info = self.getItemInfo(uri)

        if lock_info is None:
            locker.acquire()
            try:
                birth = time.time()
                expires = birth + item.getLockDuration()
                infos = item.getLockInfo()
                self[uri] = (expires, infos, self._calculateTTL(expires))
            finally:
                locker.release()

    def removeItem(self, uri):
        """ manually remove an item """
        if self.has_key(uri):
            del self[uri]
