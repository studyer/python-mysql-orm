from model import Model
from model import StringField
from model import IntegerField

__author__ = 'studyer'


class Writer(Model):
    __table__ = 'Writers'
    id = IntegerField('Id')
    name = StringField('Name')

    def find_by_id(self, id):
        result = self._db['localhost'].where(id=id).select()
        self.__dict__.update(result[0])
        return self
