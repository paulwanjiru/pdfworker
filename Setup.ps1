# ============================================================
#  Document Studio Pro — Setup.ps1
#  Zero-dependency WPF splash screen installer for Windows
#  Requires: PowerShell 5.1+ (built-in on Windows 10/11)
# ============================================================

Set-StrictMode -Off
$ErrorActionPreference = 'Stop'

# ── Load WPF Assemblies ──────────────────────────────────────────────────────
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms

# ── Application Metadata ─────────────────────────────────────────────────────
$AppName    = "Document Studio Pro"
$AppVersion = "5.0"
$AppDir     = Join-Path $env:LOCALAPPDATA "DocumentStudioPro"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonDir  = Join-Path $AppDir "runtime"
$LogFile    = Join-Path $AppDir "install.log"

$PYTHON_VERSION   = "3.11.9"
$PYTHON_INSTALLER = "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
$GET_PIP_URL      = "https://bootstrap.pypa.io/get-pip.py"

# ── XAML UI Definition ───────────────────────────────────────────────────────
[xml]$XAML = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="Document Studio Pro — Installer"
    Width="680" Height="440"
    WindowStyle="None"
    AllowsTransparency="True"
    Background="Transparent"
    WindowStartupLocation="CenterScreen"
    ResizeMode="NoResize">

  <Window.Resources>
    <Style x:Key="StatusDot" TargetType="Ellipse">
      <Setter Property="Width"  Value="8"/>
      <Setter Property="Height" Value="8"/>
      <Setter Property="Fill"   Value="#2563eb"/>
      <Setter Property="Margin" Value="0,0,8,0"/>
      <Setter Property="VerticalAlignment" Value="Center"/>
      <Style.Triggers>
        <Trigger Property="Tag" Value="done">
          <Setter Property="Fill" Value="#16a34a"/>
        </Trigger>
        <Trigger Property="Tag" Value="error">
          <Setter Property="Fill" Value="#dc2626"/>
        </Trigger>
      </Style.Triggers>
    </Style>
  </Window.Resources>

  <!-- Drop shadow container -->
  <Border Margin="20" CornerRadius="16"
          Background="#0b1220"
          BorderBrush="#2563eb" BorderThickness="1.5">
    <Border.Effect>
      <DropShadowEffect BlurRadius="30" ShadowDepth="0" Opacity="0.6" Color="#2563eb"/>
    </Border.Effect>

    <Grid>
      <Grid.RowDefinitions>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="*"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
      </Grid.RowDefinitions>

      <!-- Drag area -->
      <Border Grid.Row="0" Background="Transparent" MouseDown="Window_MouseDown" Cursor="SizeAll" Height="10"/>

      <!-- Header -->
      <StackPanel Grid.Row="0" Orientation="Vertical" Margin="40,32,40,0">
        <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
          <!-- Glowing dot logo -->
          <Ellipse Width="12" Height="12" Fill="#2563eb" Margin="0,0,12,0" VerticalAlignment="Center">
            <Ellipse.Effect>
              <DropShadowEffect BlurRadius="10" ShadowDepth="0" Color="#2563eb" Opacity="0.9"/>
            </Ellipse.Effect>
          </Ellipse>
          <TextBlock x:Name="TitleBlock" Text="Document Studio Pro"
                     Foreground="White" FontSize="22" FontWeight="Bold"
                     FontFamily="Segoe UI Variable Display, Segoe UI, sans-serif"/>
        </StackPanel>
        <TextBlock Text="Professional Document Suite — Installer"
                   Foreground="#64748b" FontSize="12" Margin="24,4,0,0"
                   FontFamily="Segoe UI Variable Text, Segoe UI, sans-serif"/>

        <!-- Divider -->
        <Rectangle Height="1" Fill="#1e3a8a" Margin="0,20,0,0" Opacity="0.7"/>
      </StackPanel>

      <!-- Steps list -->
      <StackPanel x:Name="StepsPanel" Grid.Row="1" Margin="40,24,40,0" VerticalAlignment="Top">

        <!-- Step row template x5 -->
        <Grid x:Name="Step1Row" Margin="0,0,0,16">
          <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
          <Ellipse x:Name="Dot1" Style="{StaticResource StatusDot}" Grid.Column="0"/>
          <StackPanel Grid.Column="1">
            <TextBlock Text="Checking environment" Foreground="#f1f5f9" FontSize="13" FontWeight="SemiBold"/>
            <TextBlock x:Name="Step1Detail" Text="Validating system requirements and internet connectivity..."
                       Foreground="#64748b" FontSize="11" TextWrapping="Wrap"/>
          </StackPanel>
        </Grid>

        <Grid x:Name="Step2Row" Margin="0,0,0,16">
          <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
          <Ellipse x:Name="Dot2" Style="{StaticResource StatusDot}" Grid.Column="0" Opacity="0.3"/>
          <StackPanel Grid.Column="1" Opacity="0.3">
            <TextBlock Text="Installing Python runtime" Foreground="#f1f5f9" FontSize="13" FontWeight="SemiBold"/>
            <TextBlock x:Name="Step2Detail" Text="Waiting..."
                       Foreground="#64748b" FontSize="11" TextWrapping="Wrap"/>
          </StackPanel>
        </Grid>

        <Grid x:Name="Step3Row" Margin="0,0,0,16">
          <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
          <Ellipse x:Name="Dot3" Style="{StaticResource StatusDot}" Grid.Column="0" Opacity="0.3"/>
          <StackPanel Grid.Column="1" Opacity="0.3">
            <TextBlock Text="Installing application packages" Foreground="#f1f5f9" FontSize="13" FontWeight="SemiBold"/>
            <TextBlock x:Name="Step3Detail" Text="Waiting..."
                       Foreground="#64748b" FontSize="11" TextWrapping="Wrap"/>
          </StackPanel>
        </Grid>

        <Grid x:Name="Step4Row" Margin="0,0,0,16">
          <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
          <Ellipse x:Name="Dot4" Style="{StaticResource StatusDot}" Grid.Column="0" Opacity="0.3"/>
          <StackPanel Grid.Column="1" Opacity="0.3">
            <TextBlock Text="Deploying application &amp; creating shortcuts" Foreground="#f1f5f9" FontSize="13" FontWeight="SemiBold"/>
            <TextBlock x:Name="Step4Detail" Text="Waiting..."
                       Foreground="#64748b" FontSize="11" TextWrapping="Wrap"/>
          </StackPanel>
        </Grid>

        <Grid x:Name="Step5Row" Margin="0,0,0,0">
          <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
          <Ellipse x:Name="Dot5" Style="{StaticResource StatusDot}" Grid.Column="0" Opacity="0.3"/>
          <StackPanel Grid.Column="1" Opacity="0.3">
            <TextBlock Text="Launching Document Studio Pro" Foreground="#f1f5f9" FontSize="13" FontWeight="SemiBold"/>
            <TextBlock x:Name="Step5Detail" Text="Waiting..."
                       Foreground="#64748b" FontSize="11" TextWrapping="Wrap"/>
          </StackPanel>
        </Grid>
      </StackPanel>

      <!-- Progress Bar -->
      <Grid Grid.Row="2" Margin="40,20,40,8">
        <Grid.RowDefinitions>
          <RowDefinition Height="Auto"/>
          <RowDefinition Height="Auto"/>
        </Grid.RowDefinitions>
        <StackPanel Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,0,0,6">
          <TextBlock x:Name="PctLabel" Text="0%" Foreground="#2563eb" FontSize="12" FontWeight="Bold"/>
        </StackPanel>
        <Border Grid.Row="1" CornerRadius="5" Background="#1e293b" Height="10" ClipToBounds="True">
          <Border x:Name="ProgressFill" CornerRadius="5" Background="#2563eb"
                  HorizontalAlignment="Left" Width="0">
            <Border.Effect>
              <DropShadowEffect BlurRadius="8" ShadowDepth="0" Color="#60a5fa" Opacity="0.8"/>
            </Border.Effect>
          </Border>
        </Border>
      </Grid>

      <!-- Status Label -->
      <TextBlock x:Name="StatusLabel" Grid.Row="3"
                 Text="Initializing installer..."
                 Foreground="#64748b" FontSize="11"
                 HorizontalAlignment="Center" Margin="40,0,40,24"
                 TextWrapping="Wrap" TextAlignment="Center"/>
    </Grid>
  </Border>
