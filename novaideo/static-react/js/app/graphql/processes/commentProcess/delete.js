import update from 'immutability-helper';
import { gql } from 'react-apollo';

import { filterActions } from '../../../utils/processes';
import { PROCESSES } from '../../../processes';

export const deleteMutation = gql`
  mutation($context: String) {
    deleteComment(context: $context) {
      status
    }
  }
`;

export default function deleteComment({ mutate }) {
  return ({ context, channel }) => {
    return mutate({
      variables: {
        context: context.oid
      },
      optimisticResponse: {
        __typename: 'Mutation',
        deleteComment: {
          __typename: 'DeleteComment',
          status: true
        }
      },
      updateQueries: {
        Comments: (prev, { mutationResult }) => {
          if (!mutationResult.data.deleteComment.status) return false;
          const currentComment = prev.node.comments.edges.filter((item) => {
            return item && item.node.id === context.id;
          })[0];
          const index = prev.node.comments.edges.indexOf(currentComment);
          return update(prev, {
            node: {
              lenComments: { $set: prev.node.lenComments - 1 },
              comments: {
                totalCount: { $set: prev.node.comments.totalCount - 1 },
                edges: {
                  $splice: [[index, 1]]
                }
              }
            }
          });
        },
        Comment: (prev, { mutationResult }) => {
          if (!mutationResult.data.deleteComment.status) return false;
          const currentComment = prev.node.comments.edges.filter((item) => {
            return item && item.node.id === context.id;
          })[0];
          const index = prev.node.comments.edges.indexOf(currentComment);
          return update(prev, {
            node: {
              lenComments: { $set: prev.node.lenComments - 1 },
              comments: {
                totalCount: { $set: prev.node.comments.totalCount - 1 },
                edges: {
                  $splice: [[index, 1]]
                }
              }
            }
          });
        },
        IdeasList: (prev) => {
          const currentIdea = prev.ideas.edges.filter((item) => {
            return item && item.node.oid === channel.subject.oid;
          })[0];
          if (!currentIdea) return false;
          const commentAction = filterActions(currentIdea.node.actions, {
            behaviorId: PROCESSES.ideamanagement.nodes.comment.nodeId
          })[0];

          const indexAction = currentIdea.node.actions.indexOf(commentAction);
          const newAction = update(commentAction, {
            counter: { $set: commentAction.counter - 1 }
          });
          const newIdea = update(currentIdea, {
            node: {
              actions: {
                $splice: [[indexAction, 1, newAction]]
              }
            }
          });
          const index = prev.ideas.edges.indexOf(currentIdea);
          return update(prev, {
            ideas: {
              edges: {
                $splice: [[index, 1, newIdea]]
              }
            }
          });
        },
        Idea: (prev, { queryVariables }) => {
          if (queryVariables.id !== channel.subject.id) return false;
          const commentAction = filterActions(prev.idea.actions, {
            behaviorId: PROCESSES.ideamanagement.nodes.comment.nodeId
          })[0];

          const indexAction = prev.idea.actions.indexOf(commentAction);
          const newAction = update(commentAction, {
            counter: { $set: commentAction.counter - 1 }
          });
          return update(prev, {
            idea: {
              actions: {
                $splice: [[indexAction, 1, newAction]]
              }
            }
          });
        },
        Person: (prev, { queryVariables }) => {
          if (queryVariables.id !== channel.subject.id) return false;
          const commentAction = filterActions(prev.person.actions, {
            behaviorId: PROCESSES.usermanagement.nodes.discuss.nodeId
          })[0];
          const indexAction = prev.person.actions.indexOf(commentAction);
          const newAction = update(commentAction, {
            counter: { $set: commentAction.counter - 1 }
          });
          return update(prev, {
            person: {
              actions: {
                $splice: [[indexAction, 1, newAction]]
              }
            }
          });
        },
        PersonInfo: (prev, { queryVariables }) => {
          if (queryVariables.id !== channel.subject.id) return false;
          const commentAction = filterActions(prev.person.actions, {
            behaviorId: PROCESSES.usermanagement.nodes.discuss.nodeId
          })[0];
          const indexAction = prev.person.actions.indexOf(commentAction);
          const newAction = update(commentAction, {
            counter: { $set: commentAction.counter - 1 }
          });
          return update(prev, {
            person: {
              actions: {
                $splice: [[indexAction, 1, newAction]]
              }
            }
          });
        }
      }
    });
  };
}