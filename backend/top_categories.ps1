Param(
  [string]$EnvFile = "../../.env.local",
  [int]$EntitiesId = 1,
  [int]$TopN = 10
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

# Top por categorias: contar por ID e mapear nome
$catFieldId = '7' # fallback conhecido para Ticket.itilcategories_id
$ticketsForced = @('Ticket.id', $catFieldId)
$ticketRows = Search-Paginated -itemtype 'Ticket' -Headers $headers -criteria @() -forcedisplay $ticketsForced -step 300 -extraParams @{ display_type = 2 }

$idCounts = @{}
foreach ($row in $ticketRows) {
  $cid = [string]$row.$catFieldId
  if (-not $cid) { $cid = '0' }
  if ($idCounts.ContainsKey($cid)) { $idCounts[$cid]++ } else { $idCounts[$cid] = 1 }
}

$catForced = @('ITILCategory.id','ITILCategory.completename','ITILCategory.name')
$catRows = Search-Paginated -itemtype 'ITILCategory' -Headers $headers -criteria @() -forcedisplay $catForced -step 300
$nameById = @{}
foreach ($cr in $catRows) {
  $oid = [string]$cr.'ITILCategory.id'
  $comp = $cr.'ITILCategory.completename'
  $nm = $cr.'ITILCategory.name'
  $label = $null
  if ($comp) { $label = Sanitize-Label([string]$comp) }
  elseif ($nm) { $label = Sanitize-Label([string]$nm) }
  else { $label = [string]$oid }
  if ($oid -ne $null -and -not $nameById.ContainsKey($oid)) { $nameById[$oid] = $label }
}

$allItems = $idCounts.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
  $key = [string]$_.Key
  $nm = if ($nameById.ContainsKey($key)) { $nameById[$key] } else { if ($key -eq '0') { 'sem' } else { $key } }
  [pscustomobject]@{ Name = $nm; Value = $_.Value }
}

function Classify-MacroArea([string]$label) {
  if (-not $label) { return 'Outros' }
  $first = ($label -split '>', 2)[0].Trim()
  # Remove diacritics to avoid console/encoding mismatches
  function Remove-Diacritics([string]$s) {
    if (-not $s) { return $s }
    $n = $s.Normalize([Text.NormalizationForm]::FormD)
    $sb = New-Object System.Text.StringBuilder
    foreach ($ch in $n.ToCharArray()) {
      if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch) -ne [Globalization.UnicodeCategory]::NonSpacingMark) { [void]$sb.Append($ch) }
    }
    return $sb.ToString().Normalize([Text.NormalizationForm]::FormC)
  }
  $plain = (Remove-Diacritics $first).ToLowerInvariant()
  if ($plain -like 'manutencao*') { return 'Manutenção' }
  if ($plain -like 'conservacao*') { return 'Conservação' }
  return 'Outros'
}

$manItems = @(); $consItems = @(); $otherItems = @()
foreach ($it in $allItems) {
  $grp = Classify-MacroArea $it.Name
  if ($grp -eq 'Manutenção') { $manItems += $it }
  elseif ($grp -eq 'Conservação') { $consItems += $it }
  else { $otherItems += $it }
}

function Sum-Total($arr) { $t = 0; foreach ($x in $arr) { $t += [int]$x.Value }; return $t }
$manTotal = Sum-Total $manItems
$consTotal = Sum-Total $consItems
$otherTotal = Sum-Total $otherItems

Write-Host ("Top Categorias - Manutenção (Total: {0})" -f $manTotal) -ForegroundColor Yellow
Print-CountsTable -items ($manItems | Sort-Object -Property Value -Descending | Select-Object -First $TopN) -nameWidth 60

Write-Host ("Top Categorias - Conservação (Total: {0})" -f $consTotal) -ForegroundColor Yellow
Print-CountsTable -items ($consItems | Sort-Object -Property Value -Descending | Select-Object -First $TopN) -nameWidth 60

Write-Host ("Top Categorias - Outros (Total: {0})" -f $otherTotal) -ForegroundColor Yellow
Print-CountsTable -items ($otherItems | Sort-Object -Property Value -Descending | Select-Object -First $TopN) -nameWidth 60