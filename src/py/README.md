# UATU - PostgreSQL + Python

Snek reads postgres database table and writes to directory.

# Usage

## Reflect

Assuming you've got the [sqlalchemy][2] & [attrdict][3] projects installed, you can execute...

```python
chmod +x uatu
./uatu.py 
```

...which will read the `default_project` from [/conf/conf.json](/conf/conf.json) and write the tables in the `public` schema to the repo. 

In our case, the `default_project` is `uatu_demo`, which corresponds to a database of the same name on my localhost. 

You can specify other `--projects` listed in your conf file. The database name need not be the same as the project name. 

## Deploy

[deploy.py][6] additionally requires the [pandas][4] and [SQLAlchemy-Utils][5] projects

[2]: https://www.sqlalchemy.org/
[3]: https://pypi.org/project/attrdict/
[4]: https://pypi.org/project/pandas/
[5]: https://pypi.org/project/SQLAlchemy-Utils/
[6]: https://github.com/petervandivier/db-code/blob/master/deploy.py
