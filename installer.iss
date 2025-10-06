; ============================================
; Rise of Kingdoms Bot - Inno Setup Script
; ============================================

#define MyAppName "Rise of Kingdoms Bot"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "RoK Bot Development"
#define MyAppURL "https://whalebots.net/"
#define MyAppExeName "RoK_Bot.exe"
#define MyAppId "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

[Setup]
; --- Application Information ---
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; --- Installation Directory Settings ---
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; --- File Configuration ---
LicenseFile=LICENSE.txt
InfoBeforeFile=INSTALL_INFO.txt
OutputDir=installer_output
OutputBaseFilename=RoK_Bot_Setup_v{#MyAppVersion}
SetupIconFile=icon.ico

; --- Compression and Performance ---
Compression=lzma
SolidCompression=yes
LZMANumBlockThreads=4

; --- UI and Security ---
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; --- Main Application Executable ---
Source: "dist\RoK_Bot\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; --- All Supporting Files ---
Source: "dist\RoK_Bot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; --- Start Menu Shortcuts ---
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; --- Desktop Icon (Optional) ---
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; --- Quick Launch Icon (Optional, Windows 7 and earlier) ---
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; --- Post-Installation Launch Option ---
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  BlueStacksInstalled: Boolean;
begin
  Result := True;

  ; // Check for BlueStacks installation in common registry locations
  BlueStacksInstalled :=
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\BlueStacks_nxt') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\BlueStacks') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\BlueStacks_nxt') or
    RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\WOW6432Node\BlueStacks');

  if not BlueStacksInstalled then
  begin
    if MsgBox(
      'BlueStacks does not appear to be installed on your system.' + #13#10#13#10 +
      'This application requires BlueStacks to function properly.' + #13#10#13#10 +
      'Do you want to continue the installation anyway?',
      mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LogsDir, TemplatesDir: string;
begin
  if CurStep = ssPostInstall then
  begin
    ; // Create necessary directories
    LogsDir := ExpandConstant('{app}\logs');
    TemplatesDir := ExpandConstant('{app}\templates');

    if not DirExists(LogsDir) then
      CreateDir(LogsDir);

    if not DirExists(TemplatesDir) then
      CreateDir(TemplatesDir);

    ; // Show completion message
    MsgBox(
      'Installation completed successfully!' + #13#10#13#10 +
      'Important Notes:' + #13#10 +
      '• Ensure BlueStacks is running before launching the bot.' + #13#10 +
      '• ADB debugging must be enabled in BlueStacks.' + #13#10 +
      '• A valid license key is required to use the bot.' + #13#10#13#10 +
      'For setup instructions, please refer to the documentation.',
      mbInformation, MB_OK);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  ; // Additional validation on directory selection page
  if CurPageID = wpSelectDir then
  begin
    if not IsAdminInstallMode then
    begin
      MsgBox(
        'Warning: You are installing to a directory that may require administrator privileges.' + #13#10#13#10 +
        'If you encounter permission issues, consider:' + #13#10 +
        '• Installing to a user directory (e.g., Documents)' + #13#10 +
        '• Running the installer as Administrator.',
        mbInformation, MB_OK);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserResponse: Integer;
  LogsDirectory: string;
begin
  case CurUninstallStep of
    usUninstall:
      begin
        UserResponse := MsgBox(
          'Do you want to delete all logs and configuration files?' + #13#10#13#10 +
          'This will remove:' + #13#10 +
          '• All log files' + #13#10 +
          '• License key file' + #13#10 +
          '• Configuration settings' + #13#10#13#10 +
          'Select "Yes" to remove all data, or "No" to keep it.',
          mbConfirmation, MB_YESNO or MB_DEFBUTTON2);

        if UserResponse = IDYES then
        begin
          LogsDirectory := ExpandConstant('{app}\logs');
          if DirExists(LogsDirectory) then
            DelTree(LogsDirectory, True, True, True);

          ; // Delete individual configuration files
          DeleteFile(ExpandConstant('{app}\license.key'));
          DeleteFile(ExpandConstant('{app}\config.ini'));
          DeleteFile(ExpandConstant('{app}\settings.json'));
        end;
      end;
  end;
end;

[Registry]
; --- Uninstall Registry Cleanup ---
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppId}_is1"; Flags: uninsdeletekey

[UninstallDelete]
; --- Cleanup of temporary and cache files during uninstall ---
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.pyc"
Type: files; Name: "{app}\*.tmp"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\*.egg-info"
