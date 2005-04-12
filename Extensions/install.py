# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziadé <tz@nuxeo.com>
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
from Products.CMFCore.permissions import setDefaultRoles

from Products.CPSInstaller.CPSInstaller import CPSInstaller
from Products.CMFCore.permissions import \
     View, ModifyPortalContent, AddPortalContent, DeleteObjects

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

        self.allowContentTypes('Wiki', ('Workspace', 'Section'))
        ptypes = {
            'Wiki' : {'allowed_content_types': ('Wiki Page',),
                      'typeinfo_name': 'CPSWiki: Wiki',
                      'add_meta_type': 'Factory-based Type Information',
                      },
            'Wiki Page' : {'allowed_content_types': (),
                           'typeinfo_name': 'CPSWiki: Wiki Page',
                           'add_meta_type': 'Factory-based Type Information',
                           },
            }
        self.verifyContentTypes(ptypes, destructive=1)
        self.allowContentTypes('Wiki Page', 'Wiki')


    def setupWorkflows(self):
        """ sets up workfows for wiki
        """
        # Workflow definition in workspaces
        wfdef = {'wfid': 'workspace_wiki_wf',
                'permissions': (View, ModifyPortalContent, AddPortalContent),
                }

        wfstates = {
            'work': {
                'title': 'Work',
                'transitions':('create_content', 'cut_copy_paste'),
                'permissions': {View: ('Manager', 'WorkspaceManager',
                                       'WorkspaceMember', 'WorkspaceReader',
                                       'Contributor', 'Reader',
                                       ),
                                ModifyPortalContent: ('Manager', 'Owner',
                                                      'WorkspaceManager',
                                                      'WorkspaceMember',
                                                      'Contributor',
                                                      ),
                                AddPortalContent: ('Manager', 'Owner',
                                                   'WorkspaceManager',
                                                   'WorkspaceMember',
                                                   'Contributor',
                                                   ),
                                },
                }
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
                          'WorkspaceMember; Contributor',
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
                          'guard_roles':'Manager; WorkspaceManager; '
                          'WorkspaceMember; Contributor',
                          'guard_expr':''},
            },
        }
        self.verifyWorkflow(wfdef, wfstates, wftransitions, {}, {})

        # Workflow definition in sections
        wfdef = {'wfid': 'section_wiki_wf',
                 'permissions': (View, ModifyPortalContent, AddPortalContent),
                 }

        wfstates = {
            'work': {
                'title': 'Work',
                'transitions': ('create_content', 'cut_copy_paste'),
                'permissions': {View: ('Manager', 'SectionManager',
                                       'SectionReviewer', 'SectionReader',
                                       'Contributor', 'Reader',
                                       ),
                                ModifyPortalContent: ('Manager', 'Owner',
                                                      'SectionManager',
                                                      'Contributor',
                                                      ),
                                AddPortalContent: ('Manager', 'Owner',
                                                   'SectionManager',
                                                   'Contributor',
                                                   ),
                                },
                }
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
                          'guard_roles': 'Manager; SectionManager; Contributor',
                          'guard_expr': ''},
            },
            'create': {
                'title': 'Initial creation',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_INITIAL_CREATE,),
                'clone_allowed_transitions': None,
                'actbox_category': 'workflow',
                'props': {'guard_permissions': '',
                          'guard_roles': 'Manager; SectionManager; Contributor',
                          'guard_expr': ''},
            },
            'create_content': {
                'title': 'Create content',
                'new_state_id': 'work',
                'transition_behavior': (TRANSITION_ALLOWSUB_CREATE,
                                        TRANSITION_ALLOWSUB_PUBLISHING),
                'clone_allowed_transitions': None,
                'trigger_type': TRIGGER_USER_ACTION,
                'props': {'guard_permissions': '',
                          'guard_roles': 'Manager; SectionManager; Contributor',
                          'guard_expr': ''},
            },
        }
        self.verifyWorkflow(wfdef, wfstates, wftransitions, {}, {})

        workspace_chains = {'Wiki': 'workspace_wiki_wf'}
        section_chains = {'Wiki': 'section_wiki_wf'}

        ws = self.portal['workspaces']
        self.verifyLocalWorkflowChains(ws, workspace_chains)

        se = self.portal['sections']
        self.verifyLocalWorkflowChains(se, section_chains)


    def updatePortalTree(self):
        """ register folderish document types in portal_tree
        """
        self.log("Registering CPS Wiki n portal_tree")

        portal_trees = self.portal.portal_trees

        types = list(portal_trees.workspaces.type_names)
        if 'Wiki' not in types:
            types = types + ['Wiki']
            portal_trees.workspaces.manage_changeProperties(type_names=types)
            portal_trees.workspaces.manage_rebuild()

        types = list(portal_trees.sections.type_names)
        if 'Wiki' not in types:
            types = types + ['Wiki']
            portal_trees.sections.manage_changeProperties(type_names=types)
            portal_trees.sections.manage_rebuild()


    def installNewPermissions(self):
        """Installs new permissions
        """
        return
        # Removing old CPSWiki permissions that are now deprecated
##         deleteWikiPage = 'Delete CPSWiki Page'
##         editWikiPage = 'Edit CPSWiki Page'
##         addWikiPage = 'Add CPSWiki Page'
##         viewWikiPage = 'View CPSWiki Page'

##         setDefaultRoles(addWikiPage, ('Manager', 'Owner'))
##         setDefaultRoles(editWikiPage, ('Manager', 'Owner'))
##         setDefaultRoles(deleteWikiPage, ('Manager', 'Owner'))
##         setDefaultRoles(viewWikiPage, ('Manager', 'Owner'))

##         # Workspace
##         wiki_ws_perms = [addWikiPage,
##                          viewWikiPage,
##                          editWikiPage,
##                          deleteWikiPage,
##                          ]

##         for perm in wiki_ws_perms:
##             self.portal[WORKSPACES_ID].manage_permission(perm, roles, 0)
##             self.portal[SECTIONS_ID].manage_permission(perm, roles, 0)


def install(self):
    installer = CPSWikiInstaller(self)
    installer.install()
    return installer.logResult()
