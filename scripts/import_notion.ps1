# Notion批量导入 - 408和政治
$key = Get-Content "$env:USERPROFILE\.config\notion\api_key"
$h = @{"Authorization"="Bearer $key"; "Notion-Version"="2025-09-03"; "Content-Type"="application/json"}
$root = "387715f9-ecd6-807f-a418-ff5520cfc38e"
$base = "D:/my-project/kaoyan-reference"

function New-NotionPage($title, $parentId) {
    $body = @{parent=@{page_id=$parentId}; properties=@{title=@(@{text=@{content=$title}})}}
    $r = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" -Method Post -Headers $h -Body (ConvertTo-Json -InputObject $body -Depth 5)
    return $r.id
}

function New-Paragraph($text) { @{object="block"; type="paragraph"; paragraph=@{rich_text=@(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}})}} }
function New-Heading($text, $level) { @{object="block"; type="heading_$level"; "heading_$level"=@{rich_text=@(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}})}} }
function New-Quote($text) { @{object="block"; type="quote"; quote=@{rich_text=@(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}})}} }
function New-Divider { @{object="block"; type="divider"; divider=@{}} }
function New-Bullet($text) { @{object="block"; type="bulleted_list_item"; bulleted_list_item=@{rich_text=@(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}})}} }
function New-Numbered($text) { @{object="block"; type="numbered_list_item"; numbered_list_item=@{rich_text=@(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}})}} }
function New-Code($text) { @{object="block"; type="code"; code=@{rich_text=@(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}}); language="plain text"}} }

function New-BoldParagraph($text) {
    $parts = @()
    $regex = "\*\*([^*]+)\*\*"
    $lastIndex = 0
    $matches = [regex]::Matches($text, $regex)
    foreach ($m in $matches) {
        if ($m.Index -gt $lastIndex) {
            $before = $text.Substring($lastIndex, $m.Index - $lastIndex)
            if ($before) { $parts += @{type="text"; text=@{content=$before.Substring(0,[Math]::Min($before.Length,1000))}} }
        }
        $parts += @{type="text"; text=@{content=$m.Groups[1].Value.Substring(0,[Math]::Min($m.Groups[1].Value.Length,1000))}; annotations=@{bold=$true}}
        $lastIndex = $m.Index + $m.Length
    }
    if ($lastIndex -lt $text.Length) {
        $after = $text.Substring($lastIndex)
        if ($after) { $parts += @{type="text"; text=@{content=$after.Substring(0,[Math]::Min($after.Length,1000))}} }
    }
    if ($parts.Count -eq 0) { $parts = @(@{type="text"; text=@{content=$text.Substring(0,[Math]::Min($text.Length,1000))}}) }
    return @{object="block"; type="paragraph"; paragraph=@{rich_text=$parts}}
}

function Convert-MDToBlocks($text) {
    $blocks = @()
    $lines = $text -split "\n"
    $i = 0
    while ($i -lt $lines.Count) {
        $line = $lines[$i]
        if (-not $line.Trim()) { $i++; continue }
        
        if ($line -match '^#### (.+)') { $blocks += New-Heading $matches[1] 3 }
        elseif ($line -match '^### (.+)') { $blocks += New-Heading $matches[1] 2 }
        elseif ($line -match '^## (.+)') { $blocks += New-Heading $matches[1] 1 }
        elseif ($line -match '^# (.+)') { $blocks += New-Heading $matches[1] 1 }
        elseif ($line -match '^> (.+)') { $blocks += New-Quote $matches[1] }
        elseif ($line.Trim() -eq '---') { $blocks += New-Divider }
        elseif ($line -match '^\d+\. (.+)') { $blocks += New-Numbered $matches[1] }
        elseif ($line -match '^- (.+)') { $blocks += New-Bullet $matches[1] }
        elseif ($line.StartsWith('```')) {
            $code = ""; $i++
            while ($i -lt $lines.Count -and -not $lines[$i].StartsWith('```')) { $code += $lines[$i] + "`n"; $i++ }
            $blocks += New-Code $code
        }
        elseif ($line -match '\|.*\|' -and $line.Split('|').Count -ge 3) {
            $tl = @($line)
            while ($i+1 -lt $lines.Count -and $lines[$i+1] -match '\|.*\|' -and $lines[$i+1].Split('|').Count -ge 3) {
                $i++; $tl += $lines[$i]
            }
            foreach ($t in $tl) {
                if ($t -match '^\|[-:|\s]+\|$') { continue }
                $cells = ($t -split '\|')[1..($t.Split('|').Count-2)] -join " | "
                $blocks += New-Paragraph $cells.Trim()
            }
        }
        else { $blocks += New-BoldParagraph $line.Trim() }
        $i++
    }
    return $blocks
}

