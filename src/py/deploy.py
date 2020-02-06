#!/usr/bin/env python3

import argparse
import json
import logging as log
import pandas
import os
import pwd
from sqlalchemy import text as sqltxt
from sqlalchemy import create_engine
from sqlalchemy_utils.functions import create_database, drop_database

default_host = '127.0.0.1'
default_user = pwd.getpwuid(os.getuid()).pw_name
here_path = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('--host', default=default_host, help='IP address or DNS name of postgres server. Default localhost')
parser.add_argument('--user', default=default_user, help='UserName to connect to the database')
parser.add_argument('--database', '--dbname', '-d', required=True, metavar='database')
parser.add_argument('-SchemaOnly', action='store_true')
parser.add_argument('-AllowClobber', action='store_true')
parser.add_argument('-Verbose', action='store_true')

def invoke_sql_file(file_path, engine):
    # https://stackoverflow.com/a/52284098/4709762
    if os.path.isfile(file_path):
        log.info(f"Deploying {file_path}")
        file = open(file_path)
        escaped_sql = sqltxt(file.read()) # needs autocommit? 🤔
        engine.execute(escaped_sql)

def get_deploy_files(repo_path,database):
    order_file = os.path.join(repo_path,'order.txt')
    # https://stackoverflow.com/a/40788179/4709762
    order = pandas.read_csv(order_file, delimiter=',').to_dict('records')
    return order

def assert_clean(engine, database):
    try:
        drop_database(engine.url)
        log.warning(f"Dropping database {database}")
    except:
        log.info(f"Database {database} does not exist")
    log.info(f"Creating database {database}")
    create_database(engine.url)

if __name__ == '__main__':
    args = parser.parse_args()

    # https://stackoverflow.com/a/15412863/4709762
    if args.Verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")


    repo_path = os.path.expanduser(os.path.join(here_path,args.database))
    tables_path = os.path.join(repo_path,'tables')
    data_path = os.path.join(repo_path,'data')

    with open(os.path.join(repo_path,"DB_VERSION"),'r') as f:
        db_version = f.read()

    db_comment = json.dumps({
        'SchemaVersion': db_version
    })

    db_uri = f"postgres://{args.user}@{args.host}:5432/{args.database}"
    engine = create_engine(db_uri)

    order = get_deploy_files(repo_path,args.database)
    # re-sort based on order declared, not position found
    # https://stackoverflow.com/a/613218/4709762
    order = sorted(order, key=lambda o: o['order'])

    log.info(f"-AllowClobber was specified. Setting clean state for database '{args.database}'")
    if args.AllowClobber == True:
        assert_clean(engine, args.database)

    invoke_sql_file(os.path.join(repo_path,"pre.sql"),engine)

    if args.SchemaOnly == True:
        log.info(f"SchemaOnly option was specified. Skipping seed data files.")

    for rel in order:
        ddl_file = os.path.join(tables_path,f"{rel['name']}.sql")
        dml_file = os.path.join(data_path,f"{rel['name']}.sql")
        invoke_sql_file(ddl_file,engine)
        if args.SchemaOnly == False:
            invoke_sql_file(dml_file,engine)

    invoke_sql_file(os.path.join(repo_path,"post"),engine)

    # https://stackoverflow.com/q/43686895/4709762
    # https://docs.sqlalchemy.org/en/13/core/connections.html#understanding-autocommit
    comment_cmd = sqltxt(f"comment on database {args.database} is '{db_comment}';").execution_options(autocommit=True)

    engine.execute(comment_cmd)

