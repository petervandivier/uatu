function Get-UatuProject {
<#
.DESCRIPTION
    List currently available Uatu projects in memory
#>
    [CmdletBinding()]
    param (
        [Parameter(Position=0,ValueFromPipeline=$true)]
        [string[]]
        $Project
    )

    begin{
        if(-not $uatu_Projects){
            $uatu_Projects = (Get-Content "$env:HOME/.uatu/conf.json" | ConvertFrom-Json).Projects
        }

        if(-not $Project){
            $Project = $uatu_Projects.PSObject.Properties.Name
        }
    }

    process{
        foreach($p in $Project){
            [PSCustomObject]@{
                ProjectName  = $p
                DatabaseName = $uatu_Projects.$p.db_name
                ProjectPath  = $uatu_Projects.$p.path
            }
        }
    }
}