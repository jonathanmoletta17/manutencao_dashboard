Param(
  [string]$EnvFile = "../../.env.local",
  [int]$EntitiesId = 1,
  [int]$TopN = 16
)

$ErrorActionPreference = 'Stop'
try { Add-Type -AssemblyName System.Web } catch { }

function Resolve-PathSafe($path) { if ([System.IO.Path]::IsPathRooted($path)) { return $path } return (Join-Path $PSScriptRoot $path) }
function Load-EnvFile($path) {
  $resolved = Resolve-PathSafe $path
  if (-not (Test-Path -Path $resolved)) { throw "Env file not found: $resolved" }
  Get-Content -Path $resolved | ForEach-Object {
    if ($_ -match '^(?<k>[^=]+)=(?<v>.*)$') { [Environment]::SetEnvironmentVariable($Matches['k'].Trim(), $Matches['v']) }
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
  $body = @{ entities_id = $entitiesId; is_recursive = $isRecursive } | ConvertTo-Json
  try { return Invoke-RestMethod -Method Post -Uri $uri -Headers $Headers -Body $body -TimeoutSec 30 } catch { Write-Warning "changeActiveEntities failed: $($_.Exception.Message)"; return $null }
}

function Build-SearchParams($criteria, $forcedisplay, [int]$start, [int]$end, $extraParams) {
  $params = @{}
  $params['range'] = "${start}-${end}"
  if (-not $params.ContainsKey('is_deleted')) { $params['is_deleted'] = '0' }
  if (-not $params.ContainsKey('is_recursive')) { $params['is_recursive'] = '1' }
  if (-not $params.ContainsKey('expand_dropdowns')) { $params['expand_dropdowns'] = '1' }
  if ($extraParams) { foreach ($k in $extraParams.Keys) { $params[$k] = $extraParams[$k] } }
  if ($criteria) {
    for ($i=0; $i -lt $criteria.Count; $i++) { $c = $criteria[$i]; foreach ($k in $c.Keys) { $params["criteria[${i}][${k}]"] = $c[$k] } }
  }
  if ($forcedisplay) { for ($i=0; $i -lt $forcedisplay.Count; $i++) { $params["forcedisplay[${i}]"] = $forcedisplay[$i] } }
  return $params
}
function Build-SearchUri([string]$itemtype, [hashtable]$params) {
  $path = Join-Url $Env:GLPI_BASE_URL ("search/" + $itemtype)
  $queryParts = New-Object System.Collections.Generic.List[string]
  foreach ($kv in $params.GetEnumerator()) { $queryParts.Add("$($kv.Key)=$($kv.Value)") }
  $query = [string]::Join('&', $queryParts)
  return "${path}?${query}"
}
function Invoke-Search([string]$itemtype, [hashtable]$Headers, [hashtable]$params) {
  $uri = Build-SearchUri -itemtype $itemtype -params $params
  try { return Invoke-RestMethod -Method Get -Uri $uri -Headers $Headers -TimeoutSec 60 } catch { Write-Warning "Search ${itemtype} failed: $($_.Exception.Message)"; return $null }
}
function Get-Item([string]$itemtype, [hashtable]$Headers, [int]$id) {
  if ($id -le 0) { return $null }
  $uri = Join-Url $Env:GLPI_BASE_URL ("${itemtype}/" + $id)
  try { return Invoke-RestMethod -Method Get -Uri $uri -Headers $Headers -TimeoutSec 30 } catch { Write-Warning "Get ${itemtype} ${id} failed: $($_.Exception.Message)"; return $null }
}
function Search-Paginated([string]$itemtype, [hashtable]$Headers, $criteria, $forcedisplay, [int]$step, $extraParams=$null) {
  $all = @(); $start = 0; $total = $null
  while ($true) {
    $end = $start + $step - 1
    $params = Build-SearchParams $criteria $forcedisplay $start $end $extraParams
    $resp = Invoke-Search -itemtype $itemtype -Headers $Headers -params $params
    if (-not $resp -or -not $resp.data) { break }
    $all += $resp.data
    if ($null -eq $total -and $resp.totalcount) { $total = [int]$resp.totalcount }
    $received = $resp.data.Count
    if ($received -le 0) { break }
    $start += $received
    if ($total -and $start -ge $total) { break }
  }
  return $all
}

function Decode-HTML([string]$s) {
  if (-not $s) { return $s }
  $t = $s
  for ($i=0; $i -lt 2; $i++) {
    try { $t = [System.Web.HttpUtility]::HtmlDecode($t) } catch { $t = [System.Net.WebUtility]::HtmlDecode($t) }
  }
  return $t
}
function Sanitize-Label([string]$s) {
  $t = Decode-HTML($s)
  if ($t) {
    $t = $t -replace '&amp;#62;', '>' -replace '&#62;', '>' -replace '&gt;', '>' -replace '&amp;gt;', '>' -replace '&#39;', "'" -replace '&amp;', '&'
  }
  return $t
}

function Print-CountsTable([object[]]$items, [int]$nameWidth = 60) {
  $nw = [Math]::Min([Math]::Max($nameWidth, 20), 80)
  $header = ("{0} | {1}" -f ("Nome".PadRight($nw)), "Qtde")
  Write-Host $header -ForegroundColor Gray
  Write-Host ("{0}-+-{1}" -f ('-'.PadRight($nw,'-')), ('-'.PadRight(5,'-'))) -ForegroundColor Gray
  foreach ($it in $items) {
    $name = [string]$it.Name
    if (-not $name) { $name = 'sem' }
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

# Contar por técnico (users_id_assign) usando fieldId numérico e mapear nomes
$assignFieldId = '5' # Fallback conhecido: Ticket.users_id_assign
$forced = @('Ticket.id', $assignFieldId)
$rows = Search-Paginated -itemtype 'Ticket' -Headers $headers -criteria @() -forcedisplay $forced -step 300 -extraParams @{ display_type = 0 }

$idCounts = @{}
$nameCounts = @{}
foreach ($row in $rows) {
  $val = $row.$assignFieldId
  if ($null -eq $val) { $name = 'sem'; $nameCounts[$name] = ($nameCounts[$name] + 1) }
  elseif ($val -is [System.Array]) {
    foreach ($v in $val) {
      $s = [string]$v
      if ([string]::IsNullOrWhiteSpace($s)) { continue }
      if ($s -match '^[0-9][0-9,;\s]*$') {
        foreach ($uid in ($s -split '[,;\s]+')) { if ($uid) { $idCounts[$uid] = ($idCounts[$uid] + 1) } }
      } else {
        $nameCounts[$s] = ($nameCounts[$s] + 1)
      }
    }
  } else {
    $s = [string]$val
    if ([string]::IsNullOrWhiteSpace($s)) { $name = 'sem'; $nameCounts[$name] = ($nameCounts[$name] + 1) }
    elseif ($s -match '^[0-9][0-9,;\s]*$') {
      foreach ($uid in ($s -split '[,;\s]+')) { if ($uid) { $idCounts[$uid] = ($idCounts[$uid] + 1) } }
    } else {
      $nameCounts[$s] = ($nameCounts[$s] + 1)
    }
  }
}

$nameById = @{}
foreach ($key in $idCounts.Keys) {
  if ($key -eq '0') { continue }
  $uidInt = 0
  [void][int]::TryParse($key, [ref]$uidInt)
  if ($uidInt -le 0) { continue }
  if (-not $nameById.ContainsKey($key)) {
    $u = Get-Item -itemtype 'User' -Headers $headers -id $uidInt
    $label = $null
    if ($u) {
      $comp = $u.completename
      $real = $u.realname
      $first = $u.firstname
      $login = $u.name
      if ($comp) { $label = Sanitize-Label([string]$comp) }
      elseif ($real -or $first) {
        $nm = ([string]$first).Trim()
        if ($real) { $nm = ($nm + ' ' + ([string]$real).Trim()).Trim() }
        $label = Sanitize-Label($nm)
      }
      elseif ($login) { $label = [string]$login }
    }
    if (-not $label) { $label = $key }
    $nameById[$key] = $label
  }
}

## Merge counts: prefer resolved names; map IDs to names as needed
$countsByName = @{}
foreach ($kv in $nameCounts.GetEnumerator()) { $countsByName[$kv.Key] = ($countsByName[$kv.Key] + $kv.Value) }
foreach ($kv in $idCounts.GetEnumerator()) {
  $key = [string]$kv.Key
  $nm = if ($nameById.ContainsKey($key)) { $nameById[$key] } else { if ($key -eq '0') { 'sem' } else { $key } }
  $countsByName[$nm] = ($countsByName[$nm] + $kv.Value)
}

$items = $countsByName.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First $TopN | ForEach-Object { [pscustomobject]@{ Name = $_.Key; Value = $_.Value } }

Write-Host "Top Técnicos (users_id_assign)" -ForegroundColor Yellow
Print-CountsTable -items $items -nameWidth 60