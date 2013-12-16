* http://www.connectionstrings.com/
* natvrdo c:\ramovani\data - p¯ÌpadnÏ vyedituj
* (zde nepouûito, ale:) chci-li na 64b. maöinÏ vytv·¯et DSN, musÌm pustit Odbcad32.exe z %systemdrive%\Windows\SysWoW64, jinak nevidÌm 32b. ovladaËe

CLEAR ALL
SET SAFETY OFF

hnd=SQLSTRINGCONNECT("Driver={Microsoft Paradox Driver (*.db )};DriverID=538;Fil=Paradox 5.X;DefaultDir=c:\ramovani\data;Dbq=c:\ramovani\data;CollatingSequence=ASCII;")
SQLEXEC(hnd,'SELECT * FROM Listy')
COPY TO c:\ramovani\data\fox\listy
SQLDISCONNECT(hnd)

use c:\ramovani\data\fox\listy

REPLACE ALL TYP WITH STRTRAN(Typ,'oevo','¯evo')

REPLACE ALL Nazev WITH PROPER(Nazev)
REPLACE ALL Nazev WITH STRTRAN(Nazev,'x',' x ') FOR 'x'$LOWER(nazev) AND NOT 'lox'$LOWER(nazev)
REPLACE ALL Nazev WITH STRTRAN(Nazev,'X',' x ') FOR 'x'$LOWER(nazev) AND NOT 'lox'$LOWER(nazev)
REPLACE ALL Nazev WITH STRTRAN(Nazev,'  ',' ')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'  ',' ')

REPLACE ALL Nazev WITH STRTRAN(Nazev,'oech','¯ech')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'aoÌû','a¯Ìû')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'toÌbro','t¯Ìbro')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'lu?','luù')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'omerane','omeranË')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'kooic','ko¯ic')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'oÌrod','¯Ìrod')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'eer','Ëer')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'toÌbr','t¯Ìbr')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'mavi','mavÏ')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'vitl','vÏtl')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'palÌeek','palÌËek')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'oen','oËn')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'Modo','Mod¯')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'modo','mod¯')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'ostiek','ostiËk')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'ovi ','ovÏ ')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'oevin','¯evÏn')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'niton','nit¯n')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'˝minn','˝mÏnn')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'ilen','Ïlen')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'toÌr','t¯Ìbr')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'oev','¯ev')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'oeöeo','¯eöeÚ')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'7eero','7 »erÚ')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'Eer','»er')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'hnid','hnÏd')
REPLACE ALL Nazev WITH STRTRAN(Nazev,'Hnid','HnÏd')
