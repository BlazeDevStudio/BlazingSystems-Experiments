$ErrorActionPreference = 'Stop'

# Exercise the real build script without compiling or touching installed state.
$buildScript = (Resolve-Path (Join-Path $PSScriptRoot '../../build-local.ps1')).Path
$windowsPowerShell = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$fixtureRoot = Join-Path $PSScriptRoot ('.build-local-fixture-' + [Guid]::NewGuid().ToString('N'))
$fixtureRoot = [IO.Path]::GetFullPath($fixtureRoot)

try {
    New-Item -ItemType Directory -Path $fixtureRoot | Out-Null
    $fakeDotnet = @'
@echo off
echo %*>>"%SOFTTIMER_BUILD_TEST_LOG%"
set attempt=0
if exist "%SOFTTIMER_BUILD_TEST_COUNT%" set /p attempt=<"%SOFTTIMER_BUILD_TEST_COUNT%"
set /a attempt+=1 >nul
>"%SOFTTIMER_BUILD_TEST_COUNT%" echo %attempt%
if "%attempt%"=="%SOFTTIMER_BUILD_TEST_FAIL_AT%" exit /b 37
exit /b 0
'@
    Set-Content -LiteralPath (Join-Path $fixtureRoot 'dotnet.cmd') -Value $fakeDotnet -Encoding Ascii

    foreach ($failAt in 1, 2, 3, 4, 0) {
        $logPath = Join-Path $fixtureRoot "calls-$failAt.txt"
        $countPath = Join-Path $fixtureRoot "count-$failAt.txt"
        $start = New-Object Diagnostics.ProcessStartInfo
        $start.FileName = $windowsPowerShell
        $start.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $buildScript + '"'
        $start.UseShellExecute = $false
        $start.CreateNoWindow = $true
        $start.RedirectStandardOutput = $true
        $start.RedirectStandardError = $true
        $start.EnvironmentVariables['PATH'] = $fixtureRoot + ';' + $env:PATH
        $start.EnvironmentVariables['SOFTTIMER_BUILD_TEST_LOG'] = $logPath
        $start.EnvironmentVariables['SOFTTIMER_BUILD_TEST_COUNT'] = $countPath
        $start.EnvironmentVariables['SOFTTIMER_BUILD_TEST_FAIL_AT'] = [string]$failAt

        $process = [Diagnostics.Process]::Start($start)
        try {
            $stdoutTask = $process.StandardOutput.ReadToEndAsync()
            $stderrTask = $process.StandardError.ReadToEndAsync()
            if (-not $process.WaitForExit(30000)) {
                $process.Kill()
                throw "Build script did not finish for failure step $failAt."
            }
            $stdout = $stdoutTask.GetAwaiter().GetResult()
            $stderr = $stderrTask.GetAwaiter().GetResult()
            $exitCode = $process.ExitCode
        }
        finally {
            $process.Dispose()
        }

        $calls = @(Get-Content -LiteralPath $logPath)
        if ($failAt -gt 0) {
            if ($exitCode -eq 0) { throw "FAIL: dotnet step $failAt exited 37, but build-local.ps1 reported success." }
            if ($calls.Count -ne $failAt) { throw "FAIL: step $failAt failed, but $($calls.Count) dotnet commands ran." }
            if ($stdout.Contains('Build passed.')) { throw "FAIL: failed build printed the success message." }
            if (-not $stderr.Contains('37')) { throw "FAIL: failure did not identify dotnet exit code 37." }
            Write-Host "PASS: step $failAt failure stops the build and reports failure."
        }
        else {
            if ($exitCode -ne 0) { throw "FAIL: successful dotnet commands returned $exitCode. $stderr" }
            if ($calls.Count -ne 4) { throw "FAIL: successful build ran $($calls.Count) of 4 dotnet commands." }
            if (-not $stdout.Contains('Build passed.')) { throw "FAIL: successful build omitted the success message." }
            if (-not $calls[0].StartsWith('restore ') -or -not $calls[1].StartsWith('restore ') -or
                -not $calls[2].StartsWith('build ') -or -not $calls[3].StartsWith('build ')) {
                throw 'FAIL: successful build changed the restore/build command order.'
            }
            Write-Host 'PASS: all four successful dotnet steps report build success.'
        }
    }
}
finally {
    $testDirectory = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
    if (-not $fixtureRoot.StartsWith($testDirectory, [StringComparison]::OrdinalIgnoreCase) -or
        -not ([IO.Path]::GetFileName($fixtureRoot)).StartsWith('.build-local-fixture-')) {
        throw 'Refusing to remove a fixture outside the test directory.'
    }
    if (Test-Path -LiteralPath $fixtureRoot) { Remove-Item -LiteralPath $fixtureRoot -Recurse -Force }
}
