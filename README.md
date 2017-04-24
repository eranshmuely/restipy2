# RestiPy2

restipy2 is a python-to-json-to-python serialization rest client (can also be used as a server)

### Basic Usage
All you have to do is subclass ```json_entity``` and add a bunch of ```json_property```s.

```
from restipy2.entity import *

class GeoModel(json_entity):
    def __init__(self):
        self.latitude = json_property("lat", float)
        self.longitude = json_property("lng", float)


class AddressModel(json_entity):
    def __init__(self):
        self.street = json_property()
        self.suite = json_property()
        self.city = json_property()
        self.geo = json_property(json_type=GeoModel)


class UserModel(json_entity):
    def __init__(self):
        self.id = json_property()
        self.name = json_property()
        self.username = json_property()
        self.address = json_property(json_type=AddressModel)
```

Then, you can create an instance of the HTTPAdapter:

```
from restipy2.adapter import HTTPAdapter

client = HTTPAdapter()

```

And start having fun:

```
users = client.get_entity('http://jsonplaceholder.typicode.com/users', UserModel)
print users[0].name, users[0].id
users[0].name = "Eran Shmuely"
users = client.post_entity('http://jsonplaceholder.typicode.com/users', users) # will try to send an HTTP Post, will probably fail since jsonplaceholder does not support that
```

The HTTPAdapter object is really cool by itself:

```
from restipy2.adapter import HTTPAdapter, HTTPProxy

 # it supports proxies, cookies and HTTP redirects:
client = HTTPAdapter(proxy=HTTPProxy("http://some-proxy"), handle_cookies=True, follow_redirects=True)

# can also be used to make JSON requests without restipying
users = client.get_json('http://jsonplaceholder.typicode.com/users') 
client.post_json('http://jsonplaceholder.typicode.com/users', [...])

# gives you access to cookies:
jsessionid = client.get_cookie('jsessionid')
jsessionid.domain = 'some-other-doamin'
client.set_cookie(jsessionid)

# and more cool stuff
```


License
----
MIT