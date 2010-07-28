# Copyright 2010 AFUL <http://aful.org>
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

from wikipage import ZODBVersionContent

def upgrade_unicode(portal):
    """Upgrades all CPSWiki instances to unicode.
    """
    logger = logging.getLogger('Products.CPSWiki.upgrade.upgrade_unicode')

    ctool = getToolByName(portal, 'portal_catalog')
    brains = ctool.searchResults(portal_type='Wiki')
    total = len(brains)
    done = 0
    for brain in brains:
        wiki = brain.getObject()
        if wiki is None:
            continue
        if not upgrade_wiki_unicode(wiki):
            logger.error("Could not upgrade wiki at %s", brain.getPath())
            continue
        done += 1
        if done % 100 == 0:
            logger.info("Upgraded %d/%d wikis", done, total)
            transaction.commit()

    logger.warn("Finished unicode upgrade of the %d/%d wikis.", done, total)
    transaction.commit()

    if not done:
        return
    logger.info("Rebuilding Tree Caches for wiki titles")
    trees = portal.portal_trees.objectValues('CPS Tree Cache')
    for tree in trees:
        logger.info("Rebuilding %s", tree)
        tree.rebuild()
        transaction.commit()
    logger.warn("Finished rebuilding the Tree Caches for wiki titles")


    brains = ctool.searchResults(portal_type='Wiki Page')
    total = len(brains)
    done = 0
    for brain in brains:
        wiki_page = brain.getObject()
        if wiki_page is None:
            continue
        if not upgrade_wiki_page_unicode(wiki_page):
            logger.error("Could not upgrade wiki_page at %s", brain.getPath())
            continue
        done += 1
        if done % 100 == 0:
            logger.info("Upgraded %d/%d wiki_pages", done, total)
            transaction.commit()

    logger.warn("Finished unicode upgrade of the %d/%d wiki_pages.", done, total)
    transaction.commit()

def upgrade_wiki_unicode(wiki):
    logger = logging.getLogger('Products.CPSWiki.upgrade.upgrade_wiki_unicode')
    logger.info("Upgrading title for wiki at %s ...", wiki.getPhysicalPath())
    wiki.title = upgrade_string_unicode(wiki.title)
    logger.info("Upgrading title %s DONE", wiki.title)
    return True

def upgrade_wiki_page_unicode(wiki_page):
    logger = logging.getLogger('Products.CPSWiki.upgrade.upgrade_wiki_page_unicode')
    logger.info("Upgrading versions for wiki_page at %s ...",
                wiki_page.getPhysicalPath())
    if not isinstance(wiki_page.source, ZODBVersionContent):
        logger.warn("Upgrade not done. "
                    "Upgrade is only supported for wiki_page "
                    "with ZODBVersionContent backend.")
        return

#     if wiki_page.title == 'ConfTelephoneAudio':
#         import pdb;pdb.set_trace()
    version_count = wiki_page.source._getHistorySize()
    version_numbers = range(version_count)
    for i in version_numbers:
        logger.info("Upgrading version %s", i)
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
                converted_lines.append(upgrade_string_unicode(line))
            wiki_page.source._setContent(i, converted_lines, tags)
        logger.info("Upgrading version %s DONE", i)
    logger.info("Upgrading versions DONE")
    return True