</Window>
"@

# ── Load & Show Window ────────────────────────────────────────────────────────
$reader = [System.Xml.XmlNodeReader]::new($XAML)
$Window = [System.Windows.Markup.XamlReader]::Load($reader)

# Bind named elements
$TitleBlock   = $Window.FindName('TitleBlock')
$StatusLabel  = $Window.FindName('StatusLabel')
$ProgressFill = $Window.FindName('ProgressFill')
$PctLabel     = $Window.FindName('PctLabel')

$Dot1  = $Window.FindName('Dot1');  $Step1Detail = $Window.FindName('Step1Detail')
$Dot2  = $Window.FindName('Dot2');  $Step2Detail = $Window.FindName('Step2Detail')
$Dot3  = $Window.FindName('Dot3');  $Step3Detail = $Window.FindName('Step3Detail')
$Dot4  = $Window.FindName('Dot4');  $Step4Detail = $Window.FindName('Step4Detail')
$Dot5  = $Window.FindName('Dot5');  $Step5Detail = $Window.FindName('Step5Detail')

$Step2Row = $Window.FindName('Step2Row')
$Step3Row = $Window.FindName('Step3Row')
$Step4Row = $Window.FindName('Step4Row')
$Step5Row = $Window.FindName('Step5Row')

# Allow window dragging
$Window.Add_MouseDown({ if ($_.LeftButton -eq 'Pressed') { $Window.DragMove() } })

