# (C) Copyright 2010 AFUL <http://aful.org>
# Author:
# M.-A. Darche
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

import logging
import re

import transaction
from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.text import upgrade_string_unicode
from Products.CPSCore.ProxyBase import walk_cps_folders

from wikipage import ZODBVersionContent

def upgrade_unicode(portal):
    """Upgrades all CPSWiki instances to unicode.
    """
    logger = logging.getLogger('Products.CPSWiki.upgrade.upgrade_unicode')

    wiki_counters = dict(done=0, total=0)
    wiki_page_counters = dict(done=0, total=0)
    for folder in walk_cps_folders(portal):
        upgrade_unicode_in(folder, wiki_counters=wiki_counters,
                           wiki_page_counters=wiki_page_counters)

    logger.warn("Finished unicode upgrade of the %d/%d wikis and %d/%d wiki_pages.",
                wiki_counters['done'], wiki_counters['total'],
                wiki_page_counters['done'], wiki_page_counters['total'])

    if not wiki_counters['done']:
        return

    logger.info("Rebuilding Tree Caches for wiki titles")
    trees = portal.portal_trees.objectValues('CPS Tree Cache')
    for tree in trees:
        logger.info("Rebuilding %s", tree)
        tree.rebuild()
        transaction.commit()
    logger.warn("Finished rebuilding the Tree Caches for wiki titles")

def upgrade_unicode_in(folder, wiki_counters, wiki_page_counters):
    for wiki in folder.objectValues(['Wiki']):
        wiki_counters['total'] += 1
        upgrade_wiki_unicode(wiki, wiki_page_counters)
        wiki_counters['done'] += 1
        if wiki_counters['done'] % 100 == 0:
            logger.info("Upgraded %d wikis over %d currently known",
                        wiki_counters['done'], wiki_counters['total'])
            transaction.commit()

def upgrade_wiki_unicode(wiki, wiki_page_counters):
    logger = logging.getLogger('Products.CPSWiki.upgrade.upgrade_wiki_unicode')
    logger.info("Upgrading wiki at %s", wiki.absolute_url_path())
    wiki.title = upgrade_string_unicode(wiki.title)
    logger.debug("Upgrading title %r DONE", wiki.title)

    for wiki_page in wiki.objectValues(['Wiki Page']):
        wiki_page_counters['total'] += 1
        upgrade_wiki_page_unicode(wiki_page)
        wiki_page_counters['done'] += 1
        if wiki_page_counters['done'] % 100 == 0:
            logger.info("Upgraded %d wiki_pages over %d currently known",
                        wiki_page_counters['done'], wiki_page_counters['total'])
            transaction.commit()

    return True

def upgrade_wiki_page_unicode(wiki_page):
    logger = logging.getLogger('Products.CPSWiki.upgrade.upgrade_wiki_page_unicode')
    logger.debug("Upgrading versions for wiki_page at %s ...",
                wiki_page.absolute_url_path())
    if not isinstance(wiki_page.source, ZODBVersionContent):
        logger.warn("Upgrade not done. "
                    "Upgrade is only supported for wiki_page "
                    "with ZODBVersionContent backend.")
        return

    wiki_page.clearCache()
    wiki_page.title = upgrade_string_unicode(wiki_page.title)

    plist_count = len(wiki_page.source.plist)
    for i in range(plist_count):
        logger.debug("Upgrading version %s", i)
        if i == 0:
            # The initial version is always an empty string and not an array.
            # We don't need to touch it.
            continue
        else:
            # content is an array
            content = wiki_page.source._getContent(i)
            lines = content[0]
            tags = content[1]
            converted_lines = []
            for line in lines:
                #logger.debug("line: %s", line)
                converted_line = upgrade_string_unicode(line)
                #logger.debug("converted_line: %s", converted_line)
                converted_lines.append(converted_line)
            wiki_page.source._setContent(i, converted_lines, tags)
        logger.debug("Upgrading version %s DONE", i)

    logger.debug("Upgrading versions DONE")
    return True

