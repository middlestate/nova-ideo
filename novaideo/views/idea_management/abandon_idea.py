
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.view import BasicView

from novaideo.content.processes.idea_management.behaviors import  AbandonIdea
from novaideo.content.idea import Idea
from novaideo import _


@view_config(
    name='abandonidea',
    context=Idea,
    renderer='pontus:templates/view.pt',
    )
class AbandonIdeaView(BasicView):
    title = _('Archive')
    name = 'abandonidea'
    behaviors = [AbandonIdea]
    viewid = 'abandonidea'

    def update(self):
        self.execute(None)        
        return list(self.behaviorinstances.values())[0].redirect(self.context, self.request)

DEFAULTMAPPING_ACTIONS_VIEWS.update({AbandonIdea:AbandonIdeaView})