# Total bar width (account for margin: 680 - 40*2 - border = ~584)
$BAR_WIDTH = 584

# ── Helper Functions ─────────────────────────────────────────────────────────
function Update-UI {
    param([scriptblock]$Action)
    $Window.Dispatcher.Invoke([System.Windows.Threading.DispatcherPriority]::Normal, $Action)
}

function Set-Progress {
    param([int]$Pct, [string]$Status = '')
    Update-UI {
        $filled = [Math]::Max(0, [Math]::Min($BAR_WIDTH, [int]($BAR_WIDTH * $Pct / 100)))
        $ProgressFill.Width = $filled
        $PctLabel.Text = "$Pct%"
        if ($Status) { $StatusLabel.Text = $Status }
    }
}

function Activate-Step {
    param([int]$Step, [string]$Detail = '')
    Update-UI {
        $panels = @($null, $Step2Row, $Step3Row, $Step4Row, $Step5Row)
        $dots   = @($null, $Dot2, $Dot3, $Dot4, $Dot5)
        $details = @($null, $Step2Detail, $Step3Detail, $Step4Detail, $Step5Detail)
        if ($Step -ge 2 -and $Step -le 5) {
            $panels[$Step].Opacity = 1.0
            $dots[$Step].Opacity   = 1.0
            if ($Detail) { $details[$Step].Text = $Detail }
        }
    }
}

function Complete-Step {
    param([int]$Step, [string]$Detail = '')
    Update-UI {
        $dots = @($null, $Dot1, $Dot2, $Dot3, $Dot4, $Dot5)
        $details = @($null, $Step1Detail, $Step2Detail, $Step3Detail, $Step4Detail, $Step5Detail)
        $dots[$Step].Tag = 'done'
        $dots[$Step].Fill = '#16a34a'
        if ($Detail) { $details[$Step].Text = $Detail }
    }
}

