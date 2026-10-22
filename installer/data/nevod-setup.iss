; Inno Setup script for the Nevod node installer (M2).
; Bundles the two PyInstaller-built exes (nevod-gui.exe, nevod-node.exe —
; build both from installer/data/nevod-gui.spec and nevod-node.spec first)
; into a single setup.exe.
;
; Build (after building both exes into installer/dist/):
;   "C:\Users\<you>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" installer\data\nevod-setup.iss
; Produces: installer/dist/nevod-setup.exe

#define MyAppName "Nevod"
#define MyAppVersion "1.0"
#define MyAppPublisher "Nevod"

[Setup]
AppId={{5BAB1CA0-034A-4E64-BB78-01D31F628B81}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Per-user install, no admin/UAC prompt — matches installer/autostart.py's
; own per-user (HKCU) philosophy, consistent with the "no technical
; knowledge required" goal of the whole installer.
DefaultDirName={localappdata}\Programs\Nevod
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist
OutputBaseFilename=nevod-setup
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\nevod-gui.exe
WizardStyle=modern

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\nevod-gui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\nevod-node.exe"; DestDir: "{app}"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
Name: "{group}\Nevod"; Filename: "{app}\nevod-gui.exe"
Name: "{group}\{cm:UninstallProgram,Nevod}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Nevod"; Filename: "{app}\nevod-gui.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\nevod-gui.exe"; Description: "{cm:LaunchProgram,Nevod}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Runs BEFORE Inno removes the files (default UninstallRun timing) — stops
; the still-running background node, disables autostart, and deletes
; node.json/node.db/admin.json/node.pid from the app-data dir, none of
; which live under {app} and so wouldn't be touched by file removal alone.
Filename: "{app}\nevod-gui.exe"; Parameters: "--uninstall-cleanup"; Flags: runhidden waituntilterminated; RunOnceId: "NevodCleanup"
