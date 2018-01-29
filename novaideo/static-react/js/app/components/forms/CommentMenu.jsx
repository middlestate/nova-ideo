/* eslint-disable react/no-array-index-key, no-confusing-arrow */
import React from 'react';
import classNames from 'classnames';
import AddIcon from 'material-ui-icons/Add';
import IconButton from 'material-ui/IconButton';
import { withStyles } from 'material-ui/styles';

import Menu from '../common/Menu';

const styles = (theme) => {
  return {
    menu: {
      flex: 1,
      display: 'flex',
      position: 'absolute',
      alignItems: 'center',
      height: '100%',
      zIndex: 1,
      borderBottomLeftRadius: 3,
      borderTopLeftRadius: 3,
      marginLeft: -1,
      '&:hover': {
        backgroundColor: theme.palette.tertiary.color,
        border: 'solid 1px',
        borderColor: theme.palette.tertiary.color,
        '& .menu-button': {
          color: theme.palette.tertiary.hover.color
        }
      }
    },
    menuOpen: {
      backgroundColor: theme.palette.tertiary.color,
      border: 'solid 1px',
      borderColor: theme.palette.tertiary.color
    },
    buttonOpen: {
      color: theme.palette.tertiary.hover.color
    }
  };
};

class CommentMenu extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      menu: false
    };
  }

  onMenuOpen = () => {
    this.setState({ menu: true });
  };

  onMenuClose = () => {
    this.setState({ menu: false });
  };

  render() {
    const { fields, classes } = this.props;
    const { menu } = this.state;
    const menuId = 'comment-menu-list';
    return (
      <Menu
        id={menuId}
        onOpen={this.onMenuOpen}
        onClose={this.onMenuClose}
        fields={fields}
        classes={{
          menu: classes.menu,
          menuOpen: classes.menuOpen
        }}
      >
        <IconButton
          className={classNames('menu-button', {
            [classes.buttonOpen]: menu
          })}
          aria-owns={menuId}
          aria-haspopup="true"
        >
          <AddIcon />
        </IconButton>
      </Menu>
    );
  }
}

export default withStyles(styles, { withTheme: true })(CommentMenu);