# Generates D1 reload SQL from Access TCC_NEW.accdb. rank=id PROVEN (Supabase style id = Access-ID-ascending position).
$ErrorActionPreference = 'Stop'
$out = 'C:\APEX Platform\apex-power-ops-platform\infra\database\migrations\tcc\_d1_loader'
$cn = New-Object -ComObject ADODB.Connection
$cn.Mode = 1
$cn.Open('Provider=Microsoft.ACE.OLEDB.16.0;Data Source=D:\TCC_NEW.accdb')

function sq($v){ if($null -eq $v -or $v -eq [DBNull]::Value){ return 'NULL' }; return "'" + (([string]$v) -replace "'","''") + "'" }
function num($v){ if($null -eq $v -or $v -eq [DBNull]::Value -or "$v" -eq ''){ return 'NULL' }; return ([string]$v) }

$classes = @{ 'mccb'='MCCB'; 'iccb'='ICCB'; 'pcb'='PCB' }

# ---- parents (_stg_d1_parents) ----
$pf = New-Object System.Text.StringBuilder
foreach ($c in $classes.Keys) {
  $t = 'Breaker' + $classes[$c]
  $rs = $cn.Execute("SELECT ID, Mfr_ID, Type, cStandard, Acdc FROM $t")
  while (-not $rs.EOF) {
    [void]$pf.AppendLine("INSERT INTO tcc._stg_d1_parents(class,src_id,mfr_id,type,standard,acdc) VALUES ('$c'," + (num $rs.Fields.Item(0).Value) + "," + (num $rs.Fields.Item(1).Value) + "," + (sq $rs.Fields.Item(2).Value) + "," + (num $rs.Fields.Item(3).Value) + "," + (num $rs.Fields.Item(4).Value) + ");")
    $rs.MoveNext()
  }
}
[System.IO.File]::WriteAllText("$out\d1_02_parents.sql", $pf.ToString(), [System.Text.UTF8Encoding]::new($false))

# ---- per-class: src_id (source_id, ordered by rank=id), triples, sst assign, orphan ----
# live orphan STYLE-id set for MCCB (tcc.brk_mccb_styles with dead breaker_id) — 325 rows, from Supabase
$orphanIds = @(4211,4212,4213,4214,4215,4216,4217,4218,4219,4220,4221,4222,4223,4224,4225,4226,4227,4228,4229,4230,4231,4232,4233,4234,4235,4236,4237,4238,4239,4240,4329,4370,4371,4372,4373,4374,4375,4376,4377,4378,4379,4380,4381,4382,4383,4384,4385,4386,4387,4388,4389,4390,4391,4392,4393,4394,4395,4396,4397,4398,4527,4528,4570,4612,4613,4614,4615,4664,4984,5182,5183,5184,5291,5318,5319,5320,5431,5507,5508,5618,5619,5620,5621,5622,6196,6197,6198,6199,6201,6202,6361,6362,6363,6369,6384,6385,6386,6387,6388,6389,6390,6413,6414,6415,6416,6417,6418,6419,6420,6421,6422,6423,6424,6425,6426,6427,6428,6429,6430,6431,6432,6433,6434,6435,6436,6437,6438,6439,6440,6441,6442,6443,6444,6445,6446,6447,6448,6449,6450,6451,6452,6453,6454,6455,6456,6457,6765,6766,6767,6768,6769,6770,6771,6772,6773,6774,6775,6776,6777,6778,6779,7037,7165,7166,7215,7239,7240,7241,7242,7519,7570,7654,7655,7656,7806,7807,7808,7809,7810,7811,7812,7813,7814,7815,7881,8035,8036,8037,8300,8354,8356,8380,8625,8626,8633,8634,8635,8645,8646,8647,8648,8649,8650,8651,8652,8653,8654,8655,8656,8657,8658,8659,8660,8661,8662,8663,8664,8665,8666,8667,8668,8669,8670,8671,8672,8673,8674,8675,8676,8677,8678,8679,8680,8681,8682,8683,8684,8685,8686,8687,8688,8689,8690,8691,8692,8700,8701,8702,8703,8792,8793,8794,8795,8796,8797,8798,8799,8800,8801,8802,8803,8804,8805,8806,8913,8914,8915,9066,9067,9068,9069,9090,9326,9448,9523,9524,9525,9526,9527,9528,9529,9530,9531,9532,9533,9534,9535,9536,9537,9538,9539,9540,9541,9542,9543,9544,9545,9546,9547,9548,9549,9644,9645,9664,9665,9666,9667,9669,9670,9671,9696,9697,9803,9804,9805,9814,9815,9816,9819,9820,9821,9825,9826,9827,9926)
$orphanSet = @{}; foreach($o in $orphanIds){ $orphanSet[[int]$o] = $true }

