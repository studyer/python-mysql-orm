# -*- coding:utf-8 -*-
import MySQLdb as mysql
from MySQLdb.cursors import DictCursor

SPLITTER = '__'
operators = {
    'eq': '= %s',
    'gt': '> %s',
}


class Query(object):
    _logic_op = 'AND'

    def __init__(self, tb_name, **queries):
        self._tb_name = tb_name
        self._queries = []
        self._queries = queries.items()

    def parse_queries(self):
        sqls, values = [], []
        if self._queries:
            for query in self._queries:
                # id__gt, 1= (id__gt, 1)
                fd_and_op, value = query
                parts = fd_and_op.split(SPLITTER)
                if parts[-1] in operators:
                    op = parts[-1]
                else:
                    op = 'eq'
                fd = parts[0]
                sql = '`%s`.`%s` %s' % (
                    self._tb_name,
                    fd,
                    operators[op])
                sqls.append(sql)
                values.append(value)
            self._sql = self._logic_op.join(sqls)
            self._param = values
        else:
            self._sql = None
            self._param = ()

    # Query sql
    def _get_sql(self):
        if not hasattr(self, '_sql'):
            self.parse_queries()
        return self._sql

    def _set_sql(self, sql):
        self._sql = sql

    sql = property(_get_sql, _set_sql)

    # Query values
    def _get_param(self):
        if not hasattr(self, 'param'):
            self.parse_queries()
        return self._param

    def _set_param(self, param):
        self._param = param

    param = property(_get_param, _set_param)


class DbConnect(object):
    _config = {}
    _db = None

    def __init__(self, config, table):
        self._config.update(config)
        self._db = mysql.connect(config['host'], config['user'], config['password'], config['dbname'])
        self._db.autocommit(True)
        self._tb_name = table
        self._queries = {}

    # turple cursor storage on client
    @property
    def cursor(self):
        return self._db.cursor()

    # dict cursor storage on client
    @property
    def dict_cursor(self):
        return self._db.cursor(DictCursor)

    @property
    def fields(self):
        sql = "SHOW FULL COLUMNS FROM " + str(self._tb_name)
        cursor = self.dict_cursor
        cursor.execute(sql)
        result = cursor.fetchall()
        columns = []
        for row in result:
            columns.append(row['Field'])
        return columns

    def where(self, **queries):
        self._queries.update(queries)
        return self

    # construct the sql string base on table entry
    def construct_sql(self, option, **args):
        # construct insert
        if option == 'insert':
            fields = args['fields']
            sql = 'INSERT INTO `%s`(%s) VALUES ' % (
                self._tb_name,
                ','.join('`%s`' % field for field in fields))
            param = args['values']
            formats = []
            for value in param:
                formats.append('%s')
            sql = sql + '(' + ','.join(formats) + ')'
            return sql, param

        # construct like 'WHERE field1=1 AND filed=2'
        query = Query(self._tb_name, **self._queries)
        where = query.sql and ('WHERE ' + query.sql) or ''
        param = query.param
        # construct select
        if option == 'select':
            get_what = 'SELECT ' + self.get_select(args.get('get_what', '*'))
            sql = ' '.join((get_what, 'FROM', self._tb_name, where))
        # construct update
        elif option == 'update':
            formats = []
            values = []
            for field, value in args.items():
                formats.append(' `%s` = %%s' % (field,))
                values.append(value)
            values.extend(param)
            param = values
            upd_what = 'UPDATE %s SET %s' % (
                self._tb_name,
                ','.join(formats))
            sql = ' '.join((upd_what, where))
        # construct delete
        elif option == 'delete':
            del_what = 'DELETE FROM %s' % self._tb_name
            sql = ' '.join((del_what, where))

        return sql, param

    def get_select(self, get_what=None):
        if get_what is None or get_what == '*':
            field_list = self.fields
            get_what = ','.join('`%s`.`%s`' % (self._tb_name, field)
                                for field in field_list)
        return get_what

    # get_what is a string of selected field
    def select(self, get_what=None):
        sql, param = self.construct_sql('select', get_what=get_what)
        if sql is None:
            return ()
        # get DataBase cursor
        cursor = self.dict_cursor
        cursor.execute(sql, param)
        results = cursor.fetchall()
        return results

    def insert(self, record):
        sql, param = self.construct_sql('insert',
                                        fields=record.keys(),
                                        values=record.values())
        cursor = self.dict_cursor
        cursor.execute(sql, param)
        return cursor.lastrowid

    def update(self, **data):
        sql, param = self.construct_sql('update', **data)
        cursor = self._db.dict_cursor
        return cursor.execute(sql, param)

    def delete(self):
        sql, param = self.construct_sql('delete')
        cursor = self._db.dict_cursor
        return cursor.execute(sql, param)
