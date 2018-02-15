import update from 'immutability-helper';
import { gql } from 'react-apollo';

import { ideaFragment } from '../../queries';

export const createAndPublishMutation = gql`
  mutation($text: String!, $title: String!, $keywords: [String]!, $attachedFiles: [Upload], $anonymous: Boolean) {
    createAndPublish(
      title: $title
      keywords: $keywords
      text: $text
      attachedFiles: $attachedFiles,
      anonymous: $anonymous
    ) {
      status
      idea {
        ...idea
      }
    }
  }
  ${ideaFragment}
`;

export default function createAndPublish({ ownProps, mutate }) {
  return ({ text, title, keywords, attachedFiles, anonymous, account }) => {
    const { formData, globalProps: { site } } = ownProps;
    const files =
      attachedFiles.length > 0
        ? formData.values.files.map((file) => {
          return {
            url: file.preview.url,
            isImage: file.preview.type === 'image',
            variations: [],
            __typename: 'File'
          };
        })
        : [];
    const createdAt = new Date();
    let authorId = account.id;
    let authorOid = account.oid;
    let authorTitle = account.title;
    if (anonymous) {
      if (account.mask) {
        authorId = account.mask.id;
        authorOid = account.mask.oid;
        authorTitle = account.mask.title;
      } else {
        authorId = 'anonymousId';
        authorOid = 'anonymousOid';
        authorTitle = 'Anonymous';
      }
    }
    return mutate({
      variables: {
        text: text,
        title: title,
        keywords: keywords,
        attachedFiles: attachedFiles,
        anonymous: anonymous
      },
      optimisticResponse: {
        __typename: 'Mutation',
        createAndPublish: {
          __typename: 'CreateAndPublish',
          status: true,
          idea: {
            __typename: 'Idea',
            id: '0',
            oid: '0',
            createdAt: createdAt.toISOString(),
            title: title,
            keywords: keywords,
            text: text,
            presentationText: text,
            attachedFiles: files,
            tokensSupport: 0,
            tokensOpposition: 0,
            userToken: null,
            state: site.supportIdeas ? ['submitted_support', 'published'] : ['published'],
            channel: {
              __typename: 'Channel',
              id: 'channel-id',
              oid: 'channel-oid',
              title: title,
              isDiscuss: false
            },
            opinion: '',
            urls: [],
            author: {
              __typename: 'Person',
              isAnonymous: anonymous,
              id: `${authorId}createidea`,
              oid: `${authorOid}createidea`,
              title: authorTitle,
              description: account.description,
              function: account.function,
              picture:
                !anonymous && account.picture
                  ? {
                    __typename: 'File',
                    url: account.picture.url
                  }
                  : null
            },
            actions: []
          }
        }
      },
      updateQueries: {
        IdeasList: (prev, { mutationResult }) => {
          const newIdea = mutationResult.data.createAndPublish.idea;
          // if the idea is submitted to moderation
          if (newIdea.state.includes('submitted')) return prev;
          return update(prev, {
            ideas: {
              edges: {
                $unshift: [
                  {
                    __typename: 'Idea',
                    node: newIdea
                  }
                ]
              }
            }
          });
        },
        MyContents: (prev, { mutationResult }) => {
          const newIdea = mutationResult.data.createAndPublish.idea;
          const totalCount = prev.account.contents.totalCount + 1;
          return update(prev, {
            account: {
              contents: {
                totalCount: { $set: totalCount },
                edges: {
                  $unshift: [
                    {
                      __typename: 'Idea',
                      node: newIdea
                    }
                  ]
                }
              }
            }
          });
        }
      }
    });
  };
}