$summary = @()
foreach ($c in $classes.Keys) {
  $st = 'Breaker' + $classes[$c] + 'Styles'
  # read all style rows ordered by ID  => rank = position (1-based) = tcc.id
  $rs = $cn.Execute("SELECT ID, BreakerID, Style, TMT_Use_SST, TMT_SST_Mfr, TMT_SST_Type, TMT_SST_Style FROM $st ORDER BY ID")
  $srcIds = New-Object System.Collections.ArrayList
  $tripleMap = @{}     # key -> triple_id
  $tripleRows = New-Object System.Collections.ArrayList
  $sstStyleIds = New-Object System.Collections.ArrayList
  $sstTripleIds = New-Object System.Collections.ArrayList
  $orphanRows = New-Object System.Collections.ArrayList
  # parent lookup for this class: Access BreakerID -> (mfr,type,std,acdc,style? no)
  $par = @{}
  $rp = $cn.Execute("SELECT ID, Mfr_ID, Type, cStandard, Acdc FROM Breaker$($classes[$c])")
  while(-not $rp.EOF){ $par[[int]$rp.Fields.Item(0).Value] = @($rp.Fields.Item(1).Value,$rp.Fields.Item(2).Value,$rp.Fields.Item(3).Value,$rp.Fields.Item(4).Value); $rp.MoveNext() }

  $rank = 0
  while (-not $rs.EOF) {
    $rank++   # = tcc.id
    [void]$srcIds.Add([int]$rs.Fields.Item(0).Value)
    $brkId = [int]$rs.Fields.Item(1).Value
    $style = $rs.Fields.Item(2).Value
    $useSst = $rs.Fields.Item(3).Value
    $isSst = ($null -ne $useSst) -and (-not ($useSst -is [System.DBNull])) -and ([int]$useSst -ne 0)
    if ($isSst) {
      $m = $rs.Fields.Item(4).Value; $ty = $rs.Fields.Item(5).Value; $sy = $rs.Fields.Item(6).Value
      $key = (("" + $m) + "`u{241F}" + ("" + $ty) + "`u{241F}" + ("" + $sy))
      if (-not $tripleMap.ContainsKey($key)) {
        $tid = $tripleMap.Count + 1
        $tripleMap[$key] = $tid
        [void]$tripleRows.Add("('$c',$tid," + (sq $m) + "," + (sq $ty) + "," + (sq $sy) + ")")
      }
      [void]$sstStyleIds.Add($rank)
      [void]$sstTripleIds.Add($tripleMap[$key])
    }
    # orphan (MCCB only): if this rank is in the live orphan id set, capture parent 4-tuple
    if ($c -eq 'mccb' -and $orphanSet.ContainsKey($rank)) {
      $p = $par[$brkId]
      [void]$orphanRows.Add("($rank,$brkId," + (num $p[0]) + "," + (sq $p[1]) + "," + (num $p[2]) + "," + (num $p[3]) + "," + (sq $style) + ")")
    }
    $rs.MoveNext()
  }

  # source_id file (DEFERRED apply): one array unnest
  $arr = ($srcIds -join ',')
  $srcSql = "UPDATE tcc.brk_$($c)_styles t SET source_id = v.src_id FROM (SELECT i AS style_id, a[i] AS src_id FROM (SELECT ARRAY[$arr]::int[] a) z, generate_series(1, array_length(a,1)) i) v WHERE t.id = v.style_id;"
  [System.IO.File]::WriteAllText("$out\d1_90_srcid_$c.sql", $srcSql, [System.Text.UTF8Encoding]::new($false))

  # triples file (compact multi-row VALUES)
  $triplesSql = "INSERT INTO tcc._stg_d1_triples(class,triple_id,mfr,type,style) VALUES`n" + ($tripleRows -join ",`n") + ";"
  [System.IO.File]::WriteAllText("$out\d1_04_triples_$c.sql", $triplesSql, [System.Text.UTF8Encoding]::new($false))

  # sst assign file (two arrays)
  $sstSql = "INSERT INTO tcc._stg_d1_sst(class,style_id,triple_id) SELECT '$c', s[i], tr[i] FROM (SELECT ARRAY[" + ($sstStyleIds -join ',') + "]::int[] s, ARRAY[" + ($sstTripleIds -join ',') + "]::int[] tr) z, generate_series(1, array_length(s,1)) i;"
  [System.IO.File]::WriteAllText("$out\d1_05_sst_$c.sql", $sstSql, [System.Text.UTF8Encoding]::new($false))

  if ($c -eq 'mccb') {
    $orphanSql = "INSERT INTO tcc._stg_d1_orphan(style_id,src_breaker_id,mfr_id,type,standard,acdc,src_style) VALUES`n" + ($orphanRows -join ",`n") + ";"
    [System.IO.File]::WriteAllText("$out\d1_06_orphan.sql", $orphanSql, [System.Text.UTF8Encoding]::new($false))
  }

  # integrity md5s (canonical, Supabase-reproducible) to verify the MCP-loaded staging matches source
  $md5h = [System.Security.Cryptography.MD5]::Create()
  # sst canonical: "style_id:triple_id" in style_id order, joined by ','  (sst arrays already in style_id order)
  $sstCanon = (0..($sstStyleIds.Count-1) | ForEach-Object { "$($sstStyleIds[$_]):$($sstTripleIds[$_])" }) -join ','
  $sstHash  = ($md5h.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($sstCanon)) | ForEach-Object { $_.ToString('x2') }) -join ''
  # triples canonical: "mfr|type|style" in triple_id order, joined by LF (NULL->'')
  $tripLines = New-Object System.Collections.ArrayList
  foreach($kv in ($tripleMap.GetEnumerator() | Sort-Object Value)){ $parts=$kv.Key -split "`u{241F}"; [void]$tripLines.Add(($parts[0]+'|'+$parts[1]+'|'+$parts[2])) }
  $tripCanon = ($tripLines -join "`n")
  $tripHash = ($md5h.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($tripCanon)) | ForEach-Object { $_.ToString('x2') }) -join ''
  $summary += "[$c] styles=$rank distinct_triples=$($tripleMap.Count) sst_rows=$($sstStyleIds.Count) orphan_rows=$($orphanRows.Count) ssthash=$sstHash triphash=$tripHash"
}
$cn.Close()
$summary | ForEach-Object { Write-Output $_ }
Write-Output 'GEN_DONE'