function Error-Step {
    param([int]$Step, [string]$Detail)
    Update-UI {
        $dots = @($null, $Dot1, $Dot2, $Dot3, $Dot4, $Dot5)
        $details = @($null, $Step1Detail, $Step2Detail, $Step3Detail, $Step4Detail, $Step5Detail)
        $dots[$Step].Tag = 'error'
        $dots[$Step].Fill = '#dc2626'
        $details[$Step].Text = $Detail
        $StatusLabel.Text = "Installation failed. See install.log for details."
    }
}

function Write-Log {
    param([string]$Msg)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "[${ts}] $Msg" | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

# ── Find Python ───────────────────────────────────────────────────────────────
function Find-Python {
    # 1. Installed in our app dir
    $candidates = @(
        (Join-Path $PythonDir "Scripts\pythonw.exe"),
        (Join-Path $PythonDir "pythonw.exe"),
        (Join-Path $PythonDir "python.exe")
    )
    foreach ($p in $candidates) { if (Test-Path $p) { return $p } }

    # 2. System Python 3.10+
    $sysPy = @('python', 'python3', 'py') | ForEach-Object {
        try {
            $v = & $_ --version 2>&1
            if ($v -match 'Python (3\.\d+)' -and [int]$Matches[1].Split('.')[1] -ge 10) { return $_ }
        } catch {}
    }
    if ($sysPy) { return $sysPy }

    return $null
}

# ── Core Installation Routine ─────────────────────────────────────────────────
$installJob = [System.Threading.Thread]::new({
    try {
        New-Item -ItemType Directory -Force -Path $AppDir | Out-Null
        Write-Log "=== Document Studio Pro Installer v$AppVersion starting ==="
        Write-Log "Install target: $AppDir"

        # ── Step 1: Environment Check ───────────────────────────────────────
        Set-Progress -Pct 2 -Status "Checking system requirements..."
        Write-Log "Step 1: Environment check"

        try {
            $null = Invoke-WebRequest -Uri "https://pypi.org" -Method Head -UseBasicParsing -TimeoutSec 8
        } catch {
            Error-Step -Step 1 -Detail "No internet connection detected. Please connect and retry."
            Write-Log "ERROR: No internet: $_"
            return
        }
        Complete-Step -Step 1 -Detail "Internet connection confirmed."
        Set-Progress -Pct 8 -Status "Environment check passed."

        # ── Step 2: Python Runtime ──────────────────────────────────────────
        Activate-Step -Step 2 -Detail "Looking for Python 3.10+ on this machine..."
        Write-Log "Step 2: Python runtime check"

        $pythonExe = Find-Python

        if (-not $pythonExe) {
            Activate-Step -Step 2 -Detail "Python not found. Downloading Python $PYTHON_VERSION (~30 MB)..."
            Write-Log "Downloading Python from $PYTHON_INSTALLER"
            Set-Progress -Pct 12 -Status "Downloading Python $PYTHON_VERSION from python.org..."

            $pyInstPath = Join-Path $env:TEMP "python_setup_$PYTHON_VERSION.exe"
            if (-not (Test-Path $pyInstPath)) {
                $wc = [System.Net.WebClient]::new()
                $wc.DownloadProgressChanged += {
                    Set-Progress -Pct ([int](12 + $_.ProgressPercentage * 0.3)) -Status "Downloading Python... $($_.ProgressPercentage)%"
                }
                $wc.DownloadFileAsync([uri]$PYTHON_INSTALLER, $pyInstPath)
                while ($wc.IsBusy) { Start-Sleep -Milliseconds 250 }
                $wc.Dispose()
            }

            Write-Log "Installing Python silently to $PythonDir"
            Set-Progress -Pct 42 -Status "Installing Python $PYTHON_VERSION (this takes ~60 seconds)..."
            Activate-Step -Step 2 -Detail "Installing Python $PYTHON_VERSION silently..."

            $proc = Start-Process -FilePath $pyInstPath -Wait -PassThru -ArgumentList @(
                "/quiet", "InstallAllUsers=0",
                "TargetDir=`"$PythonDir`"",
                "Include_pip=1",
                "Include_launcher=0",
                "Include_test=0",
                "Include_doc=0",
                "Shortcuts=0"
            )

            if ($proc.ExitCode -ne 0) {
                Error-Step -Step 2 -Detail "Python installation failed (exit: $($proc.ExitCode))."
                Write-Log "ERROR: Python installer exited with $($proc.ExitCode)"
                return
            }

            $pythonExe = Join-Path $PythonDir "python.exe"
        }

        # Ensure pip is available
        Set-Progress -Pct 45 -Status "Verifying pip..."
        try {
            & $pythonExe -m pip --version 2>&1 | Out-Null
        } catch {
            Set-Progress -Pct 45 -Status "Bootstrapping pip..."
            $getPipPath = Join-Path $env:TEMP "get-pip.py"
            Invoke-WebRequest -Uri $GET_PIP_URL -OutFile $getPipPath -UseBasicParsing
            & $pythonExe $getPipPath --quiet
        }

        Complete-Step -Step 2 -Detail "Python runtime ready: $pythonExe"
        Write-Log "Python ready: $pythonExe"
        Set-Progress -Pct 48 -Status "Python ready."

        # ── Step 3: Install Packages ────────────────────────────────────────
        Activate-Step -Step 3 -Detail "Installing PyQt5, pypdf, PyMuPDF, pdf2docx, Pillow, ReportLab..."
        Write-Log "Step 3: pip install requirements"
        Set-Progress -Pct 50 -Status "Installing packages from requirements.txt..."

        $reqFile = Join-Path $AppDir "requirements.txt"
        Copy-Item -Path (Join-Path $ScriptDir "requirements.txt") -Destination $reqFile -Force

        # Stream pip output to parse progress
        $pipArgs   = @("-m", "pip", "install", "-r", $reqFile, "--upgrade", "--quiet")
        $psi       = [System.Diagnostics.ProcessStartInfo]::new($pythonExe)
        $psi.Arguments              = ($pipArgs -join ' ')
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError  = $true
        $psi.UseShellExecute        = $false
        $psi.CreateNoWindow         = $true

        $pipProc = [System.Diagnostics.Process]::Start($psi)
        # Packages to track (rough progress milestones)
        $pkgMilestones = @{
            'PyQt5'      = 55; 'pypdf'      = 60; 'PyMuPDF'   = 65; 'pdf2docx'  = 70;
            'Pillow'     = 74; 'reportlab'  = 78; 'qrcode'    = 81; 'python-docx' = 84;
            'docx2pdf'   = 87; 'pywin32'    = 90
        }

        while (-not $pipProc.StandardOutput.EndOfStream) {
            $line = $pipProc.StandardOutput.ReadLine()
            Write-Log "pip: $line"
            foreach ($pkg in $pkgMilestones.Keys) {
                if ($line -match $pkg) {
                    Set-Progress -Pct $pkgMilestones[$pkg] -Status "Installing $pkg..."
                    Activate-Step -Step 3 -Detail "Installed: $pkg"
                }
            }
        }
        $pipProc.WaitForExit()

        if ($pipProc.ExitCode -ne 0) {
            $errOut = $pipProc.StandardError.ReadToEnd()
            Error-Step -Step 3 -Detail "Package installation failed. Check install.log."
            Write-Log "ERROR pip: $errOut"
            return
        }

        Complete-Step -Step 3 -Detail "All packages installed successfully."
        Write-Log "Packages installed successfully."
        Set-Progress -Pct 91 -Status "Packages installed."

        # ── Step 4: Deploy Application & Shortcuts ──────────────────────────
        Activate-Step -Step 4 -Detail "Copying application files..."
        Write-Log "Step 4: Deploy and shortcut"
        Set-Progress -Pct 92 -Status "Deploying application files..."

        # Copy all source files to install dir
        $sourceFiles = @("splitter.py", "launcher.vbs", "requirements.txt", "hierarchy.ico")
        foreach ($f in $sourceFiles) {
            $src = Join-Path $ScriptDir $f
            if (Test-Path $src) {
                Copy-Item -Path $src -Destination $AppDir -Force
                Write-Log "Copied: $f"
            }
        }

        # Copy the app/ package directory (split modules)
        $appSrc = Join-Path $ScriptDir "app"
        if (Test-Path $appSrc) {
            $appDst = Join-Path $AppDir "app"
            Copy-Item -Path $appSrc -Destination $appDst -Recurse -Force
            Write-Log "Copied: app/ package directory"
        }

        # Desktop Shortcut
        $iconPath    = Join-Path $AppDir "hierarchy.ico"
        $launcherVbs = Join-Path $AppDir "launcher.vbs"
        $shortcutPath = Join-Path ([System.Environment]::GetFolderPath('Desktop')) "Document Studio Pro.lnk"
        $wshell = [System.Runtime.InteropServices.RuntimeEnvironment]::GetRuntimeDirectory()
        $shell  = New-Object -ComObject WScript.Shell
        $sc     = $shell.CreateShortcut($shortcutPath)
        $sc.TargetPath       = "wscript.exe"
        $sc.Arguments        = "`"$launcherVbs`""
        $sc.WorkingDirectory = $AppDir
        $sc.Description      = "Document Studio Pro - PDF and Document Suite"
        if (Test-Path $iconPath) { $sc.IconLocation = $iconPath }
        $sc.Save()

        # Start Menu Shortcut
        $startMenu = Join-Path ([System.Environment]::GetFolderPath('StartMenu')) "Programs"
        New-Item -ItemType Directory -Force -Path (Join-Path $startMenu "Document Studio Pro") | Out-Null
        $scMenu = $shell.CreateShortcut((Join-Path $startMenu "Document Studio Pro\Document Studio Pro.lnk"))
        $scMenu.TargetPath       = "wscript.exe"
        $scMenu.Arguments        = "`"$launcherVbs`""
        $scMenu.WorkingDirectory = $AppDir
        $scMenu.Description      = "Document Studio Pro - PDF and Document Suite"
        if (Test-Path $iconPath) { $scMenu.IconLocation = $iconPath }
        $scMenu.Save()

        Complete-Step -Step 4 -Detail "Application deployed. Desktop & Start Menu shortcuts created."
        Write-Log "Shortcuts created."
        Set-Progress -Pct 98 -Status "Shortcuts created."

        # ── Step 5: Launch ──────────────────────────────────────────────────
        Activate-Step -Step 5 -Detail "Preparing to launch Document Studio Pro..."
        Set-Progress -Pct 100 -Status "Installation complete! Launching..."
        Complete-Step -Step 5 -Detail "Document Studio Pro is ready!"
        Write-Log "Installation complete. Launching application."

        Start-Sleep -Milliseconds 1800

        $launcherExe = Join-Path $AppDir "launcher.vbs"
        Start-Process -FilePath "wscript.exe" -ArgumentList "`"$launcherExe`""

        Start-Sleep -Milliseconds 1200
        Update-UI { $Window.Close() }

    } catch {
        Write-Log "FATAL: $_"
        Update-UI {
            $StatusLabel.Text     = "Unexpected error: $_  See install.log."
            $StatusLabel.Foreground = '#dc2626'
        }
    }
})

$installJob.IsBackground = $true

# ── Start installer thread after Window is shown ──────────────────────────────
$Window.Add_Loaded({ $installJob.Start() })
$Window.ShowDialog() | Out-Null
