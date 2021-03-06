# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.view import BasicView

from novaideo.content.processes.invitation_management.behaviors import (
    RemoveInvitation)
from novaideo.content.invitation import Invitation
from novaideo import _


@view_config(
    name='remove_invitation',
    context=Invitation,
    renderer='pontus:templates/views_templates/grid.pt',
    )
class RemoveInvitationView(BasicView):

    title = _('Remove the invitation')
    behaviors = [RemoveInvitation]
    name = 'remove_invitation'

    def update(self):
        results = self.execute(None)
        return results[0]


DEFAULTMAPPING_ACTIONS_VIEWS.update(
    {RemoveInvitation: RemoveInvitationView})
