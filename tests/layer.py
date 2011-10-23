# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# (C) Copyright 2011 CPS-CMS Community <http://cps-cms.org/>
# Authors:
# M.-A. Darche <madarche@nuxeo.com>
# Georges Racinet <gracinet@cps-cms.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from Testing import ZopeTestCase
from Products.CPSDefault.tests.CPSTestCase import ExtensionProfileLayerClass

ZopeTestCase.installProduct('CPSWiki')

class CPSWikiLayerClass(ExtensionProfileLayerClass):
    extension_ids = ('CPSWiki:default',)

CPSWikiLayer = CPSWikiLayerClass(__name__, 'CPSWikiLayer')
