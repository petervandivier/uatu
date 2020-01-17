#!/usr/bin/env python3
# 
# enumerate DDL objects in a database
# 

from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy.engine import reflection

from attrdict import AttrDict
import argparse
import json
import os
import pwd
import re

default_host = '127.0.0.1'
default_user = pwd.getpwuid(os.getuid()).pw_name

uatu_path = os.path.dirname(os.path.realpath(__file__))
conf = json.loads(open(f"{uatu_path}/../../conf/conf.json").read())

# https://stackoverflow.com/a/20532421/4709762
class AliasedAttrDict(AttrDict):
    aliases = {}
    def __getitem__(self, key):
        if key in self.__class__.aliases:
            return super(AliasedAttrDict, self).__getitem__(self.__class__.aliases[key])
        return super(AliasedAttrDict, self).__getitem__(key)
    def __getattr__(self, key):
        if key in self.__class__.aliases:
            return super(AliasedAttrDict, self).__getitem__(self.__class__.aliases[key])
        return super(AliasedAttrDict, self).__getitem__(key)

class ReltypeDict(AliasedAttrDict):
    aliases = {
        "table": "r",
        "view": "v",
        "materialized view": "m",
        "index": "i",
        "sequence": "S",
        "special": "s",
        "foreign table": "f",
        "partitioned table": "p",
        "partitioned index": "I"
    }

reltype_dict = ReltypeDict({
    'r': {'subdir': 'tables'},
    'v': {'subdir': 'views'},
    'm': {'subdir': 'views'},
    'i': {'subdir': 'special'},
    'S': {'subdir': 'special'},
    's': {'subdir': 'special'},
    'f': {'subdir': 'tables'},
    'p': {'subdir': 'tables'},
    'I': {'subdir': 'tables'}
})

parser = argparse.ArgumentParser()
parser.add_argument('--host',     default=default_host, help='IP address or DNS name of postgres server. Default localhost')
parser.add_argument('--user',     default=default_user, help='UserName to connect to the database')
parser.add_argument('--project',  default=conf['default_project'])

def get_uatu_path(project, obj_type, schema, relname):
    if project is None: 
        project = conf['default_project']
    # https://stackoverflow.com/a/2057072/4709762
    project_path = os.path.expanduser(conf['projects'][project]['path'])
    schema_dir = schema 
    # only nest objects in a subdirectory for non-standard schemas
    # most everything is in "public" atm
    if schema_dir == 'public':
        schema_dir = ''
    subdir = reltype_dict[obj_type]['subdir']
    return_val = {
        'dir_full_path': os.path.join(project_path, schema_dir, subdir),
        'file_full_path': os.path.join(project_path, schema_dir, subdir, relname + ".sql")
    }
    return return_val

def format_create_index_command(idx, tbl):
    cols = []
    if 'column_sorting' in idx:
        for c in idx['column_names']:
            col = c
            if col in idx['column_sorting']:
                sorts = []
                for s in idx['column_sorting'][col]:
                    if str(s).startswith('null'):
                        sorts.append(str(s).replace('nulls', 'nulls ').upper())
                    else:
                        sorts.append(s.upper())
                col = col + " " + ' '.join(sorts)
            cols.append(col)
    else:
        cols = idx['column_names']
    cols = ','.join(cols)
    create_idx_text = f"CREATE INDEX {idx['name']} ON {tbl} ({cols});"
    return create_idx_text

def get_create_table_command(table_name, engine):
    metadata = MetaData()
    # TODO: handle for non-"public" schema
    bind_schema = None
    metadata.reflect(bind=engine,schema=bind_schema)
    # https://stackoverflow.com/a/5605077/4709762
    insp = reflection.Inspector.from_engine(engine)
    indexes = []
    for idx in insp.get_indexes(table_name):
        if 'duplicates_constraint' not in idx:
            create_idx_text = format_create_index_command(idx, table_name)
            indexes.append(create_idx_text)
    # unfound object foo returns "KeyError: 'foo'" here
    create_table_text = str(CreateTable(metadata.tables[table_name])) + ";\n"
    create_table_text = remove_sequence(create_table_text)
    create_table_text = create_table_text + "\n".join(indexes) + "\n"
    return create_table_text

def remove_sequence(create_table_text):
    # https://chat.stackexchange.com/transcript/message/53260939#53260939
    p = r"((?:INTEGER|INT) DEFAULT nextval\('[^']*?'\:\:regclass\) NOT NULL)"
    for seq in re.findall(p, create_table_text):
        create_table_text = create_table_text.replace(seq, "SERIAL")
    return create_table_text

def do_dump(args):
    db_name = conf['projects'][args.project]['db_name']

    db_uri = f"postgres://{args.user}@{args.host}:5432/{db_name}"
    # TODO: errorcheck connection
    engine = create_engine(db_uri)

    metadata = MetaData()

    # TODO: handle for non-"public" schema
    # enumerate schemas with inspector - see: https://stackoverflow.com/a/22690122/4709762
    bind_schema = None

    metadata.reflect(bind=engine,schema=bind_schema)
    # key_name = f"{args.schema}.{args.object}"

    ddl = metadata.tables

    for obj in ddl:
        # TODO: handle for dots in object identifiers
        # key name does not contain schema for objects in public schema
        if '.' in obj:
            schema = obj.split('.')[0]
            name = obj.split('.')[1]
            key_name = obj
        else:
            schema = ''
            name = obj
            key_name = obj

        cmd_txt = get_create_table_command(key_name, engine)

        repo = get_uatu_path(args.project, 'table', schema, name)

        os.makedirs(repo['dir_full_path'],exist_ok=True)
        f = open(repo['file_full_path'],'w+')

        f.write(str(cmd_txt))
        f.close()

if __name__ == '__main__':
    args = parser.parse_args()

    do_dump(args)

