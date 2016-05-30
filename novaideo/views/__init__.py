# Copyright (c) 2015 by Ecreall under licence AGPL terms
# avalaible on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi, Sophie Jazwiecki
import datetime
import pytz
from pyramid.view import view_config
from persistent.list import PersistentList

from substanced.util import get_oid

from dace.processinstance.core import DEFAULTMAPPING_ACTIONS_VIEWS
from dace.util import find_catalog, getAllBusinessAction, getBusinessAction
from dace.objectofcollaboration.principal.util import get_current
from dace.objectofcollaboration.entity import Entity
from pontus.view import BasicView

from novaideo.views.idea_management.comment_idea import (
    CommentsView)
from novaideo.views.idea_management.present_idea import (
    SentToView)
from novaideo.content.interface import (
    IPerson,
    ICorrelableEntity,
    Iidea)
from novaideo.views.filter import find_entities, FILTER_SOURCES


ALL_VALUES_KEY = "*"


def is_all_values_key(key):
    value = key.replace(" ", "")
    return not value or value == ALL_VALUES_KEY


class IndexManagementJsonView(BasicView):

    def _get_pagin_data(self):
        page_limit = self.params('pageLimit')
        if page_limit is None:
            page_limit = 10
        else:
            page_limit = int(page_limit)

        current_page = self.params('page')
        if current_page is None:
            current_page = 1
        else:
            current_page = int(current_page)

        start = page_limit * (current_page - 1)
        end = start + page_limit
        return page_limit, current_page, start, end

    def __call__(self):
        operation_name = self.params('op')
        if operation_name is not None:
            operation = getattr(self, operation_name, None)
            if operation is not None:
                return operation()

        return {}


@view_config(name='novaideoapi',
             context=Entity,
             xhr=True,
             renderer='json')
