#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{8F5C3B9D-9E42-4B7A-9C35-48E72A6D1D3B}
AppName=Labelme
AppVersion={#AppVersion}
AppVerName=Labelme {#AppVersion}
AppPublisher=Labelme Project
AppPublisherURL=https://github.com/phanhai27/labelme
AppSupportURL=https://github.com/phanhai27/labelme/issues
DefaultDirName={autopf}\Labelme
DefaultGroupName=Labelme
AllowNoIcons=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\..\dist
OutputBaseFilename=Labelme-Windows-Setup-x64
SetupIconFile=..\..\labelme\icons\icon.ico
UninstallDisplayIcon={app}\Labelme.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\Labelme\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Labelme"; Filename: "{app}\Labelme.exe"; IconFilename: "{app}\Labelme.exe"
Name: "{group}\{cm:UninstallProgram,Labelme}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Labelme"; Filename: "{app}\Labelme.exe"; Tasks: desktopicon; IconFilename: "{app}\Labelme.exe"

[Run]
Filename: "{app}\Labelme.exe"; Description: "{cm:LaunchProgram,Labelme}"; Flags: nowait postinstall skipifsilent
