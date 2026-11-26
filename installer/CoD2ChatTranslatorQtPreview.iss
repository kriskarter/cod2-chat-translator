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
[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

[Code]
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
