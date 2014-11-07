
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.default_behavior import Cancel
from pontus.form import FormView
from pontus.schema import select

from novaideo.content.processes.amendment_management.behaviors import (
    DuplicateAmendment)
from novaideo.content.amendment import Amendment, AmendmentSchema
from novaideo import _



@view_config(
    name='duplicateamendment',
    context=Amendment,
    renderer='pontus:templates/view.pt',
    )
class DuplicateAmendmentView(FormView):
    title = _('Duplicate')
    name = 'duplicateamendment'
    schema = select(AmendmentSchema(), 
                    ['description',
                     'keywords',
                     'text'])

    behaviors = [DuplicateAmendment, Cancel]
    formid = 'formduplicateamendment'

    def default_data(self):
        return self.context


DEFAULTMAPPING_ACTIONS_VIEWS.update({DuplicateAmendment:DuplicateAmendmentView})