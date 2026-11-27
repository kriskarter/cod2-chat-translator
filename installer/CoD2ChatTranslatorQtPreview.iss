#define MyAppName "CoD2 Chat Translator Qt Preview"
#define MyAppVersion "1.22.0"
#define MyAppExeName "CoD2ChatTranslatorQt.exe"
[Setup]
AppId={{D6A4A2EF-73A2-4D25-9E38-2B85188A09D9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=kriskarter
DefaultDirName={localappdata}\Programs\CoD2ChatTranslatorQtPreview
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
CloseApplications=no
RestartApplications=no
OutputDir=..\release-qt
OutputBaseFilename=CoD2ChatTranslator_QtPreview_Setup
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
DisableDirPage=no
WizardImageFile=qt-wizard\welcome1.bmp,qt-wizard\welcome2.bmp
WizardSmallImageFile=qt-wizard\icon1.bmp,qt-wizard\icon2.bmp
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"
[Files]
Source: "..\dist\CoD2ChatTranslatorQt\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\COPYRIGHT.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\QT_THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\qt_licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "..\qt_dependency_inventory.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Check: WantsDesktop
[UninstallDelete]
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent runasoriginaluser

[Code]
var DesktopChoice: TNewCheckBox;

function WantsDesktop: Boolean;
var Saved: Cardinal;
begin
  Result := True;
  if RegQueryDWordValue(HKCU, 'Software\kriskarter\CoD2ChatTranslatorQtPreview', 'DesktopShortcut', Saved) then
    Result := Saved <> 0;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    DesktopChoice := TNewCheckBox.Create(WizardForm);
    DesktopChoice.Parent := WizardForm.FinishedPage;
    DesktopChoice.Caption := ExpandConstant('{cm:CreateDesktopIcon}');
    DesktopChoice.Left := WizardForm.RunList.Left;
    DesktopChoice.Top := WizardForm.RunList.Top;
    DesktopChoice.Width := WizardForm.RunList.Width;
    DesktopChoice.Height := ScaleY(22);
    DesktopChoice.Checked := WantsDesktop;
    WizardForm.RunList.Height := WizardForm.RunList.Height - DesktopChoice.Height;
    WizardForm.RunList.Top := DesktopChoice.Top + DesktopChoice.Height;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var Link: String;
begin
  Result := True;
  if (CurPageID = wpFinished) and Assigned(DesktopChoice) then
  begin
    Link := ExpandConstant('{autodesktop}\{#MyAppName}.lnk');
    if DesktopChoice.Checked then
      CreateShellLink(Link, '{#MyAppName}', ExpandConstant('{app}\{#MyAppExeName}'), '', ExpandConstant('{app}'), '', 0, SW_SHOWNORMAL)
    else if FileExists(Link) then DeleteFile(Link);
    RegWriteDWordValue(HKCU, 'Software\kriskarter\CoD2ChatTranslatorQtPreview', 'DesktopShortcut', Ord(DesktopChoice.Checked));
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsDir, LangFile, LangCode: String;
begin
  if CurStep = ssPostInstall then
  begin
    SettingsDir := ExpandConstant('{userappdata}\CoD2ChatTranslatorQtPreview');
    ForceDirectories(SettingsDir);
    LangFile := SettingsDir + '\ui_language.txt';
    if (not FileExists(LangFile)) and (not FileExists(SettingsDir + '\qt_settings.json')) then
    begin
      if ActiveLanguage = 'russian' then LangCode := 'ru'
      else if ActiveLanguage = 'ukrainian' then LangCode := 'uk'
      else LangCode := 'en';
      SaveStringToFile(LangFile, LangCode, False);
    end;
  end;
end;
