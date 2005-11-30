# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziad� <tz@nuxeo.com>
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

from Products.CPSInstaller.CPSInstaller import CPSInstaller

try:
    from Products.CMFCore.permissions import \
    View, ModifyPortalContent, AddPortalContent, DeleteObjects, setDefaultRoles
except ImportError:
    # CPS 3.2
    from Products.CMFCore.CMFCorePermissions import \
    View, ModifyPortalContent, AddPortalContent, DeleteObjects, setDefaultRoles

try:
    from Products.CPSWorkflow.transitions import \
     TRANSITION_INITIAL_PUBLISHING, TRANSITION_INITIAL_CREATE, \
     TRANSITION_ALLOWSUB_CREATE, TRANSITION_ALLOWSUB_PUBLISHING, \
     TRANSITION_BEHAVIOR_PUBLISHING, TRANSITION_BEHAVIOR_FREEZE, \
     TRANSITION_BEHAVIOR_DELETE, TRANSITION_BEHAVIOR_MERGE, \
     TRANSITION_ALLOWSUB_CHECKOUT, TRANSITION_INITIAL_CHECKOUT, \
     TRANSITION_BEHAVIOR_CHECKOUT, TRANSITION_ALLOW_CHECKIN, \
     TRANSITION_BEHAVIOR_CHECKIN, TRANSITION_ALLOWSUB_DELETE, \
     TRANSITION_ALLOWSUB_MOVE, TRANSITION_ALLOWSUB_COPY
except ImportError:
    # CPS 3.2
    from Products.CPSCore.CPSWorkflow import \
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

SKINS = {'cps_wiki': 'Products/CPSWiki/skins/cps_wiki'}

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
        self.setupTranslations()
        self.finalize()
        self.reindexCatalog()
        self.updateExistingWikis()
        self.log("CPSWiki Install / Update .........[ S T O P ]  ")

    def verifyPortalTypes(self):
        """Verify portal types
        """
        ptypes = {
            'Wiki': {
                'typeinfo_name': 'CPSWiki: Wiki (Wiki)',
                'add_meta_type': 'Factory-based Type Information',
                'allowed_content_types': ('Wiki Page',),
                },
            'Wiki Page': {
                'typeinfo_name': 'CPSWiki: Wiki Page (Wiki Page)',
                'add_meta_type': 'Factory-based Type Information',
                'allowed_content_types': (),
                },
            }
        self.verifyContentTypes(ptypes, destructive=1)
        self.allowContentTypes('Wiki', ('Workspace', 'Section'))
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


    def updateWiki(self, wiki):
        """ upgrade Wiki instances """
        from Products.CPSWiki.wikipage import WikiPage
        from Products.CPSWiki.wikirelations import WikiRelation, \
                                                   ZODBBackend
        if not hasattr(wiki, 'version') or wiki.version != (0, 7):
            # < 0.6, need to add _relation to all wiki pages
            # and to upgrade links
            wiki.version = (0, 7)
            for id, object in wiki.objectItems():
                if object.portal_type != WikiPage.portal_type:
                    continue
                self.log('upgrading page %s' % object.id)
                object._relations = WikiRelation(object, ZODBBackend())

            self.log('clearing caches and rebuilding relations')
            count = 0
            for id, object in wiki.objectItems():
                if object.portal_type != WikiPage.portal_type:
                    continue
                object.updateCache()
                count += 1
            self.log('upgraded %d pages for wiki %s' % (count, wiki.id))

    def updateExistingWikis(self):
        """ look in the portal for Wiki instances """
        wikis = self.portal.portal_catalog(portal_type='Wiki')
        for wiki in wikis:
            wiki_instance = wiki.getObject()
            if wiki_instance is None:
                continue
            self.updateWiki(wiki_instance)

def install(self):
    installer = CPSWikiInstaller(self)
    installer.install()
    return installer.logResult()
