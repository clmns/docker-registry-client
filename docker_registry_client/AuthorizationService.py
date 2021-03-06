try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit
import requests
import logging

logger = logging.getLogger(__name__)


class AuthorizationService(object):
    """This class implements a Authorization Service for Docker registry v2.

    Specification can be found here :
    https://github.com/docker/distribution/blob/master/docs/spec/auth/token.md

    The idea is to delegate authentication to a third party and use a token to authenticate to
    the registry. Token has to be renew each time we change "scope"

    """
    def __init__(self, registry, url="", auth=None, verify=False):
        # Registry ip:port
        self.registry = urlsplit(registry).netloc
        # Service url, ip:port
        self.url = url
        # Authentication (user, password) or None. Used by request to do basicauth
        self.auth = auth

        # Desired scope is the scope needed for the next operation on the registry
        self.desired_scope = ""
        # Scope of the token we have
        self.scope = ""
        # Token used to authenticate
        self.token = ""
        # Boolean to enfore https checks. Used by request
        self.verify = verify

        # If we have no url then token are not required. get_new_token will not be called
        if url:
            split = urlsplit(url)
            # user in url will take precedence over giver username
            if split.username and split.password:
                self.auth = (split.username, split.password)

            self.token_required = True
        else:
            self.token_required = False

    def get_new_token(self):
        rsp = requests.get("{0}/token?service={1}&scope={2}".format(self.url, self.registry, self.desired_scope),
                           auth=self.auth, verify=self.verify)
        if not rsp.ok:
            logger.error("Can't get token for authentication")
            self.token = ""

        self.token = rsp.json()['token']
        # We managed to get a new token, update the current scope to the one we wanted
        self.scope = self.desired_scope
