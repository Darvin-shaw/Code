# 诊断 Docker/Nexent 所需的 Windows 功能状态（管理员运行）
$ErrorActionPreference = "Continue"
$names = @(
    "VirtualMachinePlatform",
    "HypervisorPlatform",
    "Microsoft-Windows-Subsystem-Linux",
    "Microsoft-Hyper-V-All",
    "Microsoft-Hyper-V-Hypervisor",
    "Containers"
)
$rows = foreach ($name in $names) {
    try {
        Get-WindowsOptionalFeature -Online -FeatureName $name |
            Select-Object FeatureName, State
    } catch {
        [pscustomobject]@{ FeatureName = $name; State = "ERROR" }
    }
}
$out = Join-Path $env:TEMP "codex-feature-states.json"
$rows | ConvertTo-Json | Out-File -FilePath $out -Encoding utf8
Write-Output "written=$out"
