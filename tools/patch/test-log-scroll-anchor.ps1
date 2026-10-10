param(
    [string]$AnchorAssembly = 'runtime/build/ElsinoreHan.TranslationToggle.dll',
    [string]$GamePath = 'D:/SteamLibrary/steamapps/common/Elsinore'
)
$ErrorActionPreference = 'Stop'
# 只执行真实 helper 的纯段落映射函数；不创建 Unity 对象或启动游戏。
$managed = Join-Path $GamePath 'Elsinore_Data/Managed'
foreach ($dependency in @('UnityEngine.dll', 'UnityEngine.CoreModule.dll', 'UnityEngine.UIModule.dll', 'UnityEngine.UI.dll', 'Unity.TextMeshPro.dll')) {
    $null = [System.Reflection.Assembly]::LoadFrom((Join-Path $managed $dependency))
}
$assembly = [System.Reflection.Assembly]::LoadFrom((Resolve-Path -LiteralPath $AnchorAssembly).Path)
$type = $assembly.GetType('LogScrollAnchor', $true)
$count = $type.GetMethod('ParagraphCount')
$at = $type.GetMethod('ParagraphAt')
$start = $type.GetMethod('ParagraphStart')
$documentCount = $type.GetMethod('DocumentParagraphCount')
$documentAt = $type.GetMethod('DocumentParagraphAt')
$documentStart = $type.GetMethod('DocumentParagraphStart')
$assertions = 0
function Assert-Equal($actual, $expected, [string]$name) {
    if ($actual -cne $expected) { throw "$name 的实际值 $actual 与期望值 $expected 不符" }
    $script:assertions++
}
Assert-Equal ($documentCount.Invoke($null, @("`n<i></i>`n甲`n`n乙`n"))) 2 '文档空白及空标签不算阅读段落'
Assert-Equal ($documentCount.Invoke($null, @("a`n`n`nb"))) ($documentCount.Invoke($null, @("甲`n乙"))) '文档空白数量不同仍对应'
Assert-Equal ($documentStart.Invoke($null, @("a`n`n`nb", 1))) 4 '文档第二非空段起点'
Assert-Equal ($documentAt.Invoke($null, @("a`n`n`nb", 4))) 1 '文档第二非空段序号'
Assert-Equal ($documentAt.Invoke($null, @("a`n`n`nb", 2))) 0 '空白分隔属于前段'
Assert-Equal ($documentStart.Invoke($null, @('单段', -1))) -1 '文档负数段号'
Assert-Equal ($documentStart.Invoke($null, @('单段', 1))) -1 '文档越界段号'
Assert-Equal ($documentCount.Invoke($null, @(''))) 0 '文档空正文'
Assert-Equal ($count.Invoke($null, @('单段文字'))) 1 '单段'
Assert-Equal ($count.Invoke($null, @("a`n`nb`n"))) 4 '空段和末尾段'
Assert-Equal ($count.Invoke($null, @("a`r`nb"))) 2 'CRLF 不重复计段'
Assert-Equal ($at.Invoke($null, @("a`nb", 1))) 0 '换行字符属于前段'
Assert-Equal ($at.Invoke($null, @("a`nb", 2))) 1 '换行后属于后段'
Assert-Equal ($start.Invoke($null, @("a`nb", -1))) -1 '负数段号'
Assert-Equal ($start.Invoke($null, @("a`nb", 2))) -1 '越界段号'
$source = "<b>Hamlet:</b> <indent=16%>A rather long line.<line-height=90%>`n<b>Ophelia:</b> Short."
$target = "<b>哈姆雷特：</b> <indent=16%>短句。<line-height=90%>`n<b>奥菲莉娅：</b>一条比英文更长的中文句子。"
Assert-Equal ($count.Invoke($null, @($source))) ($count.Invoke($null, @($target))) '中英文长度不同但结构一致'
foreach ($text in @($source, $target)) {
    $offset = $start.Invoke($null, @($text, 1))
    Assert-Equal ($text.Substring($offset).StartsWith('<b>')) $true '第二段起点位于真实结构标记前'
    Assert-Equal ($at.Invoke($null, @($text, $offset))) 1 '中英文第二段号一致'
}
[pscustomobject]@{ passed=$true; assertions=$assertions; scope='真实 C# helper 纯映射函数；不是 Unity 布局或物理键盘验收' } | ConvertTo-Json
