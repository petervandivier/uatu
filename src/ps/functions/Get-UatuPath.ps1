#!/usr/bin/env pwsh

function Get-UatuPath {
<#
.DESCRIPTION
    Returns directory & file paths with a given Uatu project 
    for a potential database object

.EXAMPLE
    Get-UatuPath -ProjectName 'foo' -Name 'bar' | fl

.TODO
    Support pipelining

.TODO
    Add support for a project class object in a different 
    parameterset than ProjectName
#>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]
        $ProjectName,

        [Parameter()]
        [ValidateNotNullOrEmpty()]
        [Alias('Type')]
        [string]
        $ObjectType = 'table',

        [Parameter(Mandatory=$true)]
        [Alias('Name')]
        [string]
        $ObjectName,

        [Parameter()]
        [ValidateNotNullOrEmpty()]
        [Alias('Schema')]
        [string]
        $SchemaName = 'public'
    )

    if(-not $uatu_Projects){
        $uatu_Projects = (Get-Content "$env:HOME/.uatu/conf.json" | ConvertFrom-Json).Projects
    }

    $Project = $uatu_Projects.$ProjectName
    $ProjectRoot = $Project.Path

    # TODO: support other platforms
    # TODO: pending schema class
    # ([uatu.schema]$Schema).IsDefault($Project.Platform)
    $SchemaPath = switch($SchemaName){
        'public' {''}
        default {$SchemaName}
    }

    $TypePath = switch($ObjectType){
        'table' {'tables'}
    }

    $DirectoryFullPath = Join-Path $ProjectRoot $TypePath $SchemaPath 
    $FileFullPath      = Join-Path $DirectoryFullPath "$ObjectName.sql"

    [PSCustomObject]@{
        Directory = @{
            FullPath = $DirectoryFullPath
            Exists   = Test-Path $DirectoryFullPath
        }
        File = @{
            FullPath = $FileFullPath
            Exists   = Test-Path $FileFullPath
            BaseName = $ObjectName
        }
    }
}
