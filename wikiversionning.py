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
from difflib import ndiff, restore, Differ

LINE_FEED = '\r\n'
LINE_FEED_U = u'\r\n'

class VersionContent:
    """ deals with incremental diffs
    """
    _max_size = 30
    _primary = None
    _versions = []

    def __init__(self, primary, tags={}):
        self._primary = (self._stringToList(primary), tags)
        self._versions = []

    #
    # read - write APIS
    #
    def _setContent(self, index, content):
        """ write content, useful to be overriden """
        if index == 0:
            self._primary = content
        else:
            self._versions[index-1] = content

    def _getContent(self, index):
        """ write content, useful to be overriden """
        if index == 0:
            return self._primary
        else:
            return self._versions[index-1]

    def _delContent(self, index):
        """ write content, useful to be overriden """
        if index > 0:
            del self._versions[index-1]

    def _getHistorySize(self):
        """ write content, useful to be overriden """
        return len(self._versions)

    def _addContent(self, content, tags={}):
        """ write content, useful to be overriden """
        self._versions.append((content, tags))

    #
    # base
    #
    def _stringToList(self, string):
        """ outsourced to deal unicode if needed """
        return  string.split(LINE_FEED)

    def _listToString(self, list_):
        """ outsourced to deal unicode if needed """
        return LINE_FEED.join(list_)

    def appendVersion(self, content, tags={}):
        """ adding a new version """
        content = self._stringToList(content)

        while self._getHistorySize() >= self._max_size:
            firstdiff = self.getVersion(1)
            self._primary = firstdiff
            self._delContent(1)

        last_version = self.getLastVersion()
        last = last_version[0]
        last = self._stringToList(last)

        delta = list(ndiff(last, content))
        self._addContent(delta, tags)

    def restoreVersion(self, index):
        version, tags = self.getVersion(index)

        # drop index -> end
        while self._getHistorySize() != index + 1:
            self._delContent(self._getHistorySize())

    def getLastVersion(self):
        """ getting last version """
        i = self._getHistorySize()
        version = self._getContent(i)
        content = version[0]
        tags = version[1]

        if i == 0:
            return (self._listToString(content), tags)
        current = restore(content, 2)
        return (self._listToString(current), tags)

    def getVersion(self, index):
        """ restoring a version """
        version = self._getContent(index)
        content = version[0]
        tags = version[1]
        if index == 0:
            return (self._listToString(content), tags)
        current = restore(content, 2)
        return (self._listToString(current), tags)

    def getVersionCount(self):
        return self._getHistorySize() + 1

    def getDiffs(self, index_a, index_b, separator=''):
        """ retrieves a diff between two version """
        version_count = self.getVersionCount()
        if index_a >= version_count or index_b >= version_count:
            return None

        version_a, tags = self.getVersion(index_a)
        version_b, tags = self.getVersion(index_b)

        # Make sure texts end with a newline, or the formatting will be off:
        if not version_a[-1] == '\n':
            version_a += '\n'
        if not version_b[-1] == '\n':
            version_b += '\n'
        
        dif = Differ()
        result = list(dif.compare(version_a.splitlines(1),
                                  version_b.splitlines(1)))
        result = separator.join(result)
        # The python difflib inserts lines that highlight what changed when 
        # things inside a line changed. So far so good, but it starts these
        # lines with a '?', which to most normal people means that there is
        # something questionable going on. Hence, we switch that out for
        # a '>' character instead, which does not carry any such connotations.
        return result.replace('\n?', '\n>')
