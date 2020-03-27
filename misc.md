# Stuff

## And Things

Notes I don't have the spoons to contextualize elsewhere

## PG Data extraction

[Invoke-PgQuery sucks at binary data at the moment](https://github.com/petervandivier/dbutil/issues/1) so I use [psql `\copy`](https://www.postgresql.org/docs/current/app-psql.html) to extract text-safe representation of table data and pipe (I wish...) the csv into `Format-SqlValues` for seed data files.

```powershell
Param(
    $database,
    $csvDir
)

$getTbls = @"
SELECT 
    relname                              as table_name, 
    n_live_tup                           as row_count, 
    pg_size_pretty(pg_table_size(relid)) as size 
FROM pg_stat_user_tables;
"@
$tbls = ipgq -d $database -q $getTbls
$tbls | ? rows -gt 0 | % { echo "\copy $($_.relname) to $csvDir/$($_.relname).csv csv header" | psql -d $database }
gci $csvDir -R | % { 
    # reallllllyyy need to get pipelining working on fmt-sqlvals...
    $data = ipcsv $_ 
    Format-SqlValues -InputObject $data -Expanded -TableName $_.BaseName | Set-Content "$csvDir/../$($_.BaseName).sql"
} 
```
