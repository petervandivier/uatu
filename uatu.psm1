Push-Location $PSScriptRoot

Get-ChildItem -Path ./src/ps/functions | ForEach-Object {
    . $PSItem.FullName 
}

Pop-Location
