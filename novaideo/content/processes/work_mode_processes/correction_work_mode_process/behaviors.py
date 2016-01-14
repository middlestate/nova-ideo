# -*- coding: utf8 -*-
# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# avalaible on http://www.gnu.org/licenses/agpl.html 

# licence: AGPL
# author: Amen Souissi

"""
This module represent all of behaviors used in the 
Proposal management process definition. 
"""

from persistent.list import PersistentList
from bs4 import BeautifulSoup
from pyramid.httpexceptions import HTTPFound
from pyramid.threadlocal import get_current_registry
from pyramid import renderers

from substanced.util import get_oid

from dace.util import copy, getSite
from dace.objectofcollaboration.principal.util import (
    has_role,
    get_current,
    grant_roles)
from daceui.interfaces import IDaceUIAPI
#from dace.objectofcollaboration import system
from dace.processinstance.activity import (
    InfiniteCardinality, ActionType, ElementaryAction)

from novaideo.content.correlation import CorrelationType
from novaideo.content.interface import IProposal, ICorrection
from ...user_management.behaviors import global_user_processsecurity
from novaideo import _
from novaideo.utilities.text_analyzer import (
    ITextAnalyzer,
    normalize_text)
from novaideo.utilities.util import connect
from novaideo.content.alert import (
    WorkingGroupAlert)

try:
    basestring
except NameError:
    basestring = str


DEFAULT_NB_CORRECTORS = 1


def valid_correction(process, correction, current_version, user):
    correction.state.remove('in process')
    correction.state.append('processed')
    proposal = correction.proposal
    wg = proposal.working_group
    root = getSite()
    contextname = current_version.__name__
    root.addtoproperty('proposals', current_version, moving=current_version)
    current_version.setproperty('version', proposal)
    root.rename(current_version.__name__, contextname)
    current_version.state = PersistentList(['amendable', 'published'])
    current_version.setproperty('author', proposal.author)
    current_version.setproperty('comments', proposal.comments)
    current_version.keywords = proposal.keywords
    current_version.setproperty('attached_files', proposal.attached_files)
    related_ideas = proposal.related_ideas
    connect(current_version,
        related_ideas,
        {'comment': _('Add related ideas'),
         'type': _('New version')},
        user,
        ['related_proposals', 'related_ideas'],
        CorrelationType.solid)
    proposal.state = PersistentList(['archived'])
    process.attachedTo.process.execution_context.add_created_entity(
        'proposal', current_version)
    wg.setproperty('proposal', current_version)
    for member in wg.members:
        grant_roles(member, (('Participant', current_version),))

    current_version.reindex()
    proposal.reindex()
    process.attachedTo.process.reindex()
    process.reindex()


def correctitem_relation_validation(process, context):
    return process.execution_context.has_relation(context.proposal, 'proposal')


def correctitem_roles_validation(process, context):
    return has_role(role=('Participant', context.proposal))


def correctitem_processsecurity_validation(process, context):
    return global_user_processsecurity(process, context)


def correctitem_state_validation(process, context):
    return 'active' in context.proposal.working_group.state and \
           'amendable' in context.proposal.state


