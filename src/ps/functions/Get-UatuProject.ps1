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
    }

    process{
        if($Project){
            foreach($p in $Project){
                $uatu_Projects.$p
            }
        }else {
            $uatu_Projects
        }
    }
}