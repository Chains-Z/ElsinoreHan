# 用户正在游玩时仅使用冻结来源，不触碰可能被实时日志独占的原存档目录。
function Get-ProbeSaveSnapshot([string]$Path, [bool]$ConcurrentGameActive) {
    if ($ConcurrentGameActive -or -not (Test-Path -LiteralPath $Path)) { return }
    foreach ($file in Get-ChildItem -LiteralPath $Path -File -Recurse -Force) {
        $relative = $file.FullName.Substring($Path.Length + 1)
        [pscustomobject]@{
            path = $relative
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            write_time = $file.LastWriteTimeUtc.ToString('o')
        }
    }
}
