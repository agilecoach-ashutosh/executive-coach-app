[Setup]
AppId=PresenceCoachDesktop
AppName=Presence Coach
AppVersion=0.1.0
DefaultDirName={localappdata}\Programs\PresenceCoach
DefaultGroupName=Presence Coach
PrivilegesRequired=lowest
OutputDir=installer-output
OutputBaseFilename=Presence-Coach-Setup-0.1.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
[Files]
Source: "dist\PresenceCoach\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Presence Coach"; Filename: "{app}\PresenceCoach.exe"
Name: "{autodesktop}\Presence Coach"; Filename: "{app}\PresenceCoach.exe"
[Run]
Filename: "{app}\PresenceCoach.exe"; Description: "Open Presence Coach"; Flags: nowait postinstall skipifsilent
