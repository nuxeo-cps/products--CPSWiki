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

import unittest

from Products.CPSUtil.tests.web_conformance import assertValidCss
from Products.CPSDefault.tests.CPSTestCase import CPSTestCase
from layer import CPSWikiLayer

class WebConformanceTests(CPSTestCase):

    layer = CPSWikiLayer

    def test_css(self):
        portal = self.portal
        ALL_CSS = ['wiki.css']
        for css_name in ALL_CSS:
            css_body = getattr(portal, css_name)(portal)
            assertValidCss(css_body, css_name)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WebConformanceTests),
        ))
