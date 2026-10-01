; 记账本 · 安装包配方
; 用 Inno Setup 编译： ISCC.exe 安装包.iss

#define MyAppName "记账本"
#define MyAppVersion "1.0"
#define MyAppExeName "记账本.exe"
#define SourceDir "D:\记账本"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=记账本_安装包
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinese"; MessagesFile: "ChineseSimplified.isl"

[Files]
; ⚠️ 只带程序本体和界面。
; 源码 / data（你的账）/ .git / 备份 / preview —— 一个都不带。
Source: "{#SourceDir}\记账本.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单 + 桌面
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
; 装完问一句"要不要现在打开"
Filename: "{app}\{#MyAppExeName}"; Description: "立即打开记账本"; Flags: nowait postinstall skipifsilent
