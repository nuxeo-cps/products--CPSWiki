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

""" page versionning base on incremental diff
    (not using CMF ones on purpose)
"""
from difflib import ndiff, restore

LINE_FEED = '\r\n'
LINE_FEED_U = u'\r\n'

class VersionContent:
    """ deals with incremental diffs
    """
    _max_size = 30
    _primary = None
    _versions = []

    def __init__(self, primary):
        self._primary = self._stringToList(primary)

    def _stringToList(self, string):
        """ outsourced to deal unicode if needed """
        return  string.split(LINE_FEED)

    def _listToString(self, list_):
        """ outsourced to deal unicode if needed """
        return ''.join(list_)

    def appendVersion(self, content):
        """ adding a new version """
        content = self._stringToList(content)

        while len(self._versions) >= self._max_size:
            firstdiff = self.getVersion(1)
            self._primary = firstdiff
            del self._versions[0]

        last = self._stringToList(self.getLastVersion())
        delta = list(ndiff(last, content))
        self._versions.append(delta)

    def restoreVersion(self, index):
        version = self.getVersion(index)

        # drop index -> end
        while len(self._versions) != index + 1:
            del self._versions[len(self._versions)-1]

    def getLastVersion(self):
        """ getting last version """
        i = len(self._versions)
        if i == 0:
            return self._listToString(self._primary)
        current = restore(self._versions[i-1], 2)
        return self._listToString(current)


    def getVersion(self, index):
        """ restoring a version """
        if index == 0:
            return self._listToString(self._primary)

        current = restore(self._versions[index-1], 2)
        return self._listToString(current)

