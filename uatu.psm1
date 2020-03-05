#!/usr/bin/env pwsh

Push-Location $PSScriptRoot

Get-ChildItem -Path ./src/ps/functions | ForEach-Object {
    . $PSItem.FullName 
}

. ./uatu.ps1

Pop-Location
