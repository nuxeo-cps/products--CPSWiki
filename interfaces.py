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

import Interface

class IWikiParser(Interface.Base):
    """Define an interface for all wiki parser.
    """

    def parseContent(content, wiki):
        """Return the render of the provided content along with references on
        the linked pages and potentially linked pages.
        """

    def getId():
        """Return a parser unique ID.
        """

class IWikiTag(Interface.Base):
    """ let the user extends the tags parsed
    by providing bracketed content

    for example [id:*anything*] will be sent to
    the right wikitag with the *anything* value
    """

    def getTagId():
        """ returns the id of the tage """

    def render(context, parameters):
        """ gets what's inside the brackets and return
        what has to be displayed, given a context
        """

    def canHandle(parser):
        """ returns true if it's compatible with the given parser """

    def getHelp():
        """ returns translatable text, that can be used to display
        syntax help"""

class IWikiRelation(Interface.Base):
    """ relation: subjet, object, predicate
    IWikiRelation methods are object
    the result the predicate

    for example (more to come in the adapter implementation):

        'page 1 is linked to page 2'
        'page 1 is about theaters'
        'page 1 is about snow'
        'page 1 relates to page 2 about snow'

    WikiRelation(page1).isLinkedTo() == ('page 2',)
    WikiRelation(page1).isBackLinkedTo() == ()
    WikiRelation(page1).isAbout() == ('theaters', 'snow')
    WikiRelation(page1).relatesTo('snow') == ('page2')

    """
    def clearAll():
        """ remove all relations """

    def isLinkedTo():
        """ returns all the pages ids that
        are linked to (childs) the page in a tuple
        """

    def addLinksTo(ids):
        """ add a link to given ids
        """

    def removeLinksTo(ids):
        """ remove link to given ids
        """

    def isBackLinkedTo():
        """ returns all the pages ids that
        are backlinked to (parents) the page
        """

    def addBackLinksTo(ids):
        """ add a backlink to given ids
        """

    def removeBackLinksTo(ids):
        """ remove  backlink to given ids
        """

    def isAbout(topic):
        """ returns all topics
        """

    def addTopics(topics):
        """ add a topic
        """

    def removeTopics(topics):
        """ remove a topic
        """

class IWikiTopic(Interface.Base):

    def talksAbout(topic):
        """ returns all pages related to the given topic
        """

class IWikiRelationGraph(Interface.Base):

    def clearAll():
        """ remove all relations """

    def getRelationsFor(subject, object):
        """ retrieves predicates """

    def addRelationsFor(subject, object, predicate):
        """ add predicate """

    def deleteRelationFor(subject, object, predicate):
        """ delete predicate """
