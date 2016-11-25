# -*- coding: utf8 -*-
# Copyright (c) 2016 by Ecreall under licence AGPL terms
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

from persistent.list import PersistentList
from zope.interface import Interface, implementer

from dace.util import Adapter, adapter
from dace.objectofcollaboration.principal.util import (
    revoke_roles, grant_roles)

from novaideo.content.interface import (
    IComment,
    Iidea,
    IProposal)
from novaideo.utilities.alerts_utility import alert
from novaideo.content.alert import InternalAlertKind
from novaideo.content.processes.proposal_management import end_work


class ISignalableObject(Interface):

    def censor(request):
        pass

    def restor(request):
        pass


@adapter(context=IComment)
@implementer(ISignalableObject)
class CommentAdapter(Adapter):
    """Return all keywords.
    """
    def censor(self, request):
        self.context.state = PersistentList(['censored'])
        members = [self.context.author]
        alert(
            'internal', [request.root], members,
            internal_kind=InternalAlertKind.moderation_alert,
            subjects=[self.context], alert_kind='object_censor')
        self.context.reindex()

    def restor(self, request):
        self.context.state = PersistentList(['published'])
        members = [self.context.author]
        alert(
            'internal', [request.root], members,
            internal_kind=InternalAlertKind.moderation_alert,
            subjects=[self.context], alert_kind='object_restor')
        self.context.reindex()


@adapter(context=Iidea)
@implementer(ISignalableObject)
class IdeaAdapter(Adapter):
    """Return all keywords.
    """
    def censor(self, request):
        self.context.state_befor_censor = PersistentList(
            list(self.context.state))
        self.context.state = PersistentList(['censored'])
        for token in list(self.context.tokens):
            token.owner.addtoproperty('tokens', token)

        members = [self.context.author]
        alert(
            'internal', [request.root], members,
            internal_kind=InternalAlertKind.moderation_alert,
            subjects=[self.context], alert_kind='object_censor')
        self.context.reindex()

    def restor(self, request):
        self.context.state = PersistentList(
            list(self.context.state_befor_censor))
        del self.context.state_befor_censor
        members = [self.context.author]
        alert(
            'internal', [request.root], members,
            internal_kind=InternalAlertKind.moderation_alert,
            subjects=[self.context], alert_kind='object_restor')
        self.context.reindex()


@adapter(context=IProposal)
@implementer(ISignalableObject)
class ProposalAdapter(Adapter):
    """Return all keywords.
    """
    def censor(self, request):
        self.context.state = PersistentList(['censored'])
        self.context.remove_tokens()
        author = self.context.author
        end_work(self.context, request)
        working_group = self.context.working_group
        working_group.state = PersistentList(['deactivated'])
        working_group.setproperty('wating_list', [])
        if hasattr(working_group, 'first_improvement_cycle'):
            del working_group.first_improvement_cycle

        if hasattr(working_group, 'first_vote'):
            del working_group.first_vote

        members = working_group.members
        alert(
            'internal', [request.root], members,
            internal_kind=InternalAlertKind.moderation_alert,
            subjects=[self.context], alert_kind='object_censor')
        if author in members:
            members.remove(author)

        for member in members:
            working_group.delfromproperty('members', member)
            revoke_roles(member, (('Participant', self.context),))

        self.context.reindex()
        working_group.reindex()

    def restor(self, request):
        self.context.state = PersistentList(['draft'])
        author = self.context.author
        working_group = self.context.working_group
        members = working_group.members
        if author not in members:
            grant_roles(user=author, roles=(('Participant', self.context), ))
            working_group.addtoproperty('members', author)

        members = working_group.members
        alert(
            'internal', [request.root], members,
            internal_kind=InternalAlertKind.moderation_alert,
            subjects=[self.context], alert_kind='object_restor')
        self.context.reindex()
        working_group.reindex()