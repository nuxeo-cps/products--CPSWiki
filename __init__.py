# (C) Copyright 2005-2008 Nuxeo SAS <http://nuxeo.com>
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

from Products.CMFCore.utils import ContentInit
from Products.CMFCore.DirectoryView import registerDirectory
try:
    from Products.CMFCore.permissions import AddPortalContent
except ImportError: # CPS 3.2
    from Products.CMFCore.CMFCorePermissions import AddPortalContent
from Products.GenericSetup import profile_registry
from Products.GenericSetup import EXTENSION

from Products.CPSCore.interfaces import ICPSSite

import wiki, wikipage

# add register tag modules here
import wikicpstags
import wikicommontags

registerDirectory('skins', globals())

contentClasses = (wiki.Wiki,
                  wikipage.WikiPage,
                  )

contentConstructors = (wiki.manage_addWiki,
                       wikipage.manage_addWikiPage,
                       )

fti = ()


def initialize(context):
    ContentInit('Wiki Content',
                content_types=contentClasses,
                permission=AddPortalContent,
                extra_constructors=contentConstructors,
                fti=fti
                ).initialize(context)
    profile_registry.registerProfile(
        'default',
        'CPS Wiki',
        "Wiki product for CPS.",
        'profiles/default',
        'CPSWiki',
        EXTENSION,
        for_=ICPSSite)
