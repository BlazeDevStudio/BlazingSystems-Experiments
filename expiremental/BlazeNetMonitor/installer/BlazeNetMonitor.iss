; BlazeNetMonitor v1.0.0 — native Windows setup.
; User-facing support is optional. Recipient is the owner's fixed PayPal QR,
; rendered by the application during CI from its verified immutable QR data.
; Installer is x64 and includes the self-contained .NET desktop runtime.

#define AppName "BlazeNetMonitor"
#define AppVersion "1.0.0"
#define AppExe "BlazeNetMonitor.exe"

[Setup]
AppId=BlazeSystems.BlazeNetMonitor.Windows
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName=BlazeNetMonitor 1.0.0
AppPublisher=Blaze Systems
AppPublisherURL=https://fb.me/manrealloumer
AppSupportURL=https://fb.me/manrealloumer
DefaultDirName={autopf}\Blaze Systems\BlazeNetMonitor
DefaultGroupName=BlazeNetMonitor
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=..\artifacts
OutputBaseFilename=BlazeNetMonitor-Setup-v1.0.0
SetupIconFile=..\src\BlazeNetMonitor\Assets\BlazeNetMonitor.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
AppMutex=Local\BlazeSystems.BlazeNetMonitor
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes
MinVersion=10.0
VersionInfoVersion=1.0.0.0
VersionInfoDescription=BlazeNetMonitor Windows installer
VersionInfoCompany=Blaze Systems
ChangesAssociations=no
UsePreviousAppDir=yes

[Files]
Source: "..\dist\win-x64\BlazeNetMonitor.exe"; DestDir: "{app}"; Flags: ignoreversion
; Displayed in the setup wizard but not installed as a replaceable payment file.
Source: "..\dist\support-qr.bmp"; Flags: dontcopy

[Icons]
Name: "{group}\BlazeNetMonitor"; Filename: "{app}\BlazeNetMonitor.exe"; WorkingDir: "{app}"
Name: "{commondesktop}\BlazeNetMonitor"; Filename: "{app}\BlazeNetMonitor.exe"; WorkingDir: "{app}"
; Startup folder fallback. If another startup method launches the process,
; --startup exits silently when the application's named mutex already exists.
Name: "{commonstartup}\BlazeNetMonitor"; Filename: "{app}\BlazeNetMonitor.exe"; Parameters: "--startup"; WorkingDir: "{app}"
Name: "{group}\Uninstall BlazeNetMonitor"; Filename: "{uninstallexe}"

[Code]
var
  SupportPage: TWizardPage;
  SupportQr: TBitmapImage;
  SupportTitle: TNewStaticText;
  SupportDescription: TNewStaticText;
  DeleteInstallerCheck: TNewCheckBox;

