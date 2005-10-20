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
# $Id:$

from wikiparserinterface import IWikiTag

# no lock used here because the registration process is done
# at startup
__registered_tags = {}

def getRegisteredTags():
    return __registered_tags.items()

def registerTag(tag):
    global __registered_tags
    if tag.getTagId() not in __registered_tags:
        __registered_tags[tag.getTagId()] = tag
    else:
        raise KeyError('%s already registered' % tag.getTagId())

def unRegisterTag(tag):
    global __registered_tags
    if tag.getTagId() in __registered_tags:
        del __registered_tags[tag.getTagId()]
    else:
        raise KeyError('%s not registered' % tag.getTagId())

def renderBrackets(bracket, parser, context=None):
    """ renders the bracket if an appropriate tag is found """
    splited_content = bracket.split(':')
    tag_id = splited_content[0].strip()
    if len(splited_content) > 1:
        parameters = splited_content[1].strip()

    if tag_id in __registered_tags:
        tagger = __registered_tags[tag_id]
        if tagger.canHandle(parser):
            return True, tagger.render(context, parameters)
    return False, bracket
