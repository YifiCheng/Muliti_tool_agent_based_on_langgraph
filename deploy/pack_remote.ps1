$ErrorActionPreference = "Stop"

$Root = Resolve-Path "$PSScriptRoot\.."
$BundleRoot = Join-Path $Root ".deploy_bundle"
$AppRoot = Join-Path $BundleRoot "business-multi-tool-agent"
$Target = Join-Path $Root "business-multi-tool-agent-remote.tar.gz"

if (Test-Path $BundleRoot) {
    Remove-Item -LiteralPath $BundleRoot -Recurse -Force
}
New-Item -ItemType Directory -Force $AppRoot | Out-Null

$SkipDirNames = @(
    ".pytest-cache",
    ".pytest_cache",
    ".tmp",
    "__pycache__",
    "raw",
    "clean",
    "reports"
)

$SkipFileExtensions = @(
    ".pyc",
    ".db",
    ".sqlite"
)

function Should-SkipPath {
    param(
        [System.IO.FileSystemInfo] $Item
    )

    $Relative = $Item.FullName.Substring($Root.Path.Length).TrimStart("\")
    $Parts = $Relative -split "\\"

    foreach ($Part in $Parts) {
        if ($SkipDirNames -contains $Part) {
            return $true
        }
    }

    if (-not $Item.PSIsContainer) {
        if ($Item.Name -eq ".env") {
            return $true
        }
        if ($SkipFileExtensions -contains $Item.Extension) {
            return $true
        }
    }

    return $false
}

function Copy-Tree {
    param(
        [string] $SourceDir
    )

    Get-ChildItem -LiteralPath $SourceDir -Force -ErrorAction Stop |
        ForEach-Object {
            if (Should-SkipPath $_) {
                return
            }

            $Relative = $_.FullName.Substring($Root.Path.Length).TrimStart("\")
            $Destination = Join-Path $AppRoot $Relative

            if ($_.PSIsContainer) {
                New-Item -ItemType Directory -Force $Destination | Out-Null
                Copy-Tree -SourceDir $_.FullName
            } else {
                New-Item -ItemType Directory -Force (Split-Path $Destination -Parent) | Out-Null
                Copy-Item -LiteralPath $_.FullName -Destination $Destination -Force
            }
        }
}

$CopyRoots = @(
    "README.md",
    "docs",
    "agent-platform"
)

foreach ($CopyRoot in $CopyRoots) {
    $SourceRoot = Join-Path $Root $CopyRoot
    if (-not (Test-Path $SourceRoot)) {
        continue
    }

    $SourceItem = Get-Item -LiteralPath $SourceRoot -Force
    if (-not $SourceItem.PSIsContainer) {
        $Destination = Join-Path $AppRoot $CopyRoot
        New-Item -ItemType Directory -Force (Split-Path $Destination -Parent) | Out-Null
        Copy-Item -LiteralPath $SourceRoot -Destination $Destination -Force
        continue
    }

    $DestinationRoot = Join-Path $AppRoot $CopyRoot
    New-Item -ItemType Directory -Force $DestinationRoot | Out-Null
    Copy-Tree -SourceDir $SourceRoot
}

if (Test-Path $Target) {
    Remove-Item -LiteralPath $Target -Force
}

tar -czf $Target -C $BundleRoot "business-multi-tool-agent"

Write-Host "bundle=$Target"
Write-Host "pack_remote=ready"
