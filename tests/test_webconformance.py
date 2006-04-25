# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Authors:
# M.-A. Darche <madarche@nuxeo.com>
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

import os
import unittest

from Testing import ZopeTestCase
from Testing.ZopeTestCase import PortalTestCase

import Products
from Products.PythonScripts.PythonScript import PythonScript

#from Products.CMFDefault.factory import addConfiguredSite
from Products.CMFDefault.Portal import manage_addCMFSite

from Products.CPSUtil.tests.web_conformance import assertValidCss

ZopeTestCase.installProduct('PythonScripts', quiet=True)

ZopeTestCase.installProduct('CMFCore', quiet=True)
ZopeTestCase.installProduct('CMFDefault', quiet=True)
ZopeTestCase.installProduct('ZCTextIndex', quiet=True)
ZopeTestCase.installProduct('MailHost', quiet=True)

ZopeTestCase.installProduct('CPSUtil', quiet=True)
ZopeTestCase.installProduct('CPSDefault', quiet=True)
ZopeTestCase.installProduct('CPSWiki', quiet=True)

portal_name = 'portal'

product_name = [c for c in __name__.split('.') if c != 'Products'][0]

class WebConformanceTests(PortalTestCase):

    def afterSetUp(self):
        # Setting up the CMF portal
        portal = self.getPortal()

        # Setting up the python script isUserAgentGecko used in the
        # wiki.css.dtml file.
        script_id = 'isUserAgentGecko'
        portal._setObject(script_id, PythonScript(script_id))

        product_file = getattr(Products, 'CPSDefault').__file__
        product_path = os.path.dirname(product_file)
        script_file_path = os.path.join(product_path, 'skins', 'cps_default',
                                        script_id + '.py')
        script_file = open(script_file_path)
        portal[script_id].ZPythonScript_edit(params='', body=script_file)


    def getPortal(self):
        if not hasattr(self.app, portal_name):
            manage_addCMFSite(self.app,
                              portal_name)
#            addConfiguredSite(self.app,
#                              portal_name, 'default')
        return self.app[portal_name]

    def test_css(self):
        portal = self.getPortal()
        product_file = getattr(Products, product_name).__file__
        product_path = os.path.dirname(product_file)
        ALL_CSS = ['wiki.css']
        for css_name in ALL_CSS:
            css_path = os.path.join(product_path, 'skins', 'cps_wiki', css_name + '.dtml')
            css_file = open(css_path)
            portal.addDTMLMethod(css_name, title=css_name, file=css_file)
            css_body = portal[css_name](self.portal)
            assertValidCss(css_body, css_name)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WebConformanceTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

