
import sys

try:
    import salt.client
except ImportError:
    pass
HAS_SALT = 'salt.client' in sys.modules

try:
    import pepper.libpepper
except ImportError:
    pass
HAS_PEPPER = 'salt.pepper' in sys.modules


class SaltLocalClientPepperWrap(object):
    '''
    Emulates a salt.client.LocalClient object as far as we expect by wrapping a provided
    libpepper.Pepper client instance.
    '''

    def __init__(self, pepper_instance):
        '''
        Init

        :param pepper_instance: Pepper client instance
        :type pepper_instance: pepper.libpepper.Pepper
        '''
        self.p = pepper_instance

    def cmd(self, tgt, fun, arg=(), kwarg=None, expr_form='glob',
            timeout=None, ret=None):
        '''
        Perform Salt command on Node.

        :param fun: Salt function
        :type fun: str
        :param arg: Args for function
        :type arg: list
        :param kwarg: Kwargs for function
        :type kwarg: dict
        :return: Results
        '''
        ret = self.p.local(self.node.name, fun, arg=arg, kwarg=kwarg)
        return ret


def get_saltcli(api_url=None, username=None, password=None, eauth='pam',
                debug_http=False, ignore_ssl_errors=False):
    if api_url:
        assert HAS_PEPPER
        pepper = pepper.libpepper.Pepper(api_url=api_url, debug_http=debug_http,
                                         ignore_ssl_errors=ignore_ssl_errors)

        ret = pepper.login(username, password, eauth)
        assert ret['return']

        saltcli = SaltLocalClientPepperWrap(pepper)
    else:
        assert HAS_SALT
        saltcli = salt.client.LocalClient()
    return saltcli

