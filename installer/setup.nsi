; Digital Signature Agent Installer
Unicode true
Name "Digital Signature Agent"
OutFile "DigitalSignatureAgent_Setup.exe"
InstallDir "$PROGRAMFILES\Digital Signature Agent"
RequestExecutionLevel admin

; Modern UI
!include MUI2.nsh

; Icons
!define MUI_ICON "..\common\images\logo_icon.ico"
!define MUI_UNICON "..\common\images\logo_icon.ico"

; Interface settings
!define MUI_ABORTWARNING

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY

; Desktop Shortcut Page
!define MUI_FINISHPAGE_SHOWREADME
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcut

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

Function CreateDesktopShortcut
  CreateShortcut "$DESKTOP\Digital Signature Agent.lnk" "$INSTDIR\DigitalSignatureAgent.exe"
FunctionEnd

Section "Main Application" SecMain
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Main executable
    File "..\dist\DigitalSignatureAgent.exe"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Start menu shortcuts
    CreateDirectory "$SMPROGRAMS\Digital Signature Agent"
    CreateShortcut "$SMPROGRAMS\Digital Signature Agent\Digital Signature Agent.lnk" "$INSTDIR\DigitalSignatureAgent.exe"
    CreateShortcut "$SMPROGRAMS\Digital Signature Agent\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
    ; Registry information for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalSignatureAgent" \
        "DisplayName" "Digital Signature Agent"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalSignatureAgent" \
        "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalSignatureAgent" \
        "DisplayIcon" "$INSTDIR\DigitalSignatureAgent.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalSignatureAgent" \
        "Publisher" "Your Company"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalSignatureAgent" \
        "DisplayVersion" "1.0.0"
    
SectionEnd

Section "Uninstall"
    ; Remove shortcuts
    Delete "$SMPROGRAMS\Digital Signature Agent\Digital Signature Agent.lnk"
    Delete "$SMPROGRAMS\Digital Signature Agent\Uninstall.lnk"
    RMDir "$SMPROGRAMS\Digital Signature Agent"
    
    ; Remove desktop shortcut
    Delete "$DESKTOP\Digital Signature Agent.lnk"
    
    ; Remove files
    Delete "$INSTDIR\DigitalSignatureAgent.exe"
    Delete "$INSTDIR\Uninstall.exe"
    
    ; Remove installation directory
    RMDir "$INSTDIR"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\DigitalSignatureAgent"
    
SectionEnd