# Notion Import - 408 and Politics
$ErrorActionPreference = "Continue"
$key = Get-Content "$env:USERPROFILE\.config\notion\api_key"
$h = @{"Authorization"="Bearer $key"; "Notion-Version"="2025-09-03"; "Content-Type"="application/json"}
$root = "387715f9-ecd6-807f-a418-ff5520cfc38e"
$base = "D:/my-project/kaoyan-reference"
$BATCH = 30

function Invoke-N($method, $url, $body) {
    $json = if($body) { ConvertTo-Json -InputObject $body -Depth 10 -Compress } else { $null }
    return Invoke-RestMethod -Uri $url -Method $method -Headers $h -Body $json
}

function New-Page($title, $parentId) {
    return (Invoke-N POST "https://api.notion.com/v1/pages" @{
        parent = @{page_id = $parentId}
        properties = @{title = @(@{text = @{content = $title}})}
    }).id
}

function Block($type, $content) {
    $c = $content.Substring(0, [Math]::Min($content.Length, 1000))
    if($type -eq "h1") { return @{object="block";type="heading_1";heading_1=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "h2") { return @{object="block";type="heading_2";heading_2=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "h3") { return @{object="block";type="heading_3";heading_3=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "p")  { return @{object="block";type="paragraph";paragraph=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "q")  { return @{object="block";type="quote";quote=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "b")  { return @{object="block";type="bulleted_list_item";bulleted_list_item=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "n")  { return @{object="block";type="numbered_list_item";numbered_list_item=@{rich_text=@(@{type="text";text=@{content=$c}})}} }
    if($type -eq "c")  { return @{object="block";type="code";code=@{rich_text=@(@{type="text";text=@{content=$c}});language="plain text"}} }
    if($type -eq "d")  { return @{object="block";type="divider";divider=@{}} }
    return @{object="block";type="paragraph";paragraph=@{rich_text=@(@{type="text";text=@{content=$c}})}}
}

function Import-File($path, $title, $parentId) {
    Write-Host "  $title" -NoNewline
    $pageId = New-Page $title $parentId
    $lines = Get-Content $path -Encoding UTF8 | ForEach-Object { $_.TrimEnd() }
    
    $blocks = @()
    $i = 0
    while($i -lt $lines.Count) {
        $s = $lines[$i].Trim()
        if(-not $s) { $i++; continue }
        
        if($s -match '^#### (.+)') { $blocks += Block "h3" $matches[1] }
        elseif($s -match '^### (.+)') { $blocks += Block "h2" $matches[1] }
        elseif($s -match '^## (.+)') { $blocks += Block "h1" $matches[1] }
        elseif($s -match '^> (.+)') { $blocks += Block "q" $matches[1] }
        elseif($s -eq '---') { $blocks += Block "d" "" }
        elseif($s -match '^\d+\.\s(.+)') { $blocks += Block "n" $matches[1] }
        elseif($s -match '^- (.+)') { $blocks += Block "b" $matches[1] }
        elseif($s.StartsWith('```')) {
            $code = ""; $i++
            while($i -lt $lines.Count -and -not $lines[$i].StartsWith('```')) { $code += $lines[$i] + "`n"; $i++ }
            $blocks += Block "c" $code
        }
        elseif($s -match '\|.*\|' -and $s.Split('|').Count -ge 3) {
            $parts = $s.Split('|')[1..($s.Split('|').Count-2)] -join " | "
            $blocks += Block "p" $parts.Trim()
        }
        else { $blocks += Block "p" $s }
        $i++
    }
    
    # Send blocks in batches
    for($s = 0; $s -lt $blocks.Count; $s += $BATCH) {
        $batch = $blocks[$s..([Math]::Min($s+$BATCH-1, $blocks.Count-1))]
        try {
            Invoke-N PATCH "https://api.notion.com/v1/blocks/$pageId/children" @{children = $batch} | Out-Null
        } catch {
            Write-Host " FAIL"
            return
        }
    }
    Write-Host " OK ($($blocks.Count) blocks)"
}

# Clean existing 408
try {
    $children = Invoke-N GET "https://api.notion.com/v1/blocks/$root/children?page_size=20" $null
    foreach($c in $children.results) {
        if($c.type -eq 'child_page' -and $c.child_page.title -eq '408') {
            Invoke-N PATCH "https://api.notion.com/v1/pages/$($c.id)" @{archived=$true} | Out-Null
        }
    }
} catch {}

# Import 408
Write-Host "=== 408 ==="
$s408 = New-Page "408" $root
Import-File "$base/408/知识库/408数据结构_按章节知识点.md" "数据结构" $s408
Import-File "$base/408/知识库/计算机组成原理_按章节知识点.md" "计算机组成原理" $s408
Import-File "$base/408/知识库/操作系统_按章节知识点.md" "操作系统" $s408
Import-File "$base/408/知识库/计算机网络_按章节知识点.md" "计算机网络" $s408
Import-File "$base/408/常考题型与解法/408数据结构_常考题型与解法.md" "常考题型-数据结构" $s408
Import-File "$base/408/常考题型与解法/计算机组成原理_常考题型与解法.md" "常考题型-计组" $s408
Import-File "$base/408/常考题型与解法/操作系统_常考题型与解法.md" "常考题型-操作系统" $s408
Import-File "$base/408/常考题型与解法/计算机网络_常考题型与解法.md" "常考题型-计算机网络" $s408

# Import 政治
Write-Host "=== 政治 ==="
$sPoli = New-Page "政治" $root
Import-File "$base/政治/知识库/01-马克思主义基本原理.md" "马原" $sPoli
Import-File "$base/政治/知识库/02-毛泽东思想和中国特色社会主义理论体系概论.md" "毛中特" $sPoli
Import-File "$base/政治/知识库/03-习近平新时代中国特色社会主义思想概论.md" "习思想" $sPoli
Import-File "$base/政治/知识库/04-中国近现代史纲要.md" "史纲" $sPoli
Import-File "$base/政治/知识库/05-思想道德与法治.md" "思修" $sPoli
Import-File "$base/政治/知识库/06-形势与政策知识点.md" "时政" $sPoli
Import-File "$base/政治/常考题型与解法/01-马原常见题型.md" "常考题型-马原" $sPoli
Import-File "$base/政治/常考题型与解法/02-毛中特常见题型.md" "常考题型-毛中特" $sPoli
Import-File "$base/政治/常考题型与解法/03-史纲常见题型.md" "常考题型-史纲" $sPoli
Import-File "$base/政治/常考题型与解法/04-思修常见题型.md" "常考题型-思修" $sPoli
Import-File "$base/政治/常考题型与解法/05-形势与政策常见题型.md" "常考题型-时政" $sPoli

Write-Host "ALL DONE!"