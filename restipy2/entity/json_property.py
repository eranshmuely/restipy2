class json_property(object):

    def __init__(self, json_name=None, json_type=None):
        """
        represents a property (key value pair) in a JSON document
        :param json_name: the property name, if None, we will use the python property name
        :param json_type: the type, if None, we will use whatever the json package gives us
        """
        self.json_name = json_name
        self.json_value = None
        self.json_type = json_type

    def to_json(self):
        return {self.json_name: self.json_value}

    def __repr__(self):
        return str(self.json_value)

    def __str__(self):
        return repr(self)

    def __int__(self):
        return int(self.json_value)
