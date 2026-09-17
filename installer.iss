#ifndef MyAppVersion
  #define MyAppVersion "0.2.0"
#endif

[Setup]
AppId=PresenceCoachDesktop
AppName=Presence Coach
AppVersion={#MyAppVersion}
AppPublisher=Presence Coach
AppPublisherURL=https://github.com/agilecoach-ashutosh/executive-coach-app
AppSupportURL=https://github.com/agilecoach-ashutosh/executive-coach-app/issues
AppUpdatesURL=https://github.com/agilecoach-ashutosh/executive-coach-app/releases
DefaultDirName={localappdata}\Programs\PresenceCoach
DefaultGroupName=Presence Coach
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=Presence-Coach-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
SetupIconFile=Presence-Coach.ico
UninstallDisplayIcon={app}\PresenceCoach.exe
CloseApplications=yes
RestartApplications=no

[Files]
Source: "dist\PresenceCoach\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Presence Coach"; Filename: "{app}\PresenceCoach.exe"; IconFilename: "{app}\PresenceCoach.exe"
Name: "{autodesktop}\Presence Coach"; Filename: "{app}\PresenceCoach.exe"; IconFilename: "{app}\PresenceCoach.exe"

[Run]
Filename: "{app}\PresenceCoach.exe"; Description: "Open Presence Coach"; Flags: nowait postinstall skipifsilent
