Param(
  [string]$EnvFile = "../../.env.local",
  [int]$EntitiesId = 1
)

$ErrorActionPreference = 'Stop'

function Resolve-PathSafe($path) {
  if ([System.IO.Path]::IsPathRooted($path)) { return $path }
  return (Join-Path $PSScriptRoot $path)
}

function Load-EnvFile($path) {
  $resolved = Resolve-PathSafe $path
  if (-not (Test-Path -Path $resolved)) { throw "Env file not found: $resolved" }
  Get-Content -Path $resolved | ForEach-Object {
    if ($_ -match '^(?<k>[^=]+)=(?<v>.*)$') {
      [Environment]::SetEnvironmentVariable($Matches['k'].Trim(), $Matches['v'])
    }
  }
}

function New-Header() { return @{ 'App-Token'=$Env:GLPI_APP_TOKEN; 'Authorization'="user_token $Env:GLPI_USER_TOKEN"; 'Content-Type'='application/json' } }
function Join-Url([string]$base, [string]$segment) { $b=$base.TrimEnd('/'); $s=$segment.TrimStart('/'); return "$b/$s" }
function Init-GLPISession([hashtable]$Headers) {
  $uri = Join-Url $Env:GLPI_BASE_URL 'initSession'
  try { $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers $Headers -TimeoutSec 30; if ($resp.session_token) { $Headers['Session-Token']=$resp.session_token; return $resp } else { throw "initSession did not return session_token" } }
  catch { Write-Warning "initSession failed: $($_.Exception.Message)"; return $null }
}
function Change-ActiveEntities([hashtable]$Headers, [int]$entitiesId, [bool]$isRecursive) {
  $uri = Join-Url $Env:GLPI_BASE_URL 'changeActiveEntities'
  $body = @{ entities_id=$entitiesId; is_recursive=$isRecursive } | ConvertTo-Json
  try { return Invoke-RestMethod -Method Post -Uri $uri -Headers $Headers -Body $body -TimeoutSec 30 }
  catch { Write-Warning "changeActiveEntities failed: $($_.Exception.Message)"; return $null }
}

# (Sem importações externas: lógica mínima e focada)

function Print-CountsTable([object[]]$items, [int]$nameWidth = 40) {
  $nw = [Math]::Min([Math]::Max($nameWidth, 20), 80)
  $header = ("{0} | {1}" -f ("Nome".PadRight($nw)), "Qtde")
  Write-Host $header -ForegroundColor Gray
  Write-Host ("{0}-+-{1}" -f ('-'.PadRight($nw,'-')), ('-'.PadRight(5,'-'))) -ForegroundColor Gray
  foreach ($it in $items) {
    $name = [string]$it.Name
    if (-not $name) { $name = '(vazio)' }
    if ($name.Length -gt $nw) { $name = $name.Substring(0,$nw-1) + '...' }
    $line = ("{0} | {1}" -f ($name.PadRight($nw)), ([string]$it.Value))
    Write-Host $line
  }
}

# Main
Load-EnvFile -path $EnvFile
$headers = New-Header
$session = Init-GLPISession -Headers $headers
if ($session) { Change-ActiveEntities -Headers $headers -entitiesId $EntitiesId -isRecursive $true | Out-Null }

function Get-TicketsCountByStatus([hashtable]$Headers, [int]$StatusValue) {
  $base = $Env:GLPI_BASE_URL.TrimEnd('/')
  $qs = "criteria[0][field]=12&criteria[0][searchtype]=equals&criteria[0][value]=$StatusValue&forcedisplay[0]=id"
  $uri = "$base/search/Ticket?$qs"
  try {
    $resp = Invoke-RestMethod -Method Get -Uri $uri -Headers $Headers -TimeoutSec 30
    if ($resp.totalcount) { return [int]$resp.totalcount } else { return 0 }
  } catch { return 0 }
}

$novos = Get-TicketsCountByStatus -Headers $headers -StatusValue 1
$naoSol = (Get-TicketsCountByStatus -Headers $headers -StatusValue 2) + (Get-TicketsCountByStatus -Headers $headers -StatusValue 4)
$planej = Get-TicketsCountByStatus -Headers $headers -StatusValue 3
$soluc = Get-TicketsCountByStatus -Headers $headers -StatusValue 5
$fech = Get-TicketsCountByStatus -Headers $headers -StatusValue 6
$resolv = $soluc + $fech

$rows = @(
  [pscustomobject]@{ Name = 'Novos (1)'; Value = $novos },
  [pscustomobject]@{ Name = 'Nao solucionados (2,4)'; Value = $naoSol },
  [pscustomobject]@{ Name = 'Planejados (3)'; Value = $planej },
  [pscustomobject]@{ Name = 'Solucionados (5)'; Value = $soluc },
  [pscustomobject]@{ Name = 'Fechados (6)'; Value = $fech },
  [pscustomobject]@{ Name = 'Resolvidos (5+6)'; Value = $resolv }
)
Print-CountsTable -items $rows -nameWidth 40