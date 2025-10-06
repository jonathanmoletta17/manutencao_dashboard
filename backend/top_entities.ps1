Param(
  [string]$EnvFile = "../../.env.local",
  [int]$EntitiesId = 1,
  [string]$TargetEntityName,
  [int]$TopN = 10
)

$ErrorActionPreference = 'Stop'
try { Add-Type -AssemblyName System.Web } catch { }

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
  try { return Invoke-RestMethod -Method Post -Uri $uri -Headers $Headers -Body $body -TimeoutSec 30 }
  catch { Write-Warning "changeActiveEntities failed: $($_.Exception.Message)"; return $null }
}

# Helpers de busca (compatíveis com abordagem dos utilitários)
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
function Get-SearchOptions([hashtable]$Headers, [string]$itemtype) {
  $uri = Join-Url $Env:GLPI_BASE_URL ("searchOptions/" + $itemtype)
  try { return Invoke-RestMethod -Method Get -Uri $uri -Headers $Headers -TimeoutSec 30 } catch { Write-Warning "searchOptions ${itemtype} failed: $($_.Exception.Message)"; return $null }
}
function Find-FieldIdByName([hashtable]$Headers, [string]$itemtype, [string[]]$candidates) {
  $opts = Get-SearchOptions -Headers $Headers -itemtype $itemtype
  if (-not $opts) { return $null }
  foreach ($cand in $candidates) {
    $lcand = ("$cand").ToLower()
    foreach ($opt in $opts) {
      $field = if ($opt.PSObject.Properties['field']) { ("$($opt.field)").ToLower() } else { $null }
      $linkfield = if ($opt.PSObject.Properties['linkfield']) { ("$($opt.linkfield)").ToLower() } else { $null }
      if ($field -eq $lcand -or $linkfield -eq $lcand) { return [string]$opt.id }
    }
  }
  return $null
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

# Impressão simples de tabela
function Print-CountsTable([object[]]$items, [int]$nameWidth = 60) {
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
if ($session) {
  $activeId = $EntitiesId
  if ($TargetEntityName) {
    # Mudar temporariamente para root (0) para buscar qualquer entidade
    Change-ActiveEntities -Headers $headers -entitiesId 0 -isRecursive $true | Out-Null
    $entityForcedFind = @('Entity.id','Entity.completename')
    $allEntities = Search-Paginated -itemtype 'Entity' -Headers $headers -criteria @() -forcedisplay $entityForcedFind -step 800
    $match = $null
    $target = ($TargetEntityName).Trim()
    foreach ($e in $allEntities) {
      $cnRaw = [string]$e.'Entity.completename'
      $cn = (Sanitize-Label($cnRaw)).Trim()
      if ($cn -and (
        $cn.Equals($target, [System.StringComparison]::OrdinalIgnoreCase) -or
        $cn.StartsWith($target, [System.StringComparison]::OrdinalIgnoreCase)
      )) { $match = $e; break }
    }
    if ($match) { $activeId = [int]$match.'Entity.id' }
    else { Write-Warning "Target entity name not found: $TargetEntityName. Using EntitiesId $EntitiesId." }
  }
  Change-ActiveEntities -Headers $headers -entitiesId $activeId -isRecursive $true | Out-Null
}

# Top por entidades em duas etapas: contar por ID e mapear nome
$eidFid = Find-FieldIdByName -Headers $headers -itemtype 'Ticket' -candidates @('entities_id','Ticket.entities_id')
if (-not $eidFid) { $eidFid = '80' }
$ticketsForced = @('Ticket.id', $eidFid)
$ticketRows = Search-Paginated -itemtype 'Ticket' -Headers $headers -criteria @() -forcedisplay $ticketsForced -step 300 -extraParams @{ display_type = 2 }

$idCounts = @{}
foreach ($row in $ticketRows) {
  $eid = [string]$row.$eidFid
  if (-not $eid) { $eid = 0 }
  if ($idCounts.ContainsKey($eid)) { $idCounts[$eid]++ } else { $idCounts[$eid] = 1 }
}

# Buscar nomes das entidades
$entityForced = @('Entity.id','Entity.completename','Entity.name')
$entityRows = Search-Paginated -itemtype 'Entity' -Headers $headers -criteria @() -forcedisplay $entityForced -step 300
$nameById = @{}
foreach ($er in $entityRows) {
  $oid = [string]$er.'Entity.id'
  $comp = $er.'Entity.completename'
  $nm = $er.'Entity.name'
  $label = $null
  if ($comp) { $label = Sanitize-Label([string]$comp) }
  elseif ($nm) { $label = Sanitize-Label([string]$nm) }
  else { $label = [string]$oid }
  if ($oid -ne $null -and -not $nameById.ContainsKey($oid)) { $nameById[$oid] = $label }
}

$sorted = $idCounts.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First $TopN
$items = $sorted | ForEach-Object {
  $key = [string]$_.Key
  $nm = if ($nameById.ContainsKey($key)) { $nameById[$key] } else { if ($key -eq '0') { '(sem entidade)' } else { $key } }
  [pscustomobject]@{ Name = $nm; Value = $_.Value }
}
Print-CountsTable -items $items -nameWidth 60