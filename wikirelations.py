# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziade <tz@nuxeo.com>
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

from ZODB.PersistentMapping import PersistentMapping
from interfaces import IWikiRelation, IWikiRelationGraph

class MemoryBackend:

    __implements__ = (IWikiRelationGraph,)

    def __init__(self):
        self._triplets = {}

    def clearAll(self):
        self._triplets = {}

    def getRelationsFor(self, subject, object):
        key = '%s:%s' %  (subject, object)
        if key in self._triplets.keys():
            return self._triplets[key]
        else:
            return []

    def addRelationFor(self, subject, object, predicate):
        key = '%s:%s' %  (subject, object)
        if key in self._triplets.keys():
            if predicate not in self._triplets[key]:
                self._triplets[key].append(predicate)
        else:
            self._triplets[key] = [predicate]

    def deleteRelationFor(self, subject, object, predicate):
        count = 0
        key = '%s:%s' %  (subject, object)
        if key in self._triplets.keys():
            if predicate in self._triplets[key]:
                self._triplets[key].remove(predicate)
                count += 1
        return count

class ZODBBackend(MemoryBackend):
    def __init__(self):
        self._triplets = PersistentMapping()

    def clearAll(self):
        self._triplets = PersistentMapping()

class WikiRelation:
    """ adapter that let a wiki page index
    its relations
    """
    __implements__ = (IWikiRelation,)

    def __init__(self, wikipage, backend=MemoryBackend()):
        self._backend = backend
        self._wikipage = wikipage
        self._isLinkedTo = '<is_linked_to>'
        self._isLinkableTo = '<is_linkable_to>'
        self._isBackLinkedTo = '<is_blinked_to>'
        self._isAbout = '<is_about_to>'

    def clearAll(self):
        self._backend.clearAll()

    def isLinkedTo(self):
        return self._backend.getRelationsFor(self._wikipage.id,
                                             self._isLinkedTo)

    def addLinksTo(self, ids):
        for id in ids:
            self._backend.addRelationFor(self._wikipage.id, self._isLinkedTo,
                                         id)

    def removeLinksTo(self, ids):
        count = 0
        for id in ids:
            count += self._backend.deleteRelationFor(self._wikipage.id,
                                                     self._isLinkedTo,
                                                     id)
        return count

    def isLinkableTo(self):
        return self._backend.getRelationsFor(self._wikipage.id,
                                             self._isLinkableTo)

    def addLinkablesTo(self, ids):
        for id in ids:
            self._backend.addRelationFor(self._wikipage.id, self._isLinkableTo,
                                         id)

    def removeLinkablesTo(self, ids):
        count = 0
        for id in ids:
            count += self._backend.deleteRelationFor(self._wikipage.id,
                                                     self._isLinkableTo,
                                                     id)
        return count

    def isBackLinkedTo(self):
        return self._backend.getRelationsFor(self._wikipage.id,
                                             self._isBackLinkedTo)

    def addBackLinksTo(self, ids):
        for id in ids:
            self._backend.addRelationFor(self._wikipage.id,
                                         self._isBackLinkedTo,
                                         id)

    def removeBackLinksTo(self, ids):
        count = 0
        for id in ids:
            count += self._backend.deleteRelationFor(self._wikipage.id,
                                                     self._isBackLinkedTo,
                                                     id)
        return count

    def isAbout(self):
        return self._backend.getRelationsFor(self._wikipage.id,
                                             self._isAbout)

    def addTopics(self, topics):
        for topic in topics:
            self._backend.addRelationFor(self._wikipage.id,
                                         self._isAbout,
                                         topic)

    def removeTopics(self, topics):
        count = 0
        for topic in topics:
            count += self._backend.deleteRelationFor(self._wikipage.id,
                                                     self._isAbout,
                                                     topic)
        return count
