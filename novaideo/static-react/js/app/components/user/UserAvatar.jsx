/* eslint-disable no-underscore-dangle */
import React from 'react';
import { withStyles } from '@material-ui/core/styles';
import Avatar from '@material-ui/core/Avatar';
import Icon from '@material-ui/core/Icon';
import classNames from 'classnames';

import { initalsGenerator } from '../../utils/globalFunctions';

const styles = (theme) => {
  return {
    avatar: {
      borderRadius: 4,
      background: 'white'
    },
    anonymousAvatar: {
      color: theme.palette.tertiary.hover.color,
      backgroundColor: theme.palette.tertiary.color,
      fontWeight: 900
    },
    noPicture: {
      color: theme.palette.tertiary.hover.color,
      backgroundColor: theme.palette.primary['500'],
      fontSize: 16
    }
  };
};

export const DumbUserAvatar = ({ classes, picture, isAnonymous, title, strictUrl, anonymousIcon = 'guy-fawkes-mask' }) => {
  let content = null;
  if (isAnonymous) {
    content = <Icon className={`mdi-set mdi-${anonymousIcon}`} />;
  } else if (title && !picture) {
    content = initalsGenerator(title);
  }
  const urlAddon = !strictUrl ? '/profil' : '';
  return (
    <Avatar
      className={classNames({
        [classes.anonymousAvatar]: isAnonymous,
        [classes.noPicture]: !isAnonymous && !picture
      })}
      classes={{ root: classes.avatar }}
      src={picture ? `${picture.url}${urlAddon}` : ''}
    >
      {content}
    </Avatar>
  );
};

export default withStyles(styles)(DumbUserAvatar);