# Copyright (c) 2014 by Ecreall under licence AGPL terms 
# available on http://www.gnu.org/licenses/agpl.html

# licence: AGPL
# author: Amen Souissi

import pytz
import unittest
from pyramid import testing
try:
    from pyramid_robot.layer import Layer
except ImportError:
    class Layer():
        pass

from substanced.db import root_factory

from dace.subscribers import stop_ioloop

from novaideo import searchable_contents


class BaseFunctionalTests(object):

    def setUp(self):
        import tempfile
        import os.path
        self.tmpdir = tempfile.mkdtemp()
        dbpath = os.path.join(self.tmpdir, 'test.db')
        uri = 'file://' + dbpath + '?blobstorage_dir=' + self.tmpdir
        settings = {'zodbconn.uri': uri,
                    'sms.service': 'pyramid_sms.ovh.OvhService',
                    'substanced.secret': 'sosecret',
                    'substanced.initial_login': 'admin',
                    'substanced.initial_password': 'admin',
                    'novaideo.secret' : 'seekri1',
                    'substanced.uploads_tempdir' : self.tmpdir,
                    'mail.default_sender': 'admin@example.com',
                    'pyramid.includes': [
                        'substanced',
                        'pyramid_chameleon',
                        'pyramid_layout',
                        'pyramid_mailer.testing', # have to be after substanced to override the mailer
                        'pyramid_tm',
                        'dace',
                        'pontus',
                        'daceui'
        ]}

        testing.setUp()
        from novaideo import main
        self.app = app = main({}, **settings)
        self.db = app.registry._zodb_databases['']
        self.request = request = testing.DummyRequest()
        self.request.invalidate_cache = True
        self.config = testing.setUp(registry=app.registry, request=request)
        self.registry = self.config.registry
        from .catalog import (
            NovaideoIndexes, Text,
            Lexicon, Splitter,
            CaseNormalizer, StopWordRemover)
        # lexicon is a persistent object, we need to be sure it's a fresh one
        # between tests
        NovaideoIndexes.relevant_data = Text(
            lexicon=Lexicon(Splitter(), CaseNormalizer(), StopWordRemover()))
        self.root = root_factory(request)
        request.root = self.root

    def tearDown(self):
        stop_ioloop()
        import shutil
        testing.tearDown()
        self.db.close()
        shutil.rmtree(self.tmpdir)


class FunctionalTests(BaseFunctionalTests, unittest.TestCase):

    def setUp(self):
        super(FunctionalTests, self).setUp()

    def default_novaideo_config(self):
        self.request.get_time_zone = pytz.timezone('Europe/Paris')
        self.request.moderate_ideas = False
        self.request.moderate_proposals = False
        self.request.examine_ideas = False
        self.request.examine_proposals = False
        self.request.support_ideas = True
        self.request.support_proposals = True
        self.request.root.content_to_support = ['idea', 'proposal']
        self.request.content_to_examine = []
        self.request.content_to_support = ['idea', 'proposal']
        self.request.accessible_to_anonymous = True
        self.request.content_to_manage = [
            'question', 'idea', 'proposal']
        self.request.root.content_to_manage = [
            'challenge', 'question', 'idea', 'proposal']
        self.request.searchable_contents = searchable_contents(
            self.request)
        self.request.user = self.request.root['principals']['users']['admin']
        self.request.user.email = None

    def moderation_novaideo_config(self):
        self.default_novaideo_config()
        self.request.moderate_ideas = True
        self.request.moderate_proposals = True
        self.request.root.content_to_moderate = ['idea', 'proposal']
    
    def no_support_novaideo_config(self):
        self.default_novaideo_config()
        self.request.support_ideas = False
        self.request.support_proposals = False
        self.request.root.content_to_support = []

    def examination_novaideo_config(self):
        self.default_novaideo_config()
        self.request.examine_ideas = True
        self.request.examine_proposals = True
        self.request.content_to_examine = ['idea', 'proposal']
        self.request.root.content_to_examine = ['idea', 'proposal']
            

class RobotLayer(BaseFunctionalTests, Layer):

    defaultBases = ()

    def setUp(self):
        super(RobotLayer, self).setUp()
        from webtest import http
        self.server = http.StopableWSGIServer.create(self.app, port=8080)

    def tearDown(self):
        super(RobotLayer, self).tearDown()
        self.server.shutdown()


ROBOT_LAYER = RobotLayer()
