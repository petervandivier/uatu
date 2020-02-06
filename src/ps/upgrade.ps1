#!/usr/bin/env pwsh

[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    $Database,

    [Parameter(Mandatory=$true)]
    [Alias('To')]
    [int]
    $ToVersion

    # ¿TODO? $ToLatest
)

Push-Location "$PSScriptRoot/$Database"

# https://stackoverflow.com/a/11496486/4709762
$get_db_comment = @"
SELECT pg_catalog.shobj_description(d.oid, 'pg_database') AS "Description"
FROM   pg_catalog.pg_database d
WHERE  datname = '$Database';
"@

$db_comment = psql --dbname=$Database -t -c $get_db_comment | ConvertFrom-Json

[int]$current_version = $db_comment.SchemaVersion

while($current_version -lt $ToVersion){
    $next_version = $current_version + 1

    $migration_file = Resolve-Path -Path "./migrations/$current_version/$next_version.sql" 

    Write-Warning "Bumping database '$Database' version from '$current_version' to '$next_version'."
    psql --dbname=$Database --file=$migration_file.FullName

    $current_version = $next_version
}

Set-Content -Path "./DB_VERSION" -Value $current_version -Force

$DB_COMMENT = @{
    SchemaVersion = $current_version
} | ConvertTo-Json -Compress

psql --dbname=$database -c "comment on database $database is '$DB_COMMENT';"

Pop-Location
