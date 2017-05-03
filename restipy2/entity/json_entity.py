import json
from collections import Mapping
from json_property import json_property


class json_entity(Mapping):

    def __init__(self):
        super(json_entity, self).__init__()

    @classmethod
    def from_json(cls, json_data):

        if isinstance(json_data, basestring):
            json_data = json.loads(json_data)

        def deserialize_one(json_data):
            instance = cls()
            for key, value in instance.__dict__.iteritems():
                if isinstance(value, json_property):
                    try:
                        if value.json_type is not None:
                            if issubclass(value.json_type, json_entity):
                                setattr(instance, key, value.json_type.from_json(json_data.get(value.json_name)))
                            elif issubclass(value.json_type, basestring):
                                setattr(instance, key, str(json_data.get(value.json_name)))
                            elif issubclass(value.json_type, int):
                                setattr(instance, key, int(float(json_data.get(value.json_name))))
                            elif issubclass(value.json_type, long):
                                setattr(instance, key, long(float(json_data.get(value.json_name))))
                            elif issubclass(value.json_type, float):
                                setattr(instance, key, float(json_data.get(value.json_name)))
                            continue
                        setattr(instance, key, json_data.get(value.json_name))
                    except:
                        setattr(instance, key, None)
            return instance

        return deserialize_one(json_data) if isinstance(json_data, dict) else \
            [deserialize_one(obj) for obj in json_data]

    @classmethod
    def from_string(cls, json_string):
        return cls.from_json(json.loads(json_string))

    def __getattribute__(self, item):
        if item == '__class__':
            return {}.__class__
        attr = object.__getattribute__(self, item)
        return attr.json_value if isinstance(attr, json_property) else attr

    def __setattr__(self, key, value):
        item = self.__dict__.get(key)
        if isinstance(item, json_property):
            item.json_value = value
        else:
            if isinstance(value, json_property) and value.json_name is None:
                value.json_name = key
            object.__setattr__(self, key, value)

    @property
    def json_properties(self):
        return {p.json_name: p.json_value for p in self.__dict__.itervalues() if isinstance(p, json_property)}

    def to_json(self):
        json_value = {}
        for key, value in self.json_properties.iteritems():
            if isinstance(value, json_entity):
                json_value.update({key: value.to_json()})
            else:
                json_value.update({key: value})

        return json_value

    def __repr__(self):
        return json.dumps(self.to_json(), sort_keys=True, indent=4)

    def __str__(self):
        return repr(self)

    def __len__(self):
        return len(self.json_properties.keys())

    def __iter__(self):
        return self.json_properties.__iter__()

    def __getitem__(self, item):
        return self.json_properties.get(item)
