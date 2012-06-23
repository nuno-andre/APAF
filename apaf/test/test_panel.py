from functools import partial, wraps

import txtorcon
from twisted.trial import unittest
from twisted.internet import reactor
from twisted.web import client
from twisted.internet import tcp
from cyclone.escape import json_decode, json_encode

from apaf.panel import panel
from apaf.core import add_service
from apaf import config

def page(path, raises=False, **settings):
    """
    Decorator helper for unittest.
    Uses asyncronous callbacks from twisted to get the page referred with path,
    and then tests it with the given path.
    """
    url =  'http://127.0.0.1:%d%s' % (6660, path)

    def inner(func):
        @wraps(func)
        def wrap(self):
            d = client.getPage(url, **settings)
            if raises:
                d.addErrback(partial(func, self))
            else:
                d.addCallback(partial(func, self))
            return d
        return wrap
    return inner


class TestPanel(unittest.TestCase):
    def setUp(self):
        """
        Set up an asyncronous get trasport.
        """
        torconfig = txtorcon.TorConfig()
        self.prot = add_service(torconfig, panel.PanelService(), 6660)
        self.addCleanup(self.prot.loseConnection)

class TestServices(TestPanel):
    @page('/services/')
    def test_get_services(self, response):
        self.assertTrue(response)
        response = json_decode(response)
        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 1)

    @page('/services/panel')
    def test_get_service_panel(self, response):
        self.assertTrue(response)
        response = json_decode(response)
        self.assertTrue(isinstance(response, dict))
        self.assertTrue(all(x in response for x in
                        ['name', 'url','desc']))


class TestConfig(TestPanel):
    @page('/config')
    def test_get_config(self, response):
        self.assertTrue(response)
        response = json_decode(response)
        self.assertEqual(dict(config.custom), response)

    @page('/config', method='PUT',
          headers={'settings': json_encode(dict(base_port=6666))})
    def test_put_config(self, response):
        self.assertTrue(response)
        self.assertEqual(json_decode(response), {'result':True})

class TestAuth(TestPanel):
    @page('/auth/login')
    def test_login(self, response):
        pass
    test_login.skip = 'not implemented'

    @page('/auth/logout')
    def test_logout(self, response):
        pass
    test_logout.skip = 'not implemented'

class TestMiscellanous(TestPanel):

    @page('/foo/bar', raises=True)
    def test_notfound(self, error):
        self.assertEqual(error.value.status, '404')


if __name__ == '__main__':
    from unittest import main
    main()