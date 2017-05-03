import urllib2
import urllib
import json
import cookielib
import ssl
from base64 import urlsafe_b64encode
from restipy2.entity import json_entity


class JSONResponse(urllib.addbase):
    def __init__(self, response):
        urllib.addbase.__init__(self, response.fp)
        self.headers = response.headers
        self.url = response.url
        self.code = response.code
        try:
            self.json = json.load(response.fp)
        except:
            self.json = response.fp.read()

    def info(self):
        return self.headers

    def getcode(self):
        return self.code

    def geturl(self):
        return self.url

    def read(self):
        """:rtype: dict"""
        return self.json

    def get(self, key, default=None):
        return self.read().get(key, default)

    def __str__(self):
        return json.dumps(self.json, sort_keys=True, indent=4, separators=(',', ': '))


class HTTPAuthorization(object):
    def __init__(self, authentication_type, authentication_value):
        self._authentication_type = authentication_type
        self._authentication_value = authentication_value

    def __repr__(self):
        return '{} {}'.format(self._authentication_type, self._authentication_value)

    def __str__(self):
        return repr(self)


class BasicHTTPAuthorization(HTTPAuthorization):
    def __init__(self, username, password):
        value = urlsafe_b64encode('{}:{}'.format(username, password))
        super(self.__class__, self).__init__('Basic', value)


class BearerHTTPAuthorization(HTTPAuthorization):
    def __init__(self, bearer):
        super(self.__class__, self).__init__('Bearer', bearer)


class ContentType(set):
    JSON = 'application/json'
    URLEncoded = 'application/x-www-form-urlencoded'


class HTTPProxy(urllib2.ProxyHandler):
    def __init__(self, proxy_host, username=None, password=None):
        urllib2.ProxyHandler.__init__(self, {'http': proxy_host, 'https': proxy_host})
        self.proxy_auth_handler = None  # type: urllib2.ProxyBasicAuthHandler
        if username and password:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, proxy_host, username, password)
            self.proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)

    @property
    def handlers(self):
        handlers = [self]
        if self.proxy_auth_handler: handlers.append(self.proxy_auth_handler)
        return handlers


class HTTPRequest(urllib2.Request):
    @property
    def method(self):
        return self.get_method()

    @method.setter
    def method(self, method):
        self.get_method = lambda: method

    @property
    def proxy(self):
        return self._proxy

    @property
    def cookie_jar(self):
        return self._cookie_jar

    @cookie_jar.setter
    def cookie_jar(self, cookie_jar):
        self._cookie_jar = cookie_jar

    @proxy.setter
    def proxy(self, proxy):
        self._proxy = proxy

    def __init__(self, url, data=None, headers={}, method='GET', content_type=ContentType.JSON, authorization=None,
                 proxy=None, cookie_jar=None, follow_redirects=False):
        urllib2.Request.__init__(self, url, data, headers)
        if authorization: self.add_header('Authorization', str(authorization))
        self.add_header('Content-Type', content_type)
        self.get_method = lambda: method
        self._proxy = proxy
        self._cookie_jar = cookie_jar
        self._follow_redirects = follow_redirects

    def send(self, ssl_verify=True):
        try:
            handlers = []
            if not ssl_verify:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                handlers.append(urllib2.HTTPSHandler(context=ctx))
            if self.proxy: handlers += self.proxy.handlers
            if self.cookie_jar is not None: handlers.append(urllib2.HTTPCookieProcessor(self.cookie_jar))
            if not self._follow_redirects:
                class NoRedirectHandler(urllib2.HTTPRedirectHandler):
                    def http_error_302(self, req, fp, code, msg, headers):
                        infourl = urllib.addinfourl(fp,headers,req.get_full_url(),code)
                        infourl.status = code
                        return infourl
                handlers.append(NoRedirectHandler())
            return urllib2.build_opener(*handlers).open(self)
        except urllib2.HTTPError as e:
            return e
        except urllib2.URLError as e:
            print '[HTTPAdapter] URLError: {0}'.format(e)
            raise e
        except Exception as e:
            print '[HTTPAdapter] Exception: {0}'.format(e)
            raise e


