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
from Products.CMFCore.permissions import setDefaultRoles

from Products.CPSInstaller.CPSInstaller import CPSInstaller
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CPSWiki.wikipermissions import addWikiPage, deleteWikiPage,\
    editWikiPage, viewWikiPage

from Products.CPSWorkflow.transitions import \
     TRANSITION_INITIAL_PUBLISHING, TRANSITION_INITIAL_CREATE, \
     TRANSITION_ALLOWSUB_CREATE, TRANSITION_ALLOWSUB_PUBLISHING, \
     TRANSITION_BEHAVIOR_PUBLISHING, TRANSITION_BEHAVIOR_FREEZE, \
     TRANSITION_BEHAVIOR_DELETE, TRANSITION_BEHAVIOR_MERGE, \
     TRANSITION_ALLOWSUB_CHECKOUT, TRANSITION_INITIAL_CHECKOUT, \
     TRANSITION_BEHAVIOR_CHECKOUT, TRANSITION_ALLOW_CHECKIN, \
     TRANSITION_BEHAVIOR_CHECKIN, TRANSITION_ALLOWSUB_DELETE, \
     TRANSITION_ALLOWSUB_MOVE, TRANSITION_ALLOWSUB_COPY
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION, \
     TRIGGER_AUTOMATIC

WebDavLockItem = 'WebDAV Lock items'
WebDavUnlockItem = 'WebDAV Unlock items'
SECTIONS_ID = 'sections'
WORKSPACES_ID = 'workspaces'

SKINS = {'cps_wiki': 'Products/CPSWiki/www'}