procedure InitializeWizard;
begin
  SupportPage := CreateCustomPage(
    wpWelcome,
    'Support BlazeNetMonitor',
    'Optional support for future updates.');

  ExtractTemporaryFile('support-qr.bmp');
  SupportQr := TBitmapImage.Create(SupportPage);
  SupportQr.Parent := SupportPage.Surface;
  SupportQr.Left := ScaleX(8);
  SupportQr.Top := ScaleY(13);
  SupportQr.Width := ScaleX(210);
  SupportQr.Height := ScaleY(210);
  SupportQr.Stretch := True;
  SupportQr.Bitmap.LoadFromFile(ExpandConstant('{tmp}\support-qr.bmp'));

  SupportTitle := TNewStaticText.Create(SupportPage);
  SupportTitle.Parent := SupportPage.Surface;
  SupportTitle.Left := ScaleX(235);
  SupportTitle.Top := ScaleY(29);
  SupportTitle.Width := SupportPage.SurfaceWidth - SupportTitle.Left - ScaleX(10);
  SupportTitle.Height := ScaleY(54);
  SupportTitle.WordWrap := True;
  SupportTitle.Caption := 'Support BlazeNetMonitor';

  SupportDescription := TNewStaticText.Create(SupportPage);
  SupportDescription.Parent := SupportPage.Surface;
  SupportDescription.Left := ScaleX(235);
  SupportDescription.Top := ScaleY(87);
  SupportDescription.Width := SupportPage.SurfaceWidth - SupportDescription.Left - ScaleX(10);
  SupportDescription.Height := ScaleY(122);
  SupportDescription.WordWrap := True;
  SupportDescription.Caption :=
    'Scan to support future development.' + #13#10 + #13#10 +
    'Any amount is appreciated.' + #13#10 + #13#10 +
    'PayPal: Loumer Cabaluna Manreal' + #13#10 + #13#10 +
    'Click Next to install.';

  DeleteInstallerCheck := TNewCheckBox.Create(WizardForm.FinishedPage);
  DeleteInstallerCheck.Parent := WizardForm.FinishedPage;
  DeleteInstallerCheck.Left := WizardForm.FinishedLabel.Left;
  DeleteInstallerCheck.Top := WizardForm.FinishedPage.ClientHeight - ScaleY(70);
  DeleteInstallerCheck.Width := WizardForm.FinishedPage.ClientWidth - DeleteInstallerCheck.Left - ScaleX(12);
  DeleteInstallerCheck.Height := ScaleY(25);
  DeleteInstallerCheck.Caption := 'Delete the installer file after setup';
  DeleteInstallerCheck.Checked := False;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    WizardForm.FinishedHeadingLabel.Caption := 'Thank you!';
    WizardForm.FinishedLabel.Caption :=
      'BlazeNetMonitor 1.0.0 has been installed.' + #13#10 + #13#10 +
      'The app is available in the Start menu and on your desktop.' + #13#10 +
      'It will also start when you sign in to Windows.' + #13#10 + #13#10 +
      'Finishing setup will open fb.me/manrealloumer.';
  end;
end;

procedure QueueDeleteInstaller;
var
  Source, ScriptName, Cmd, Contents: String;
  ResultCode: Integer;
begin
  Source := ExpandConstant('{srcexe}');
  if CompareText(ExtractFileName(Source), 'BlazeNetMonitor-Setup-v1.0.0.exe') <> 0 then
  begin
    Log('Self-delete skipped: unexpected installer file name');
    Exit;
  end;

  ScriptName := ExpandConstant('{tmp}\BlazeNetMonitor-self-cleanup.cmd');
  Contents :=
    '@echo off' + #13#10 +
    'for /L %%I in (1,1,25) do (' + #13#10 +
    '  timeout /t 1 /nobreak >nul' + #13#10 +
    '  del /f /q "' + Source + '" >nul 2>&1' + #13#10 +
    '  if not exist "' + Source + '" goto done' + #13#10 +
    ')' + #13#10 +
    ':done' + #13#10 +
    'del /q "%~f0" >nul 2>&1' + #13#10;
  if not SaveStringToFile(ScriptName, Contents, False) then
  begin
    Log('Self-delete helper could not be written');
    Exit;
  end;
  Cmd := '/C ""' + ScriptName + '""';
  if not Exec(ExpandConstant('{cmd}'), Cmd, '', SW_HIDE, ewNoWait, ResultCode) then
    Log('Could not schedule optional installer file deletion');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ErrorCode: Integer;
begin
  if (CurStep <> ssDone) or WizardSilent then Exit;
  // Open browser only after successful Finish, as the installing user.
  if not ShellExecAsOriginalUser('open',
    'https://fb.me/manrealloumer', '', '', SW_SHOWNORMAL, ewNoWait, ErrorCode) then
    Log('Could not open creator Facebook page');

  // Then launch the installed app under the user's normal credentials, not elevated.
  // Its owner QR splash appears separately.
  if not ExecAsOriginalUser(
    ExpandConstant('{app}\BlazeNetMonitor.exe'), '', ExpandConstant('{app}'),
    SW_SHOWNORMAL, ewNoWait, ErrorCode) then
    Log('Automatic first launch failed; use the Start menu shortcut');

  if DeleteInstallerCheck.Checked then QueueDeleteInstaller;
end;
