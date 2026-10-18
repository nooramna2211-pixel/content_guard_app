#define MyAppName "Content Guard"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Content Guard"
#define MyAppExeName "ContentGuard.exe"

[Setup]
AppId={{B9D1EDC5-24D3-4A7C-AC82-B89450DC9308}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Content Guard
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=ContentGuard-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
Uninstallable=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "Start Content Guard when I sign in to Windows"; GroupDescription: "Optional startup:"; Flags: unchecked
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Dirs]
Name: "{localappdata}\Content Guard"; Permissions: users-modify

[Files]
Source: "..\dist\ContentGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\extension\*"; DestDir: "{app}\extension"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README_ANDROID.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\index.html"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Content Guard"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Content Guard"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\Content Guard"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Start Content Guard"; Flags: postinstall nowait skipifsilent
