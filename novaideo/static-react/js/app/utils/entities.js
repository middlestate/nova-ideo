/* eslint-disable import/prefer-default-export, no-underscore-dangle, no-param-reassign */
import HelpIcon from 'material-ui-icons/Help';
import { ICONS_MAPPING } from '../constants';

function equal(element, filter, defaultValue = true) {
  if (!filter) return defaultValue;
  if (typeof filter === 'object') return filter.includes(element);
  return filter === element;
}
// filter = { descriminator: undefined, processId: undefined, nodeId: undefined }
export function filterActions(actions, filter = {}) {
  if (!actions) return [];
  const validKeys = Object.keys(filter).filter((key) => {
    return filter[key];
  });
  return actions.filter((action) => {
    return validKeys.every((key) => {
      return key in action && equal(action[key], filter[key]);
    });
  });
}

export function getActions(actions, filter = {}) {
  if (!actions) return [];
  const newActions = filterActions(actions, filter).map((action) => {
    const newAction = { ...action };
    newAction.icon = action.icon in ICONS_MAPPING ? ICONS_MAPPING[action.icon] : HelpIcon;
    return newAction;
  });
  newActions.sort((a1, a2) => {
    return a1.order - a2.order;
  });
  return newActions;
}

export function getAction(actions, filter = {}) {
  return getActions(actions, filter)[0];
}