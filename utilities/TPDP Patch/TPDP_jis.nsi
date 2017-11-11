;TPDP.nsi
;Installer for the English patch of Touhoumon Puppet Dance Performance
;Script Ver 1.1 - Jan 1 2016
;Modified: Ver 1.1 Jan 14 2016 - Fixed installer appending "幻想人形演舞" to
;				to install directory.
;-----------------------------------------------------------------------------

!include "Sections.nsh"
!include "MUI2.nsh"

;-----------------------------------------------------------------------------
;Names
;-----------------------------------------------------------------------------

!define CompanyName "Touhou Puppet Play Community"
!define GameName "TPDP Shard of Dreams"
!define JPGameName "Gensou Ningyou Enbu Yume no Kakera"
!define GameVersion "1.103"
!define PatcherName "${GameName} Interface Translation R2"
;Name of the application (appears in the title bar)
Name "${PatcherName}"
;Name of the patcher
OutFile "YNK_Interface_Patch_R2.exe"

;-----------------------------------------------------------------------------
;Configurations
;-----------------------------------------------------------------------------
; Compression type
SetCompressor /SOLID lzma
;Default installation directory
InstallDir "C:\game\FocasLens\幻想人形演舞-ユメノカケラ-\"
;Privilege level
RequestExecutionLevel admin

;-----------------------------------------------------------------------------
;MUI Images
;-----------------------------------------------------------------------------
!define MUI_ICON "patch.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
;!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${ImageDir}\welcome.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_HEADERIMAGE_RIGHT


;-----------------------------------------------------------------------------
;Pages
;-----------------------------------------------------------------------------
!insertmacro MUI_PAGE_WELCOME
	!define MUI_TEXT_WELCOME_INFO_TITLE "${PatcherName} Installer"
	!define MUI_TEXT_WELCOME_INFO_TEXT "Welcome to the ${PatcherName}.$\n$\nPlease ensure that you have backed up your files before continuing. Best results for patch installation can be obtained by running this patcher while in JP locale."
!insertmacro MUI_PAGE_LICENSE License.txt
;!insertmacro MUI_PAGE_COMPONENTS	
!define  MUI_DIRECTORYPAGE_TEXT_DESTINATION ""
!define MUI_DIRECTORYPAGE_TEXT_TOP "Please select the location of your Japanese ${JPGameName} installation."
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TITLE_3LINES
!insertmacro MUI_PAGE_FINISH


;-----------------------------------------------------------------------------
;Language - This must go after previous MUI defines
;-----------------------------------------------------------------------------
!insertmacro MUI_LANGUAGE "English"

;-----------------------------------------------------------------------------
;Installer Sections
;-----------------------------------------------------------------------------
;TPDP English Files
!define ERROR_FILES "Files not found. Please select the correct directory and try again."
Section "${GameName} Files" SectionFiles
	SectionIn RO
	IfFileExists $INSTDIR\幻想人形演舞-ユメノカケラ-.exe +3 0 ;Fuckin GOTOs man...
	MessageBox MB_OK "${ERROR_FILES}"
	Abort
	IfFileExists $INSTDIR\dat\gn_dat1.arc +3 0
	MessageBox MB_OK "${ERROR_FILES}"
	Abort
	IfFileExists $INSTDIR\dat\gn_dat5.arc +3 0
	MessageBox MB_OK "${ERROR_FILES}"
	Abort
	IfFileExists $INSTDIR\dat\gn_dat6.arc +3 0
	MessageBox MB_OK "${ERROR_FILES}"
	Abort
	;Set output path to the installation directory
	SetOutPath $INSTDIR		
	Rename 幻想人形演舞-ユメノカケラ-.exe 幻想人形演舞-ユメノカケラ-.exe.bak
	File 幻想人形演舞-ユメノカケラ-.exe
	SetOutPath $INSTDIR\dat	
	Rename gn_dat1.arc gn_dat1.arc.bak
	Rename gn_dat5.arc gn_dat5.arc.bak
	Rename gn_dat6.arc gn_dat6.arc.bak
	File dat\gn_dat1.arc
	File dat\gn_dat5.arc
	File dat\gn_dat6.arc	
SectionEnd

;Section descriptions
LangString DESC_SectionFiles ${LANG_ENGLISH} "The English translated files."
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SectionFiles} $(DESC_SectionFiles)
!insertmacro MUI_FUNCTION_DESCRIPTION_END



;-----------------------------------------------------------------------------