function Import-File($path, $title, $parentId) {
    Write-Host "  $title"
    $pageId = New-NotionPage $title $parentId
    $content = Get-Content $path -Raw -Encoding UTF8
    $blocks = Convert-MDToBlocks $content
    $total = $blocks.Count
    Write-Host "    Blocks: $total"
    for ($s = 0; $s -lt $total; $s += 90) {
        $batch = $blocks[$s..([Math]::Min($s+89, $total-1))]
        $body = @{children=$batch}
        Invoke-RestMethod -Uri "https://api.notion.com/v1/blocks/$pageId/children" -Method Patch -Headers $h -Body (ConvertTo-Json -InputObject $body -Depth 10 -Compress) | Out-Null
    }
    Write-Host "    OK"
}

# Import 408
$subj408 = New-NotionPage "408" $root
Write-Host "408: $subj408"
Import-File "$base/408/知识库/408数据结构_按章节知识点.md" "数据结构" $subj408
Import-File "$base/408/知识库/计算机组成原理_按章节知识点.md" "计算机组成原理" $subj408
Import-File "$base/408/知识库/操作系统_按章节知识点.md" "操作系统" $subj408
Import-File "$base/408/知识库/计算机网络_按章节知识点.md" "计算机网络" $subj408
Import-File "$base/408/常考题型与解法/408数据结构_常考题型与解法.md" "常考题型-数据结构" $subj408
Import-File "$base/408/常考题型与解法/计算机组成原理_常考题型与解法.md" "常考题型-计组" $subj408
Import-File "$base/408/常考题型与解法/操作系统_常考题型与解法.md" "常考题型-操作系统" $subj408
Import-File "$base/408/常考题型与解法/计算机网络_常考题型与解法.md" "常考题型-计算机网络" $subj408

# Import 政治
$subjPoli = New-NotionPage "政治" $root
Write-Host "政治: $subjPoli"
Import-File "$base/政治/知识库/01-马克思主义基本原理.md" "马原" $subjPoli
Import-File "$base/政治/知识库/02-毛泽东思想和中国特色社会主义理论体系概论.md" "毛中特" $subjPoli
Import-File "$base/政治/知识库/03-习近平新时代中国特色社会主义思想概论.md" "习思想" $subjPoli
Import-File "$base/政治/知识库/04-中国近现代史纲要.md" "史纲" $subjPoli
Import-File "$base/政治/知识库/05-思想道德与法治.md" "思修" $subjPoli
Import-File "$base/政治/知识库/06-形势与政策知识点.md" "时政" $subjPoli
Import-File "$base/政治/常考题型与解法/01-马原常见题型.md" "常考题型-马原" $subjPoli
Import-File "$base/政治/常考题型与解法/02-毛中特常见题型.md" "常考题型-毛中特" $subjPoli
Import-File "$base/政治/常考题型与解法/03-史纲常见题型.md" "常考题型-史纲" $subjPoli
Import-File "$base/政治/常考题型与解法/04-思修常见题型.md" "常考题型-思修" $subjPoli
Import-File "$base/政治/常考题型与解法/05-形势与政策常见题型.md" "常考题型-时政" $subjPoli

Write-Host "`nALL DONE!"
