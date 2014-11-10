# -*- coding: utf8 -*-
import deform
from pyramid.view import view_config

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.form import  FormView
from pontus.schema import select

from novaideo.content.processes.amendment_management.behaviors import  Associate
from novaideo.content.amendment import Amendment
from novaideo import _
from novaideo.views.idea_management.associate import (
    RelatedContentsView, 
    AssociateView as AssociateIdeaView)
from novaideo.content.correlation import CorrelationSchema, Correlation


class AssociateFormView(FormView):

    title = _('Associate')
    schema = select(CorrelationSchema(factory=Correlation, editable=True),
                    ['targets', 'intention', 'comment'])
    behaviors = [Associate]
    formid = 'formassociate'
    name = 'associateform'

    def before_update(self):
        target = self.schema.get('targets')
        target.title = _("Related contents")
        formwidget = deform.widget.FormWidget(css_class='controled-form', 
                                    activable=True,
                                    button_css_class="pull-right",
                                    picto_css_class="glyphicon glyphicon-link",
                                    button_title=_("Associate"))
        formwidget.template = 'novaideo:views/templates/ajax_form.pt'
        self.schema.widget = formwidget


@view_config(
    name='associateamendment',
    context=Amendment,
    renderer='pontus:templates/view.pt',
    )
class AssociateView(AssociateIdeaView):
    title = _('Associate the amendment')
    description = _("Associate the amendment to an other content")
    views = (RelatedContentsView, AssociateFormView)


DEFAULTMAPPING_ACTIONS_VIEWS.update({Associate:AssociateView})