class CorrectItem(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    isSequential = True
    context = ICorrection
    relation_validation = correctitem_relation_validation
    roles_validation = correctitem_roles_validation
    processsecurity_validation = correctitem_processsecurity_validation
    state_validation = correctitem_state_validation

    def _include_to_proposal(self, context, proposal, text_to_correct, request, content):
        corrections = [item for item in context.corrections.keys()
                       if 'included' not in context.corrections[item]]
        text = self._include_items(text_to_correct, request, corrections)
        if content == 'description' or content == 'title':
            text = text.replace('<p>', '').replace('</p>', '')

        setattr(proposal, content, text)

    def _include_items(self, text, request, items, to_add=False):
        text_analyzer = get_current_registry().getUtility(
            ITextAnalyzer, 'text_analyzer')
        todel = "ins"
        toins = "del"
        if to_add:
            todel = "del"
            toins = "ins"

        soup = BeautifulSoup(text)
        corrections = []
        for item in items:
            corrections.extend(soup.find_all('span', {'id': 'correction',
                                                      'data-item': item}))

        blocstodel = ('span', {'id': 'correction_actions'})
        soup = text_analyzer.include_diffs(
            soup, corrections, todel, toins, blocstodel)
        return text_analyzer.soup_to_text(soup)

    def _include_vote(self, context, request, item,
                      content, vote, user_oid, user):
        text_to_correct = getattr(context, content, '')
        context.corrections[item][vote].append(user_oid)
        len_vote = len(context.corrections[item][vote])
        vote_bool = False
        if vote == 'favour':
            len_vote -= 1
            vote_bool = True

        if len_vote >= DEFAULT_NB_CORRECTORS:
            text = self._include_items(
                text_to_correct, request, [item], vote_bool)
            setattr(context, content, text)
            text_to_correct = getattr(context, content, '')
            context.corrections[item]['included'] = True
            current_version = context.current_version
            if not any('included' not in context.corrections[c]
                       for c in context.corrections.keys()):
                valid_correction(self.process, context, current_version, user)

            self._include_to_proposal(context, current_version, text_to_correct,
                                      request, content)

    def start(self, context, request, appstruct, **kw):
        item = appstruct['item']
        content = appstruct['content']
        vote = (appstruct['vote'].lower() == 'true')
        user = get_current()
        user_oid = get_oid(user)
        correction_data = context.corrections[item]
        if user_oid not in correction_data['favour'] and \
           user_oid not in correction_data['against']:
            if vote:
                self._include_vote(context, request,
                                   item, content,
                                   'favour', user_oid, user)
            else:
                self._include_vote(context, request,
                                   item, content,
                                   'against', user_oid, user)

        return {}

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def correct_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def correct_roles_validation(process, context):
    return has_role(role=('Participant', context))


def correct_processsecurity_validation(process, context):
    correction_in_process = any(('in process' in c.state
                                 for c in context.corrections))

    return not correction_in_process and \
           not getattr(context.working_group, 'first_decision', True) and \
           global_user_processsecurity(process, context)


def correct_state_validation(process, context):
    return 'active' in context.working_group.state and\
           'amendable' in context.state


class CorrectProposal(InfiniteCardinality):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'text-action'
    style_picto = 'glyphicon glyphicon-edit'
    style_order = 2
    submission_title = _('Save')
    correction_item_template = 'novaideo:views/proposal_management/templates/correction_item.pt'
    isSequential = True
    context = IProposal
    processs_relation_id = 'proposal'
    relation_validation = correct_relation_validation
    roles_validation = correct_roles_validation
    processsecurity_validation = correct_processsecurity_validation
    state_validation = correct_state_validation

    def _get_newversion(self, context, correction):
        copy_of_proposal = copy(context,
                                (correction, 'current_version'),
                                new_name=context.__name__,
                                omit=('created_at', 'modified_at',
                                      'corrections'),
                                roles=True)
        copy_of_proposal.setproperty('originalentity', context.originalentity)
        copy_of_proposal.state = PersistentList(['archived'])
        copy_of_proposal.reindex()
        return copy_of_proposal

    def _add_vote_actions(self, tag, correction, request):
        dace_ui_api = get_current_registry().getUtility(IDaceUIAPI,
                                                        'dace_ui_api')
        if not hasattr(self, '_correctitemaction'):
            correctitemnode = self.process['correctitem']
            correctitem_wis = [wi for wi in correctitemnode.workitems
                               if wi.node is correctitemnode]
            if correctitem_wis:
                self._correctitemaction = correctitem_wis[0].actions[0]

        if hasattr(self, '_correctitemaction'):
            actionurl_update = dace_ui_api.updateaction_viewurl(
                request=request,
                action_uid=str(get_oid(self._correctitemaction)),
                context_uid=str(get_oid(correction)))
            values = {'favour_action_url': actionurl_update,
                      'against_action_url': actionurl_update}
            body = renderers.render(
                self.correction_item_template, values, request)
            correction_item_soup = BeautifulSoup(body)
            tag.append(correction_item_soup.body)
            tag.body.unwrap()

    def _add_actions(self, correction, request, soup):
        corrections_tags = soup.find_all('span', {'id': 'correction'})
        for correction_tag in corrections_tags:
            self._add_vote_actions(correction_tag, correction, request)

    def _identify_corrections(self, soup, correction, descriminator, content):
        correction_tags = soup.find_all('span', {'id': "correction"})
        correction_oid = str(get_oid(correction))
        user = get_current()
        user_oid = get_oid(user)
        for correction_tag in correction_tags:
            correction_tag['data-correction'] = correction_oid
            correction_tag['data-item'] = str(descriminator)
            correction_tag['data-content'] = content
            init_vote = {'favour': [user_oid], 'against': []}
            correction.corrections[str(descriminator)] = init_vote
            descriminator += 1

        return descriminator      

    def start(self, context, request, appstruct, **kw):
        user = get_current()
        correction = appstruct['_object_data']
        correction.text = normalize_text(correction.text)
        old_text = correction.text
        correction.setproperty('author', user)
        context.addtoproperty('corrections', correction)
        self._get_newversion(context, correction)
        text_analyzer = get_current_registry().getUtility(
                                                ITextAnalyzer,
                                                'text_analyzer')
        souptextdiff, textdiff = text_analyzer.render_html_diff(
                                       getattr(context, 'text', ''),
                                       getattr(correction, 'text', ''),
                                       "correction")
        soupdescriptiondiff, descriptiondiff = text_analyzer.render_html_diff(
                                        getattr(context, 'description', ''),
                                        getattr(correction, 'description', ''),
                                        "correction")
        souptitlediff, titlediff = text_analyzer.render_html_diff(
                                        getattr(context, 'title', ''),
                                        getattr(correction, 'title', ''),
                                        "correction")
        descriminator = 0
        descriminator = self._identify_corrections(souptitlediff,
                                                   correction,
                                                   descriminator,
                                                   'title')
        self._add_actions(correction, request, souptitlediff)
        descriminator = self._identify_corrections(soupdescriptiondiff,
                                                   correction,
                                                   descriminator,
                                                   'description')
        self._add_actions(correction, request, soupdescriptiondiff)
        self._identify_corrections(souptextdiff, correction,
                                   descriminator, 'text')
        self._add_actions(correction, request, souptextdiff)
        correction.text = text_analyzer.soup_to_text(souptextdiff)
        correction.description = text_analyzer.soup_to_text(soupdescriptiondiff)
        correction.title = text_analyzer.soup_to_text(souptitlediff)
        if souptextdiff.find_all("span", id="correction") or \
           soupdescriptiondiff.find_all("span", id="correction") or\
           souptitlediff.find_all("span", id="correction"):
            correction.state.append('in process')
            alert = WorkingGroupAlert(alert_kind='correction_added')
            request.root.addtoproperty('alerts', alert)
            alert.init_alert(context.working_group.members, [context])
        else:
            context.text = old_text

        return {}

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))


def close_relation_validation(process, context):
    return process.execution_context.has_relation(context, 'proposal')


def close_roles_validation(process, context):
    return has_role(role=('System',))


def close_state_validation(process, context):
    wg = context.working_group
    return 'active' in wg.state and 'amendable' in context.state


class CloseWork(ElementaryAction):
    style = 'button' #TODO add style abstract class
    style_descriminator = 'global-action'
    style_order = 4
    context = IProposal
    actionType = ActionType.system
    processs_relation_id = 'proposal'
    roles_validation = close_roles_validation
    relation_validation = close_relation_validation
    state_validation = close_state_validation

    def start(self, context, request, appstruct, **kw):
        #TODO
        if context.corrections:
            last_correction = context.corrections[-1]
            if 'in process' in last_correction.state:
                current_version = last_correction.current_version
                valid_correction(self.process, last_correction,
                                 current_version, get_current())
                last_correction.state = PersistentList(['processed'])

        return {}

    def redirect(self, context, request, **kw):
        return HTTPFound(request.resource_url(context, "@@index"))

#TODO behaviors
