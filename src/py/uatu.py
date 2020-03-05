#!/usr/bin/env python3
# 
# enumerate DDL objects in a database
# 

from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
from sqlalchemy.engine import reflection
from sqlalchemy.dialects import postgresql

import argparse
import json
import os
import pwd
import re

default_host = '127.0.0.1'
default_user = pwd.getpwuid(os.getuid()).pw_name

uatu_path = os.path.dirname(os.path.realpath(__file__))
conf_path = os.path.expanduser("~/.uatu")
conf = json.loads(open(f"{conf_path}/conf.json").read())

parser = argparse.ArgumentParser()
parser.add_argument('--host',     default=default_host, help='IP address or DNS name of the postgres instance. Default localhost')
parser.add_argument('--port',     default=5432,         help='Port of the postgres instance. Default 5432')
parser.add_argument('--user',     default=default_user, help='UserName to connect to the database')
parser.add_argument('--password', default='')
# TODO: default='foo' needed here for error-free entry into interactive session
#   how to make that not suck? 🤔
parser.add_argument('--project',  default='foo')
# TODO: one-off manual config support
# parser.add_argument('--config')

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
    subdir = "tables"
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
    if_uq = ''
    if idx['unique']:
        if_uq = 'UNIQUE '
    create_idx_text = f"CREATE {if_uq}INDEX {idx['name']} ON {tbl} ({cols});"
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
    tbl = metadata.tables[table_name]
    create_table_text = str(CreateTable(tbl).compile(dialect=postgresql.dialect())) + ";\n"
    create_table_text = remove_sequence(create_table_text)
    create_table_text = create_table_text + "\n".join(indexes) + "\n"
    return create_table_text

def remove_sequence(create_table_text):
    # replace sequence construct with SERIAL or BIGSERIAL as needed
    # sequence object not bound to table is know sqlalchemy limitation
    # https://docs.sqlalchemy.org/en/13/core/reflection.html#limitations-of-reflection
    # see also: https://chat.stackexchange.com/transcript/message/53260939
    p = r"((?:INTEGER|INT) DEFAULT nextval\('[^']*?'\:\:regclass\) NOT NULL)"
    for seq in re.findall(p, create_table_text):
        create_table_text = create_table_text.replace(seq, "SERIAL")
    return create_table_text

def do_dump(
    project,
    user,
    password,
    host,
    port
):
    db_name = conf['projects'][project]['db_name']

    db_uri = f"postgres://{user}:{password}@{host}:{port}/{db_name}"
    # TODO: errorcheck connection
    engine = create_engine(db_uri)

    metadata = MetaData()

    # TODO: handle for non-"public" schema
    # enumerate schemas with inspector - see: https://stackoverflow.com/a/22690122/4709762
    bind_schema = None

    metadata.reflect(bind=engine,schema=bind_schema)
    # key_name = f"{schema}.{object}"

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

    # TODO: if args.config is not None and args.project is not conf['default_project']: sys.exit ("you may only specify one of ...")

    do_dump(
        args.project,
        args.user,
        args.password,
        args.host,
        args.port
    )

