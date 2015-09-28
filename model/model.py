# -*- coding:utf-8 -*-
import ConfigParser
from db.mysql import DbConnect


class Field(object):
    def __init__(self, name, column_type):
        self.name = name
        self.column_type = column_type

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)


class StringField(Field):
    def __init__(self, name):
        super(StringField, self).__init__(name, 'varchar(100)')


class IntegerField(Field):
    def __init__(self, name):
        super(IntegerField, self).__init__(name, 'bigint')


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == "Model":
            return type.__new__(cls, name, bases, attrs)
        mappings = {}
        for k, v in attrs.iteritems():
            if isinstance(v, Field):
                mappings[k] = v
        for k in mappings.iterkeys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings
        return type.__new__(cls, name, bases, attrs)


class Model(dict):
    __metaclass__ = ModelMetaclass
    __table__ = None
    _db = {}

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
        dbconf = self.load_config()
        for conf_name, config in dbconf.iteritems():
            self._db[conf_name] = DbConnect(config, self.__table__)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'", item)

    def __setattr__(self, key, value):
        self[key] = value

    def save(self):
        params = {}
        for k, v in self.__mappings__.iteritems():
            print k, v
            params[k] = getattr(self, k, None)
        rowid = self._db['localhost'].insert(params)
        return rowid

    def load_config(self):
        dbconf_file = "db.ini"
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.read(dbconf_file)
        sections = conf_parser.sections()
        dbconf = {}
        for section in sections:
            dbconf[section] = {key: val for key, val in conf_parser.items(section)}
        return dbconf
