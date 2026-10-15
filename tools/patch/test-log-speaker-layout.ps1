$ErrorActionPreference = 'Stop'
foreach ($name in @('UnityEngine.dll', 'UnityEngine.CoreModule.dll', 'Unity.TextMeshPro.dll')) {
    $null = [Reflection.Assembly]::LoadFrom(('D:/SteamLibrary/steamapps/common/Elsinore/Elsinore_Data/Managed/' + $name))
}
$assembly = [Reflection.Assembly]::LoadFrom((Resolve-Path runtime/build/ElsinoreHan.TranslationToggle.dll).Path)
$method = $assembly.GetType('LogSpeakerLayout', $true).GetMethod('ResolveIndent')
$cases = @(
    @([single]160, [single]200, [single]36, [single]209),
    @([single]160, [single]80, [single]36, [single]160),
    @([single]160, [single]159, [single]36, [single]168),
    @([single]240, [single]200, [single]36, [single]240),
    @([single]160, [single]::NaN, [single]36, [single]160),
    @([single]160, [single]::PositiveInfinity, [single]36, [single]160),
    @([single]160, [single]200, [single]0, [single]160),
    @([single]160, [single]200, [single]::NaN, [single]160)
)
foreach ($case in $cases) {
    $actual = $method.Invoke($null, @($case[0], $case[1], $case[2]))
    if ($actual -ne $case[3]) { throw '日志姓名缩进断言失败' }
}
Write-Output '8项真实C#姓名缩进边界断言通过'