class NovaideoAPI(IndexManagementJsonView):
    alert_template = 'novaideo:views/templates/alerts/alerts.pt'

    def find_user(self):
        name = self.params('q')
        if name:
            page_limit, current_page, start, end = self._get_pagin_data()
            if is_all_values_key(name):
                result = find_entities(interfaces=[IPerson],
                                       metadata_filter={'states': ['active']})
            else:
                result = find_entities(interfaces=[IPerson],
                                       text_filter={'text_to_search': name},
                                       metadata_filter={'states': ['active']})

            result = [res for res in result]
            if len(result) >= start:
                result = result[start:end]
            else:
                result = result[:end]

            default_img_url = self.request.static_url(
                'novaideo:static/images/user100.png')
            entries = [{'id': str(get_oid(e)),
                        'text': e.title,
                        'img_url': e.get_picture_url(
                            'profil', default_img_url)}
                       for e in result]
            result = {'items': entries, 'total_count': len(result)}
            return result

        return {'items': [], 'total_count': 0}

    def find_base_review(self):
        name = self.params('q')
        if name:
            user = get_current()
            page_limit, current_page, start, end = self._get_pagin_data()
            if is_all_values_key(name):
                result = find_entities(
                    user=user,
                    interfaces=[IBaseReview])
            else:
                result = find_entities(
                    user=user,
                    interfaces=[IBaseReview],
                    text_filter={'text_to_search': name})

            total_count = len(result)
            if total_count >= start:
                result = list(result)[start:end]
            else:
                result = list(result)[:end]

            entries = [{'id': str(get_oid(e)),
                        'text': e.title,
                        'icon': e.icon} for e in result]
            result = {'items': entries, 'total_count': total_count}
            return result

        return {'items': [], 'total_count': 0}

    def find_entity(self, interfaces=[], states=['published', 'active'], query=None):
        name = self.params('q')
        if name:
            user = get_current()
            page_limit, current_page, start, end = self._get_pagin_data()
            if is_all_values_key(name):
                result = find_entities(
                    interfaces=interfaces,
                    metadata_filter={
                        'states': states},
                    user=user,
                    add_query=query)
            else:
                result = find_entities(
                    interfaces=interfaces,
                    metadata_filter={
                        'states': states},
                    user=user,
                    text_filter={'text_to_search': name},
                    add_query=query)

            total_count = len(result)
            if total_count >= start:
                result = list(result)[start:end]
            else:
                result = list(result)[:end]

            entries = [{'id': str(get_oid(e)),
                        'text': e.title,
                        'icon': getattr(
                            e, 'icon', 'glyphicon glyphicon-question-sign')}
                       for e in result]
            result = {'items': entries, 'total_count': total_count}
            return result

        return {'items': [], 'total_count': 0}

    def find_correlable_entity(self):
        return self.find_entity(interfaces=[ICorrelableEntity])

    def find_ideas(self):
        novaideo_index = find_catalog('novaideo')
        is_workable_index = novaideo_index['is_workable']
        query = is_workable_index.eq(True)
        return self.find_entity(interfaces=[Iidea], states=[], query=query)

    def filter_result(self):
        filter_source = self.params('filter_source')
        if filter_source is not None and FILTER_SOURCES.get(filter_source, None):
            view_source = FILTER_SOURCES[filter_source](
                self.context, self.request)
            result = view_source.update()
            body = result['coordinates'][view_source.coordinates][0]['body']
            return {'body': body}

        return {'body': ''}

    def present_entity(self):
        present_actions = getAllBusinessAction(
            self.context, self.request, node_id='present')
        if present_actions:
            action = present_actions[0]
            present_view = DEFAULTMAPPING_ACTIONS_VIEWS[action.__class__]
            present_view_instance = present_view(
                self.context, self.request,
                behaviors=[action])
            present_view_instance.update()
            result_view = SentToView(self.context, self.request)
            body = result_view.update()['coordinates'][result_view.coordinates][0]['body']
            return {'body': body}

        return {'body': ''}

    def comment_entity(self):
        comment_actions = getAllBusinessAction(
            self.context, self.request, node_id='comment')
        if comment_actions:
            action = comment_actions[0]
            comment_view = DEFAULTMAPPING_ACTIONS_VIEWS[action.__class__]
            comment_view_instance = comment_view(
                self.context, self.request,
                behaviors=[action])
            comment_view_instance.update()
            result_view = CommentsView(self.context, self.request)
            body = result_view.update()['coordinates'][result_view.coordinates][0]['body']
            return {'body': body}

        return {'body': ''}

    def respond_comment(self):
        comment_actions = getAllBusinessAction(
            self.context, self.request, node_id='respond')
        if comment_actions:
            action = comment_actions[0]
            comment_view = DEFAULTMAPPING_ACTIONS_VIEWS[action.__class__]
            comment_view_instance = comment_view(
                self.context, self.request,
                behaviors=[action])
            comment_view_instance.update()
            self.request.POST.clear()
            result_view = CommentsView(self.context.subject, self.request)
            body = result_view.update()['coordinates'][result_view.coordinates][0]['body']
            return {'body': body}

        return {'body': ''}

    def get_user_alerts(self):
        user = get_current()
        objects = getattr(user, 'alerts', [])
        now = datetime.datetime.now(tz=pytz.UTC)
        objects = sorted(
            objects,
            key=lambda e: getattr(e, 'modified_at', now),
            reverse=True)
        result_body = []
        for obj in objects:
            render_dict = {
                'object': obj,
                'current_user': user
            }
            body = self.content(args=render_dict,
                                template=obj.get_templates()['small'])['body']
            result_body.append(body)

        values = {'bodies': result_body}
        body = self.content(args=values, template=self.alert_template)['body']
        return {'body': body}

    def _execute_action(self, process_id, node_id, appstruct):
        actions = getBusinessAction(
            self.context, self.request,
            process_id, node_id)
        if actions:
            try:
                action = actions[0]
                action.validate(self.context, self.request)
                action.before_execution(self.context, self.request)
                action.execute(self.context, self.request, appstruct)
                return {'state': True}
            except Exception:
                return {'state': False}

        return {'state': False}

    def oppose_idea(self):
        result = self._execute_action('ideamanagement', 'oppose', {})
        if not result.get('state'):
            self._execute_action(
                'ideamanagement', 'withdraw_token', {})
            result = self._execute_action(
                'ideamanagement', 'oppose', {})
            result['change'] = True

        if result.get('state'):
            result['action'] = self.request.resource_url(
                self.context, 'novaideoapi',
                query={'op': 'withdraw_token_idea',
                       'action': 'oppose'})
            if result.get('change', False):
                result['opposit_action'] = self.request.resource_url(
                    self.context, 'novaideoapi',
                    query={'op': 'support_idea'})

        return result

    def oppose_proposal(self):
        result = self._execute_action('proposalmanagement', 'oppose', {})
        if not result.get('state'):
            self._execute_action(
                'proposalmanagement', 'withdraw_token', {})
            result = self._execute_action(
                'proposalmanagement', 'oppose', {})
            result['change'] = True

        if result.get('state'):
            result['action'] = self.request.resource_url(
                self.context, 'novaideoapi',
                query={'op': 'withdraw_token_proposal',
                       'action': 'oppose'})
            if result.get('change', False):
                result['opposit_action'] = self.request.resource_url(
                    self.context, 'novaideoapi',
                    query={'op': 'support_proposal'})

        return result

    def support_idea(self):
        result = self._execute_action('ideamanagement', 'support', {})
        if not result.get('state'):
            self._execute_action(
                'ideamanagement', 'withdraw_token', {})
            result = self._execute_action(
                'ideamanagement', 'support', {})
            result['change'] = True

        if result.get('state'):
            result['action'] = self.request.resource_url(
                self.context, 'novaideoapi',
                query={'op': 'withdraw_token_idea',
                       'action': 'support'})
            if result.get('change', False):
                result['opposit_action'] = self.request.resource_url(
                    self.context, 'novaideoapi',
                    query={'op': 'oppose_idea'})

        return result

    def support_proposal(self):
        result = self._execute_action('proposalmanagement', 'support', {})
        if not result.get('state'):
            self._execute_action(
                'proposalmanagement', 'withdraw_token', {})
            result = self._execute_action(
                'proposalmanagement', 'support', {})
            result['change'] = True

        if result.get('state'):
            result['action'] = self.request.resource_url(
                self.context, 'novaideoapi',
                query={'op': 'withdraw_token_proposal',
                       'action': 'support'})
            if result.get('change', False):
                result['opposit_action'] = self.request.resource_url(
                    self.context, 'novaideoapi',
                    query={'op': 'oppose_proposal'})

        return result

    def withdraw_token_idea(self):
        result = self._execute_action('ideamanagement', 'withdraw_token', {})
        if result.get('state'):
            previous_action = self.params('action')
            result['action'] = self.request.resource_url(
                self.context, 'novaideoapi',
                query={'op': previous_action + '_idea'})
            result['withdraw'] = True

        return result

    def withdraw_token_proposal(self):
        result = self._execute_action(
            'proposalmanagement', 'withdraw_token', {})
        if result.get('state'):
            previous_action = self.params('action')
            result['action'] = self.request.resource_url(
                self.context, 'novaideoapi',
                query={'op': previous_action + '_proposal'})
            result['withdraw'] = True

        return result

    def update_notification_id(self):
        user = get_current()
        notif_id = self.params('id')
        if hasattr(user, 'notification_ids'):
            user.notification_ids = PersistentList([])

        user.notification_ids.append(notif_id)
        return {'ids': list(ser.notification_ids)}
