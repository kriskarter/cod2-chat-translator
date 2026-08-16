#define MyAppName "CoD2 Chat Translator"
#ifndef MyAppVersion
  #define MyAppVersion "1.11.1"
#endif
#define MyAppPublisher "kriskarter"
#define MyAppPublisherURL "https://github.com/kriskarter"
#define MyAppExeName "CoD2ChatTranslator.exe"

[Setup]
AppId={{4C1FBC79-15D6-4C54-9F76-62C2FEC6BC3A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppPublisherURL}
AppSupportURL={#MyAppPublisherURL}
DefaultDirName={localappdata}\Programs\CoD2ChatTranslator
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=CoD2ChatTranslator_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
WizardImageFile=..\assets\wizard.bmp
WizardSmallImageFile=..\assets\wizard_small.bmp
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
VersionInfoVersion={#MyAppVersion}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoDescription=Real-time Call of Duty 2 chat translator
VersionInfoCompany={#MyAppPublisher}
AppComments=Developed by kriskarter for the Call of Duty 2 community

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
english.DesktopIcon=Create a desktop shortcut
russian.DesktopIcon=Создать ярлык на рабочем столе
english.LaunchAfter=Launch CoD2 Chat Translator
russian.LaunchAfter=Запустить CoD2 Chat Translator

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\CoD2ChatTranslator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\CoD2ChatTranslatorUpdater.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\release_config.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchAfter}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  SettingsDir, LangFile, ConfigFile, LangCode: String;
begin
  if CurStep = ssPostInstall then
  begin
    SettingsDir := ExpandConstant('{userappdata}\CoD2ChatTranslator');
    ForceDirectories(SettingsDir);
    LangFile := SettingsDir + '\ui_language.txt';
    ConfigFile := SettingsDir + '\config.json';
    if (not FileExists(LangFile)) and (not FileExists(ConfigFile)) then
    begin
      if ActiveLanguage = 'russian' then
        LangCode := 'ru'
      else
        LangCode := 'en';
      SaveStringToFile(LangFile, LangCode, False);
    end;
  end;
end;
