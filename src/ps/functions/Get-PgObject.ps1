function Get-PgObject {
<#
.DESCRIPTION
    Get database-scoped object attributes.

.EXAMPLE
    $wia = @{server=".";dbName="master";schema="dbo";name="sp_WhoIsActive"}
    Get-SqlObject @wia
#>
    [CmdletBinding()]Param(

        [Alias('serverName','serverInstance','host','h')]
        [string]
        $server = '127.0.0.1',

        [Alias('databaseName','dbname','d')]
        [string]
        $database = 'postgres',

	    [Alias('schemaName','namespace')]
        [string]
        $schema = 'public',

        [Alias('objectName','name')]
        [string]
        $object,

        [Alias('user','U')]
        [string]
        $username = $env:USER
    )

    function isnull{
        Param(
            $a,
            $b
        )
        if( [string]::IsNullOrWhiteSpace($a) ){
            $b
        } else {
            $a
        }
    }

# TODO: bind params
    $query = @"
select 
    pg_get_functiondef(p.oid) as definition
   ,n.nspname as namespace
   ,r.rolname as owner
from pg_catalog.pg_proc p
join pg_catalog.pg_roles r on r.oid = p.proowner
join pg_catalog.pg_namespace n on n.oid = p.pronamespace
where p.proname='$object'
  and n.nspname='$schema';
"@

    $query = $query.Split() -join ' '

    $dbObject = Invoke-PgQuery -Query $query -Database $database 

    # $dbObject | ForEach-Object {
    #     [PSCustomObject]@{
    #         definition = $objDef
    #         base_type  = $PSItem.base_type
    #         is_table   = $PSItem.is_table
    #         server     = $PSItem.server
    #         database   = Format-SqlIdentifier $PSItem.database
    #         schema     = Format-SqlIdentifier (isnull $PSItem.schema $schema)
    #         name       = Format-SqlIdentifier (isnull $PSItem.name $object)
    #         id         = $PSItem.id
    #         exists     = $true
    #     }
    # }
    $dbObject
}

Set-Alias -Name pg_get -Value Get-PgObject
