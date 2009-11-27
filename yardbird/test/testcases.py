import unittest

from django.conf import settings
from django.test.testcases import TestCase as DjangoTestCase

from django.core.urlresolvers import clear_url_caches
from django.utils.encoding import smart_str

from yardbird.test.client import Client

class YardbirdTestCase(DjangoTestCase):
    def _urlconf_setup(self):
        if hasattr(self, 'msgconf'):
            self._old_root_msgconf = settings.ROOT_MSGCONF
            settings.ROOT_MSGCONF = self.msgconf
            clear_url_caches()
    def _urlconf_teardown(self):
        if hasattr(self, '_old_root_msgconf'):
            settings.ROOT_MSGCONF = self._old_root_msgconf
            clear_url_caches()
    def __call__(self, result=None):
        self.client = Client()
        try:
            self._pre_setup()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            import sys
            result.addError(self, sys.exc_info())
            return
        # skip the django __call__ entirely, going straight to the one
        # in the python stdlib
        unittest.TestCase.__call__(self, result)
        try:
            self._post_teardown()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            import sys
            result.addError(self, sys.exc_info())
            return
    def assertRedirects(self, *args, **kwargs):
        raise NotImplementedError, "You're thinking of HTTP"
    def assertFormError(self, *args, **kwargs):
        raise NotImplementedError, "You're thinking of HTTP"

    def assertContains(self, response, text, count=None, method='NOTICE'):
        """
        Asserts that a response indicates that a response was generated
        successfully, (i.e., the reply method was as expected), and that
        ``text`` occurs ``count`` times in the content of the response.
        If ``count`` is None, the count doesn't matter - the assertion
        is true if the text occurs at least once in the response.
        """
        self.assertEqual(response.method, method,
            "Couldn't retrieve page: Response method was %s (expected %s)'" %
                (response.method, method))
        text = smart_str(text, response._charset)
        real_count = response.content.count(text)
        if count is not None:
            self.assertEqual(real_count, count,
                "Found %d instances of '%s' in response (expected %d)" %
                    (real_count, text, count))
        else:
            self.failUnless(real_count != 0,
                            "Couldn't find '%s' in response" % text)

    def assertNotContains(self, response, text, method='NOTICE'):
        """
        Asserts that a response indicates that a response was generated
        successfully, (i.e., the reply method was as expected), and that
        ``text`` doesn't occur in the content of the response.
        """
        self.assertEqual(response.method, method,
            "Couldn't retrieve page: Response method was %s (expected %s)'" %
                (response.method, method))
        text = smart_str(text, response._charset)
        self.assertEqual(response.content.count(text),
             0, "Response should not contain '%s'" % text)