class CPSWikiInstaller(CPSInstaller):
    """CPSWiki Installer
    """
    product_name = "CPSWiki"

    def install(self):
        """Main func
        """
        self.log("CPSWiki Install / Update ........ [ S T A R T ]")
        self.verifySkins(SKINS)
        self.resetSkinCache()
        self.verifyPortalTypes()
        self.updatePortalTree()
        self.setupWorkflows()
        self.installNewPermissions()
        self.setupTranslations()
        self.finalize()
        self.reindexCatalog()
        self.log("CPSWiki Install / Update .........[ S T O P ]  ")

    def verifyPortalTypes(self):
        """Verify portal types
        """
        #wiki_type = self.portal.getCPSWikiType()
        #self.verifyFlexibleTypes(wiki_type)

        self.allowContentTypes('CPS Wiki', ('Workspace', 'Section'))

        ptypes = {
            'CPS Wiki' : {'allowed_content_types': ('CPS Wiki Page',),
                      'typeinfo_name': 'CPSWiki: CPS Wiki',
                      'add_meta_type': 'Factory-based Type Information',
                      },
            'CPS Wiki Page' : {'allowed_content_types': (),
                          'typeinfo_name': 'CPSWiki: CPS Wiki Page',
                          'add_meta_type': 'Factory-based Type Information',
                           },
            }
        self.verifyContentTypes(ptypes, destructive=1)

        self.allowContentTypes('CPS Wiki Page', 'CPS Wiki')

    def setupWorkflows(self):
        """ sets up workfows for wiki
        """
        # workflow for forums
        # in workspaces
        wfdef = {'wfid': 'workspace_wiki_wf',
                'permissions': (View, ModifyPortalContent,
                                WebDavLockItem, WebDavUnlockItem,)
                }

        wfstates = {
            'work': {
                'title': 'Work',
                'transitions':('create_content', 'cut_copy_paste'),
                'permissions': {View: ('Manager', 'WorkspaceManager',
                                    'WorkspaceMember', 'WorkspaceReader',
                                    )},
                },
            }

        wftransitions = {
            'cut_copy_paste': {
                'title': 'Cut/Copy/Paste',
                'new_state_id': '',
                'transition_behavior': (TRANSITION_ALLOWSUB_DELETE,
                                        TRANSITION_ALLOWSUB_MOVE,
                                        TRANSITION_ALLOWSUB_COPY),
                'clone_allowed_transitions': None,
                'trigger_type': TRIGGER_USER_ACTION,
                'actbox_name': '',
                'actbox_category': '',
                'actbox_url': '',
                'props': {'guard_permissions':'',
                        'guard_roles':'Manager; WorkspaceManager; '
                                        'WorkspaceMember',
                        'guard_expr':''},
            },
            'create': {
                'title': 'Initial creation',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_INITIAL_CREATE,),
                'clone_allowed_transitions': None,
                'actbox_category': 'workflow',
                'props': {'guard_permissions':'',
                        'guard_roles':'Manager; WorkspaceManager; '
                                        'WorkspaceMember',
                        'guard_expr':''},
            },
            'create_content': {
                'title': 'Create content',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_ALLOWSUB_CREATE,
                                        TRANSITION_ALLOWSUB_CHECKOUT),
                'clone_allowed_transitions': None,
                'trigger_type': TRIGGER_USER_ACTION,
                'actbox_name': '',
                'props': {'guard_permissions':'',
                        'guard_roles':'',
                        'guard_expr':''},
            },
        }
        self.verifyWorkflow(wfdef, wfstates, wftransitions, {}, {})

        # in sections
        wfdef = {'wfid': 'section_wiki_wf',
                'permissions': (View, ModifyPortalContent)}

        wfstates = {
            'work': {
                'title': 'Work',
                'transitions': ('create_content', 'cut_copy_paste'),
                'permissions': {View: ('Manager', 'SectionManager',
                                    'SectionReviewer', 'SectionReader'),
                                ModifyPortalContent: ('Manager', 'Owner',
                                                    'WorkspaceManager',
                                                    'WorkspaceMember',
                                                    'SectionManager',
                                                    'SectionReviewer')},
            },
        }

        wftransitions = {
            'cut_copy_paste': {
                'title': 'Cut/Copy/Paste',
                'new_state_id': '',
                'transition_behavior': (TRANSITION_ALLOWSUB_DELETE,
                                        TRANSITION_ALLOWSUB_MOVE,
                                        TRANSITION_ALLOWSUB_COPY),
                'clone_allowed_transitions': None,
                'trigger_type': TRIGGER_USER_ACTION,
                'actbox_name': '',
                'actbox_category': '',
                'actbox_url': '',
                'props': {'guard_permissions': '',
                        'guard_roles': 'Manager; SectionManager; '
                                        'SectionReviewer; SectionReader',
                        'guard_expr': ''},
            },
            'create': {
                'title': 'Initial creation',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_INITIAL_CREATE,),
                'clone_allowed_transitions': None,
                'actbox_category': 'workflow',
                'props': {'guard_permissions': '',
                        'guard_roles': 'Manager; SectionManager;',
                        'guard_expr': ''},
            },
            'create_content': {
                'title': 'Create content',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_ALLOWSUB_CREATE,
                                        TRANSITION_ALLOWSUB_PUBLISHING),
                'clone_allowed_transitions': None,
                'trigger_type': TRIGGER_USER_ACTION,
                'props': {'guard_permissions': 'Forum Post',
                        'guard_roles': '',
                        'guard_expr': ''},
            },
        }
        self.verifyWorkflow(wfdef, wfstates, wftransitions, {}, {})

        ws_chains = { 'CPS Wiki': 'workspace_wiki_wf'}
        se_chains = { 'CPS Wiki': 'section_wiki_wf'}

        ws = self.portal['workspaces']
        self.verifyLocalWorkflowChains(ws, ws_chains)

        se = self.portal['sections']
        self.verifyLocalWorkflowChains(se, se_chains)


    def updatePortalTree(self):
        """ register folderish document types in portal_tree
        """
        self.log("Registering CPS Wiki n portal_tree")

        portal_trees = self.portal.portal_trees

        types = list(portal_trees.workspaces.type_names)
        if 'CPS Wiki' not in types:
            types = types + ['CPS Wiki']
            portal_trees.workspaces.manage_changeProperties(type_names=types)
            portal_trees.workspaces.manage_rebuild()

        types = list(portal_trees.sections.type_names)
        if 'CPS Wiki' not in types:
            types = types + ['CPS Wiki']
            portal_trees.sections.manage_changeProperties(type_names=types)
            portal_trees.sections.manage_rebuild()

    def installNewPermissions(self):
        """Installs new permissions
        """

        setDefaultRoles(addWikiPage, ('Manager', 'Owner'))
        setDefaultRoles(editWikiPage, ('Manager', 'Owner'))
        setDefaultRoles(deleteWikiPage, ('Manager', 'Owner'))
        setDefaultRoles(viewWikiPage, ('Manager', 'Owner'))

        # Workspace
        wiki_ws_perms = {
            addWikiPage : ['Manager',
                           'WorkspaceManager',
                           'WorkspaceMember'],

            viewWikiPage : ['Manager',
                           'WorkspaceManager',
                           'WorkspaceMember'
                           'WorkspaceReader'],
            editWikiPage : ['Manager',
                           'WorkspaceManager',
                           'WorkspaceMember'],
            deleteWikiPage : ['Manager',
                              'WorkspaceManager']
            }

        for perm, roles in wiki_ws_perms.items():
            self.portal[WORKSPACES_ID].manage_permission(perm, roles, 0)

        # Section
        wiki_sc_perms = {
            addWikiPage : ['Manager',
                           'SectionManager',
                           'vMember'],

            viewWikiPage : ['Manager',
                           'SectionManager',
                           'SectionMember'
                           'SectionReader'],
            editWikiPage : ['Manager',
                            'SectionManager',
                            'SectionMember'],
            deleteWikiPage : ['Manager',
                              'SectionManager']
            }

        for perm, roles in wiki_sc_perms.items():
            self.portal[SECTIONS_ID].manage_permission(perm, roles, 0)

def install(self):
    installer = CPSWikiInstaller(self)
    installer.install()
    return installer.logResult()