class HTTPAdapter(object):

    @property
    def authorization(self):
        return self._authorization

    @authorization.setter
    def authorization(self, authorization):
        self._authorization = authorization

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, proxy):
        self._proxy = proxy

    def __init__(self, proxy=None, authorization=None, handle_cookies=False, follow_redirects=True, ssl_verify=True):
        self._authorization = authorization
        self._proxy = proxy
        self.cookie_jar = cookielib.CookieJar() if handle_cookies else None
        self._follow_redirects = follow_redirects
        self.ssl_verify = ssl_verify

    def __repr__(self):
        return 'HTTPAdapter(proxy={}, authorization={}, handle_cookies={}, follow_redirects={}, ssl_verify={})' \
                .format(self.proxy is not None, self.authorization, self.cookie_jar is not None,
                        self.follow_redirects, self.ssl_verify)

    @property
    def cookies(self):
        """:rtype: list of cookielib.Cookie"""
        if self.cookie_jar:
            return self.cookie_jar
        else:
            return None

    @property
    def follow_redirects(self): return self._follow_redirects

    @follow_redirects.setter
    def follow_redirects(self, f): self._follow_redirects = f

    def get_cookie(self, name, default=None):
        if self.cookie_jar:
            for cookie in self.cookies:
                if cookie.name == name:
                    return cookie
        return default

    def set_cookie(self, cookie):
        self.cookie_jar.set_cookie(cookie)

    @staticmethod
    def encode(data, content_type):
        if not data:
            return None
        elif content_type == ContentType.JSON and not isinstance(data, basestring):
            return json.dumps(data, ensure_ascii=False, encoding='utf8').encode('utf8')
        elif content_type == ContentType.URLEncoded:
            return urllib.urlencode(data)

    @classmethod
    def build_request(cls, url, data=None, headers={}, method='GET', content_type=ContentType.JSON, authorization=None,
                      proxy=None, cookie_jar=None, follow_redirects=None):
        encoded_data = cls.encode(data, content_type)
        return HTTPRequest(url, encoded_data, headers, method, content_type, authorization, proxy, cookie_jar,
                           follow_redirects)

    def send_request(self, url, data=None, headers={}, method='GET', content_type=ContentType.JSON, authorization=None,
                     proxy=None, cookie_jar=None, follow_redirects=None):
        return self.build_request(url, data, headers, method, content_type, authorization or self._authorization,
                                  proxy or self._proxy, cookie_jar or self.cookie_jar,
                                  follow_redirects if follow_redirects is not None else self.follow_redirects).send(self.ssl_verify)

    def request_json(self, url, data=None, headers={}, method='GET', content_type=ContentType.JSON, authorization=None,
                     proxy=None, cookie_jar=None, follow_redirects=None):
        headers.update({'Accept': ContentType.JSON})
        if isinstance(data, json_entity):
            data = json_entity.to_json()
        res = JSONResponse(
            self.send_request(url, data, headers, method, content_type, authorization, proxy, cookie_jar,
                              follow_redirects))
        res.read = lambda: res.json  # hack, can't override read method otherwise
        return res

    def get(self, url, headers={}, authorization=None, proxy=None, cookie_jar=None, follow_redirects=None):
        return self.send_request(url, headers=headers, authorization=authorization, proxy=proxy, cookie_jar=cookie_jar,
                                 follow_redirects=follow_redirects)

    def post(self, url, data, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
             cookie_jar=None, follow_redirects=True):
        return self.send_request(url, data, headers, 'POST', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def put(self, url, data, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
            cookie_jar=None, follow_redirects=None):
        return self.send_request(url, data, headers, 'PUT', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def head(self, url, data=None, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
             cookie_jar=None, follow_redirects=None):
        return self.send_request(url, data, headers, 'HEAD', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def delete(self, url, headers={}, authorization=None, proxy=None, cookie_jar=None, follow_redirects=None):
        return self.send_request(url, headers=headers, method='DELETE', authorization=authorization, proxy=proxy,
                                 cookie_jar=cookie_jar, follow_redirects=follow_redirects)

    def trace(self, url, data=None, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
              cookie_jar=None, follow_redirects=None):
        return self.send_request(url, data, headers, 'TRACE', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def patch(self, url, data, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
              cookie_jar=None, follow_redirects=None):
        return self.send_request(url, data, headers, 'PATCH', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def get_json(self, url, headers={}, authorization=None, proxy=None, cookie_jar=None, follow_redirects=None):
        return self.request_json(url, headers=headers, authorization=authorization, proxy=proxy, cookie_jar=cookie_jar,
                                 follow_redirects=follow_redirects)

    def post_json(self, url, data, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
                  cookie_jar=None, follow_redirects=None):
        return self.request_json(url, data, headers, 'POST', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def put_json(self, url, data, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
                 cookie_jar=None, follow_redirects=None):
        return self.request_json(url, data, headers, 'PUT', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def patch_json(self, url, data, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
                   cookie_jar=None, follow_redirects=None):
        return self.request_json(url, data, headers, 'PATCH', content_type, authorization, proxy, cookie_jar,
                                 follow_redirects)

    def delete_json(self, url, headers={}, authorization=None, proxy=None, cookie_jar=None, follow_redirects=None):
        return self.request_json(url, headers=headers, method='DELETE', authorization=authorization, proxy=proxy,
                                 cookie_jar=cookie_jar, follow_redirects=follow_redirects)

    @staticmethod
    def __return_entity(res, entity):
        if res.code > 400:
            raise Exception(res)
        return entity.from_json(res.json) if isinstance(entity, json_entity.__class__) else res.json

    def get_entity(self, url, entity=None, headers={}, authorization=None, proxy=None, cookie_jar=None, follow_redirects=None):
        res = self.request_json(url, headers=headers, authorization=authorization, proxy=proxy, cookie_jar=cookie_jar,
                                 follow_redirects=follow_redirects)
        return self.__class__.__return_entity(res, entity)

    def post_entity(self, url, data, entity=None, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
                  cookie_jar=None, follow_redirects=None):
        if hasattr(data, 'to_json'): data = data.to_json()
        res = self.request_json(url, data, headers, 'POST', content_type, authorization, proxy, cookie_jar, follow_redirects)
        return self.__class__.__return_entity(res, entity)

    def put_entity(self, url, data, entity=None, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
                 cookie_jar=None, follow_redirects=None):
        if hasattr(data, 'to_json'): data = data.to_json()
        res = self.request_json(url, data, headers, 'PUT', content_type, authorization, proxy, cookie_jar, follow_redirects)
        return self.__class__.__return_entity(res, entity)

    def patch_entity(self, url, data, entity=None, headers={}, content_type=ContentType.JSON, authorization=None, proxy=None,
                   cookie_jar=None, follow_redirects=None):
        if hasattr(data, 'to_json'): data = data.to_json()
        res = self.request_json(url, data, headers, 'PATCH', content_type, authorization, proxy, cookie_jar, follow_redirects)
        return self.__class__.__return_entity(res, entity)

    def delete_entity(self, url, entity=None, headers={}, authorization=None, proxy=None, cookie_jar=None, follow_redirects=None):
        res = self.request_json(url, data, headers, 'DELETE', content_type, authorization, proxy, cookie_jar, follow_redirects)
        return self.__class__.__return_entity(res, entity)
