# -*- coding: utf-8 -*-

"""Settings."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os
import os.path as op

from ..ext.six.moves import cPickle
from .logging import debug, warn


#------------------------------------------------------------------------------
# Utility functions
#------------------------------------------------------------------------------

def _load_python(path):
    path = op.realpath(op.expanduser(path))
    assert op.exists(path)
    with open(path, 'r') as f:
        contents = f.read()
    store = {}
    exec(contents, store, {})
    return store


def _load_pickle(path):
    path = op.realpath(op.expanduser(path))
    assert op.exists(path)
    with open(path, 'rb') as f:
        store = cPickle.load(f)
        assert isinstance(store, dict)
        return store


def _save_pickle(path, store):
    path = op.realpath(op.expanduser(path))
    with open(path, 'wb') as f:
        cPickle.dump(store, f)


#------------------------------------------------------------------------------
# Settings
#------------------------------------------------------------------------------

class BaseSettings(object):
    """Store key-value pairs."""
    def __init__(self):
        self._store = {}
        self._to_save = {}

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        self._store[key] = value
        self._to_save[key] = value

    def load(self, path):
        if not op.exists(path):
            debug("The settings file {} doesn't exist.".format(path))
        # Try pickle.
        if not op.splitext(path)[1]:
            try:
                self._store._update(_load_pickle(path))
            except Exception as e:
                warn("Unable to read the internal settings. "
                     "You may want to delete '{0}'.\n{1}".format(path, str(e)))
                return {}
        # Try Python.
        else:
            try:
                return self._store.update(_load_python(path))
            except Exception as e:
                warn("Unable to read the settings file "
                     "'{0}':\n{1}".format(path, str(e)))
                return {}

    def save(self, path):
        try:
            _save_pickle(path, self._to_save)
        except Exception as e:
            warn("Unable to save the internal settings file "
                 "at '{}':\n{}".format(path, str(e)))
        self._to_save = {}


class Settings(object):
    """Manage default, user-wide, and experiment-wide settings."""

    def __init__(self, phy_user_dir=None, default_path=None):

        # `.phy/` user directory, ~/.phy by default.
        if phy_user_dir is None:
            phy_user_dir = _phy_user_dir()
        self.phy_user_dir = phy_user_dir
        _ensure_dir_exists(self.phy_user_dir)

        self._bs = BaseSettings()

        # Load phy's defaults.
        self._bs.load(default_path)

        # Load the user's internal settings.
        self.internal_settings_path = op.join(self.phy_user_dir,
                                              'internal_settings')
        self._bs.load(self.internal_settings_path)

        # load the user defaults.
        self.user_settings_path = op.join(self.phy_user_dir,
                                          'user_settings.py')
        self._bs.load(self.user_settings_path)

    def on_open(self, path):
        # Get the experiment settings path.
        self.exp_name = op.splitext(op.basename(path))[0]
        self.exp_dir = op.dirname(path)
        self.exp_settings_dir = op.join(self.exp_dir, self.exp_name + '.phy')
        self.exp_settings_path = op.join(self.exp_settings_dir,
                                         'user_settings.py')
        _ensure_dir_exists(self.exp_settings_dir)

        # Load experiment-wide settings.
        self._bs.load(self.exp_settings_path)


#------------------------------------------------------------------------------
# Config
#------------------------------------------------------------------------------

_PHY_USER_DIR_NAME = '.phy'


def _phy_user_dir():
    """Return the absolute path to the phy user directory."""
    home = op.expanduser("~")
    path = op.realpath(op.join(home, _PHY_USER_DIR_NAME))
    return path


def _ensure_dir_exists(path):
    if not op.exists(path):
        os.makedirs(path)
