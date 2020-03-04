#!/usr/bin/env pwsh

[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    $Database,
    
    [switch]
    $AllowClobber,

    [switch]
    [Alias('schema-only')]
    $SchemaOnly
)

Push-Location "$PSScriptRoot/$database"

$order = Import-Csv './order.txt' | ForEach-Object {                   
    [pscustomobject]@{                                  
        table = $_.name
        order = Invoke-Expression $_.order
        tbl_file_exists = Test-Path "./tables/$($_.name).sql"
        data_file_exists = Test-Path "./data/$($_.name).sql"
    }
}

$db_exists = psql -t -c "select datname from pg_database where datname='$database'"

if(-not $db_exists){
    Write-Verbose "Creating database '$database'"
    createdb $database
}elseif ($AllowClobber) {
    psql $database -c "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$database' and pid <> pg_backend_pid();" 
    dropdb $database
    createdb $database
}

if(Test-Path "./pre.sql"){
    Write-Verbose "Executing pre-deploy script(s)"
    psql --dbname=$database --file "./pre.sql"
}

$order | Sort-Object -Property order | ForEach-Object {
    if($_.tbl_file_exists){
        Write-Verbose "Creating table '$($_.table)'"
        psql --dbname=$database --file "./tables/$($_.table).sql"
    }
}

if($SchemaOnly){
    Write-Verbose "SchemaOnly option was specified. Skipping seed data files."
}else{
    $order | Sort-Object -Property order | ForEach-Object {
        if($_.data_file_exists){
            Write-Verbose "Inserting records for '$($_.table)'"
            psql --dbname=$database --file "./data/$($_.table).sql"
        }
    }
}

if(Test-Path "./post.sql"){
    Write-Verbose "Executing post-deploy script(s)"
    psql --dbname=$database --file "./post.sql"
}

[int]$DB_VERSION = Get-Content -Path "./DB_VERSION"

$DB_COMMENT = @{
    SchemaVersion = $DB_VERSION
} | ConvertTo-Json -Compress

psql --dbname=$database -c "comment on database $database is '$DB_COMMENT';"

Pop-Location
