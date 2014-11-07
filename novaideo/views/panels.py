# -*- coding: utf8 -*-
import datetime
from collections import OrderedDict
from pyramid import renderers
from pyramid_layout.panel import panel_config

from dace.objectofcollaboration.entity import Entity
from dace.util import getBusinessAction, getSite
from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from pontus.schema import select

from novaideo.content.processes.novaideo_view_manager.behaviors import(
    SeeMyContents,
    SeeMySelections,
    SeeMyParticipations,
    SeeMySupports)
from novaideo.content.processes.proposal_management.behaviors import (
    CreateProposal)
from novaideo.content.processes.idea_management.behaviors import CreateIdea
from novaideo.content.proposal import Proposal
from novaideo.content.idea import Idea
from novaideo.content.amendment import Amendment
from novaideo.core import _

USER_MENU_ACTIONS = {'menu1': [SeeMyContents, SeeMyParticipations],
                     'menu2': [SeeMySelections, SeeMySupports],
                     'menu3': [CreateIdea, CreateProposal]}


def _getaction(view, process_id, action_id):
    root = getSite()
    actions = getBusinessAction(process_id, action_id, '', view.request, root)
    action = None
    action_view = None
    if actions is not None:
        action = actions[0]
        if action.__class__ in DEFAULTMAPPING_ACTIONS_VIEWS:
            action_view = DEFAULTMAPPING_ACTIONS_VIEWS[action.__class__]

    return action, action_view


@panel_config(
    name='usermenu',
    context = Entity ,
    renderer='templates/panels/usermenu.pt'
    )
