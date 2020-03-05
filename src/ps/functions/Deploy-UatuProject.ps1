#!/usr/bin/env pwsh

function Deploy-UatuProject {
<#
.DESCRIPTION
    Given a valid project config, execute deployment against the database
#>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]
        $ProjectName,

        [string]
        $Database,
        
        [switch]
        $AllowClobber,

        [switch]
        [Alias('schema-only')]
        $SchemaOnly
    )

    if(-not $uatu_Projects){
        $uatu_Projects = (Get-Content "$env:HOME/.uatu/conf.json" | ConvertFrom-Json).Projects
    }

    $Project = $uatu_Projects.$ProjectName

    Push-Location $Project.Path

    $order = Import-Csv './order.csv' | ForEach-Object {                   
        [pscustomobject]@{                                  
            table = $_.name
            order = Invoke-Expression $_.order
            tbl_file_exists = Test-Path "./tables/$($_.name).sql"
            data_file_exists = Test-Path "./data/$($_.name).sql"
        }
    }

    if(-not $Database){
        $Database = $Project.db_name
    }

    $db_exists = (Invoke-PgQuery -Query "select True as Exists from pg_database where datname='$Database'").Exists

    if(-not $db_exists){
        Write-Verbose "Creating database '$Database'"
        createdb $Database
    }elseif ($AllowClobber) {
        Invoke-PgQuery -Query "select pg_terminate_backend(pid) from pg_stat_activity where datname = '$Database' and pid <> pg_backend_pid();" 
        dropdb $Database
        createdb $Database
    }

    if(Test-Path "./pre.sql"){
        Write-Verbose "Executing pre-deploy script(s)"
        psql --dbname=$Database --file "./pre.sql"
    }

    $order | Sort-Object -Property order | ForEach-Object {
        if($_.tbl_file_exists){
            Write-Verbose "Creating table '$($_.table)'"
            psql --dbname=$Database --file "./tables/$($_.table).sql"
        }
    }

    if($SchemaOnly){
        Write-Verbose "SchemaOnly option was specified. Skipping seed data files."
    }else{
        $order | Sort-Object -Property order | ForEach-Object {
            if($_.data_file_exists){
                Write-Verbose "Inserting records for '$($_.table)'"
                psql --dbname=$Database --file "./data/$($_.table).sql"
            }
        }
    }

    if(Test-Path "./post.sql"){
        Write-Verbose "Executing post-deploy script(s)"
        psql --dbname=$Database --file "./post.sql"
    }

    [int]$DB_VERSION = Get-Content -Path "./DB_VERSION"

    $DB_COMMENT = @{
        SchemaVersion = $DB_VERSION
    } | ConvertTo-Json -Compress

    Invoke-PgQuery -Query "comment on database $Database is '$DB_COMMENT';"

    Pop-Location
}
