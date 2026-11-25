param(
    [string]$Deck = "",
    [string]$Map = ""
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
if (-not $Deck) { $Deck = Join-Path $repo "docs\visual_references\Figures_final_submission.pptx" }
if (-not $Map) { $Map = Join-Path $repo "config\submission_visual_map.csv" }
$deckPath = (Resolve-Path -LiteralPath $Deck).Path
$mapPath = (Resolve-Path -LiteralPath $Map).Path
$rows = Import-Csv -LiteralPath $mapPath
$expectedDeckHash = ($rows | Select-Object -First 1).source_deck_sha256.ToUpperInvariant()
$actualDeckHash = (Get-FileHash -LiteralPath $deckPath -Algorithm SHA256).Hash
if ($actualDeckHash -ne $expectedDeckHash) {
    throw "Final deck SHA-256 mismatch: $actualDeckHash != $expectedDeckHash"
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("deck-audit-" + [guid]::NewGuid().ToString("N"))
[System.IO.Directory]::CreateDirectory($tempRoot) | Out-Null
$ppt = $null
$presentation = $null
$failures = New-Object System.Collections.Generic.List[string]
try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $presentation = $ppt.Presentations.Open($deckPath, $true, $true, $false)
    foreach ($row in $rows) {
        $export = Join-Path $tempRoot (([System.IO.Path]::GetFileNameWithoutExtension($row.visual_reference)) + ".png")
        $presentation.Slides.Item([int]$row.slide_number).Export($export, "PNG", 1920, 1080)
        $exportHash = (Get-FileHash -LiteralPath $export -Algorithm SHA256).Hash.ToLowerInvariant()
        $reference = Join-Path $repo ($row.visual_reference -replace '/', '\')
        $referenceHash = (Get-FileHash -LiteralPath $reference -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($referenceHash -ne $row.visual_reference_sha256.ToLowerInvariant()) {
            $failures.Add("reference hash mismatch: $($row.visual_reference)")
        }
        if ($exportHash -ne $referenceHash) {
            $failures.Add("slide $($row.slide_number) export mismatch: $($row.publication_item)")
        }
    }
}
finally {
    if ($presentation) { $presentation.Close(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) }
    if ($ppt) { $ppt.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ppt) }
    Get-ChildItem -LiteralPath $tempRoot -File | Remove-Item -Force
    Remove-Item -LiteralPath $tempRoot -Force
}
if ($failures.Count -gt 0) {
    $failures | ForEach-Object { Write-Error $_ }
    exit 1
}
Write-Output "PASS: $($rows.Count) mapped slides exported from canonical deck and matched frozen references."