class Usermenu_panel(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request


    def __call__(self):
        root = getSite()
        search_action, search_view = _getaction(self,
                                                'novaideoviewmanager',
                                                'search')
        search_view_instance = search_view(root, self.request,
                                           behaviors=[search_action])
        search_view_instance.viewid = 'usermenu' + search_view_instance.viewid 
        posted_formid = None
        if self.request.POST :
            if '__formid__' in self.request.POST:
                posted_formid = self.request.POST['__formid__']

            if posted_formid and \
              posted_formid.startswith(search_view_instance.viewid):
                search_view_instance.postedform = self.request.POST.copy()
                self.request.POST.clear()

        search_view_instance.schema = select(search_view_instance.schema,
                                             ['text'])
        search_view_result = search_view_instance()
        search_body = ''
        if isinstance(search_view_result, dict) and \
          'coordinates' in search_view_result:
            search_body = search_view_instance.render_item(
                    search_view_result['coordinates'][search_view_instance.coordinates][0],
                    search_view_instance.coordinates,
                    None)

        result = {}
        result['search_body'] = search_body
        result['view'] = self
        return result


@panel_config(
    name = 'usernavbar',
    context = Entity ,
    renderer='templates/panels/navbar_view.pt'
    )
class UserNavBarPanel(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request


    def __call__(self):
        root = getSite()
        search_action, search_view = _getaction(self, 
                                                'novaideoviewmanager',
                                                'search')
        search_view_instance = search_view(root, self.request,
                                           behaviors=[search_action])
        actions_url = {'menu1': OrderedDict(),
                       'menu2': OrderedDict(),
                       'menu3': OrderedDict()}
        for (menu, actions) in USER_MENU_ACTIONS.items():
            for actionclass in actions:
                process_id, action_id = tuple(actionclass.node_definition.id.split('.'))
                action, view = _getaction(self, process_id, action_id)
                if not (None in (action, view)):
                    actions_url[menu][action.title] = {'action':action,
                                                       'url':action.url(root),
                                                       'view_name': getattr(view,'name', None)}
                else:
                    actions_url[menu][actionclass.node_definition.title] = {'action':None,
                                                                            'url':None,
                                                                            'view_name': getattr(view,'name', None)}

        posted_formid = None
        if self.request.POST :
            if '__formid__' in self.request.POST:
                posted_formid = self.request.POST['__formid__']

            if posted_formid and \
               posted_formid.startswith(search_view_instance.viewid):
                search_view_instance.postedform = self.request.POST.copy()
                self.request.POST.clear()

        search_view_result = search_view_instance()
        search_body = ''
        if isinstance(search_view_result, dict) and \
           'coordinates' in search_view_result:
            search_body = search_view_instance.render_item(
                              search_view_result['coordinates'][search_view_instance.coordinates][0],
                              search_view_instance.coordinates,
                              None)

        result = {}
        result['actions'] = actions_url
        result['search_body'] = search_body
        result['view'] = self
        return result


@panel_config(
    name = 'steps',
    context = Entity ,
    renderer='templates/panels/steps.pt'
    )
class StepsPanel(object):
    step4_template = 'novaideo:views/templates/panels/step4.pt'
    step3_0_template = 'novaideo:views/templates/panels/step3_0.pt'
    step3_1_template = 'novaideo:views/templates/panels/step3_1.pt'
    step3_2_template = 'novaideo:views/templates/panels/step3_2.pt'
    step3_3_template = 'novaideo:views/templates/panels/step3_3.pt'

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _get_process_context(self):
        if isinstance(self.context, Amendment):
            return self.context.proposal

        return self.context

    def _days_hours_minutes(self, td):
        return td.days, td.seconds//3600, (td.seconds//60)%60

    def _get_step3_informations(self, context, request):
        time_delta = None
        process = context.creator
        if any(s in context.state for s in ['proofreading','amendable']):
            date_iteration = process['timer'].eventKind.time_date
            if date_iteration is not None:
                time_delta = date_iteration - datetime.datetime.today()
                time_delta = self._days_hours_minutes(time_delta)

            return renderers.render(self.step3_1_template,
                                    {'context':context, 
                                     'duration':time_delta,
                                     'process': process},
                                    request)
        elif 'votes for publishing'  in context.state:
            ballot = process.vp_ballot
            if ballot.finished_at is not None:
                time_delta = ballot.finished_at - datetime.datetime.today()
                time_delta = self._days_hours_minutes(time_delta)

            return renderers.render(self.step3_3_template,
                                    {'context': context, 
                                     'duration': time_delta,
                                     'process': process,
                                     'ballot_report': ballot.report},
                                    request)
        elif 'votes for amendments'  in context.state:
            voters = []
            [voters.extend(b.report.voters) \
            for b in process.amendments_ballots]
            voters = list(set(voters))
            ballot = process.amendments_ballots[-1]
            if ballot.finished_at is not None:
                time_delta = ballot.finished_at - datetime.datetime.today()
                time_delta = self._days_hours_minutes(time_delta)

            return renderers.render(self.step3_2_template,
                                    {'context':context, 
                                     'duration':time_delta,
                                     'process': process,
                                     'ballot_report': ballot.report,
                                     'voters': voters},
                                    request)
        elif 'open to a working group'  in context.state:
            return renderers.render(self.step3_0_template,
                                   {'context':context, 
                                    'process': process,
                                    'min_members': getSite().participants_mini},
                                   request)

        return _('No more Information.')

    def _get_step4_informations(self, context, request):       
        return renderers.render(self.step4_template,
                                {'context':context},
                                request)

    def __call__(self):
        root = getSite()
        result = {}
        context = self._get_process_context()
        result['condition'] = isinstance(context, (Proposal, Idea))
        result['current_step'] = 1
        result['step4_message'] = ""
        result['step3_message'] = ""
        if isinstance(context, Proposal):
            if 'draft' in context.state:
                result['current_step'] = 2
            elif 'published' in context.state:
                result['current_step'] = 4
                result['step4_message'] = self._get_step4_informations(context,
                                                                   self.request)
            elif not ('archived' in context.state):
                result['current_step'] = 3
                result['step3_message'] = self._get_step3_informations(context,
                                                                   self.request)
            elif 'archived' in context.state:
                result['current_step'] = 0

        return result