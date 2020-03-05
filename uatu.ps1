#!/usr/bin/env pwsh

$cacheDir = Join-Path "$env:HOME" ".uatu"

if(-not (Test-Path $cacheDir)){
    $cacheDir = (New-Item -ItemType Directory -Path $cacheDir).FullName
    Copy-Item $PSScriptRoot/conf/conf.example.json -Destination $cacheDir/conf.json
}

$configuration = @{
    Name = "uatu_Configuration"
    Value = (Get-Content -Path $cacheDir/conf.json | ConvertFrom-Json)
    Force = $true
    Scope = 'Global'
}
New-Variable @configuration

$projects = @{
    Name = "uatu_Projects"
    Value = $uatu_Configuration.Projects
    Force = $true
    Scope = 'Global'
}
New-Variable @projects

$pySymLink = (New-Item -ItemType SymbolicLink -Path "$cacheDir/uatu.py" -Value "$PSScriptRoot/src/py/uatu.py" -Force).FullName
# if($os -ne 'Windows'){} for below... not sure how to do atm
# ¿TODO?: export symlink to $PATH 🤔
Invoke-Command {chmod 0744 $pySymLink}
