# Wildcard26_Readme_http

WildCard26 Mint 21 README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure. You are being introduced to new
infrastructure within E-Corp, and must harden it to the best of your ability.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. Please reset
any insecure passwords with a new temporary password of your choice and ensure that it must be changed
the next time the user logs in. The presence of any non-work related media files and "hacking tools" on any
computers is strictly prohibited. This company currently does not use any centralized maintenance or polling
tools to manage their IT equipment. This computer is for official business use only by authorized users. Your
job is to secure this computer, within the guidelines of the scenario, while ensuring the availability of
authorized business critical software and services.
Mint 21
It is company policy to use only Mint 21 on this computer. It is also company policy to use only the latest,
official, stable Mint 21 packages available for required software and services on this computer. The display
manager should remain set to LightDM.
Management has decided that the default web browser for all users on this computer should be the latest
stable version of Chromium. Employees must also have access to the latest stable versions of CherryTree,
Stellarium, and LibreOffice. The only company approved firewall for this computer is UFW. Company policy is
to never let users log in as root. If administrators need to run commands as root, they are required to use the
"sudo" command.
Due to a recent security breach, management has requested that you install the Auditd service to allow for
better system auditing. Please install the Auditd service at your earliest convienence and make sure it is
enabled and running. Management has also requested that Auditd be configured to collect system
administrator actions. Please add rules to watch the "/etc/sudoers" file and "/etc/sudoers.d/" directory.
After the recent security breach, the company has migrated the web application formerly located on this
system to the Windows 11 machine. Apache and MariaDB have been placed in two Docker honeypots on this
machine, named "apache" and "mariadb". The database is running at 172.18.0.2, and can be accessed with
the credentials "root:3Corp3x3cutive". The E-Corp directory application is located in the "/webapp" directory
and running at http://172.18.0.3/.
The Docker daemon is running as root and should not be run in "rootless" mode. Only authorized
administrators should be able to control the Docker daemon. Please do not change the container names,
container images, IP address, port, or MariaDB root password. You must keep all containers running and
accessible. Please do not make any changes to the web application code or database, however you may make
minimal changes to the container image configuration when instructed.
Critical Services:
Docker (docker)
Authorized Administrators and Users
Authorized Administrators:
twellick (you)
 password: 3Corp3x3cutive
jplofe
 password: AuditM4n@g3r
pmccleery
 password: root
wbraddock
 password: NetworkB0ss
ealderson
 password: samsep10l
lchong
 password: t3chn1t!on
sswailem
 password: data
Authorized Users:
pprice
sknowles
tcolby
jchutney
sweinsberg
sjacobs
lspencer
mralbern
jrobinson
gsheldern
coshearn
jlaslen
kshelvern
jtholdon
belkarn
bharper
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
WildCard26 Ubuntu 22.04_A README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. The presence
of any non-work related media files and "hacking tools" on any computers is strictly prohibited. This company
currently does not use any centralized maintenance or polling tools to manage their IT equipment. This
computer is for official business use only by authorized users. Your job is to secure this computer, within the
guidelines of the scenario, while ensuring the availability of authorized business critical software and services.
Ubuntu 22.04
It is company policy to use only Ubuntu 22.04 on this computer. It is also company policy to use only the
latest, official, stable Ubuntu 22.04 packages available for required software and services on this computer.
The display manager should remain set to GDM3.
Management has decided that the default web browser for all users on this computer should be the latest
stable version of Google Chrome. The only company approved firewall for this computer is UFW. Company
policy is to never let users log in as root. If administrators need to run commands as root, they are required to
use the "sudo" command.
All authorized users must be able to log in remotely using SSH. Therefore, sshd is a critical service and needs
to remain enabled.
All authorized users should be able to log in to the FTP server located at "/srv/ftp". The only FTP service that
has been approved for use on this computer is the VSFTP daemon. Please ensure this FTP server is configured
securely.
Critical Services:
OpenSSH server (sshd)
FTP server (vsftpd)
Authorized Administrators and Users
Authorized Administrators:
ealderson (you)
 password: samsep10l
ggoddard
 password: all$af3FA
lchong
 password: t3chn1t!on
oparker
 password: 123456Seven
Authorized Users:
cmoss
twellick
pprice
hdavis
sswailem
anayar
tcolby
dalderson
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
WildCard26 Ubuntu 22.04_B README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. The presence
of any non-work related media files and "hacking tools" on any computers is strictly prohibited. This company
currently does not use any centralized maintenance or polling tools to manage their IT equipment. This
computer is for official business use only by authorized users. Your job is to secure this computer, within the
guidelines of the scenario, while ensuring the availability of authorized business critical software and services.
Ubuntu 22.04
It is company policy to use only Ubuntu 22.04 on this computer. It is also company policy to use only the
latest, official, stable Ubuntu 22.04 packages available for required software and services on this computer.
The display manager should remain set to GDM3.
Management has decided that the default web browser for all users on this computer should be the latest
stable version of Google Chrome. The only company approved firewall for this computer is UFW. Company
policy is to never let users log in as root. If administrators need to run commands as root, they are required to
use the "sudo" command.
E-Corp requires Squid proxy server to support their business operations. Please ensure that the Squid proxy
server is configured securely.
Critical Services:
Squid proxy server (squid)
Authorized Administrators and Users
Authorized Administrators:
ealderson (you)
 password: samsep10l
ggoddard
 password: all$af3FA
lchong
 password: t3chn1t!on
oparker
 password: 123456Seven
Authorized Users:
cmoss
twellick
pprice
hdavis
sswailem
anayar
tcolby
dalderson
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
WildCard26 Windows 10 README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. The presence
of any non-work related media files and "hacking tools" on any computers is strictly prohibited. This company
currently does not use any centralized maintenance or polling tools to manage their IT equipment. This
computer is for official business use only by authorized users. Your job is to secure this computer, within the
guidelines of the scenario, while ensuring the availability of authorized business critical software and services.
Company policy states that Windows Action Center should be enabled and monitoring the security status of
desktop Windows operating systems at all times.
This is a critical computer in a production environment. Please do NOT attempt to install Windows "Feature
Updates" or "Insider Preview Builds." Please do NOT attempt to use the Windows recovery options "Reset this
PC" or "Go back to an earlier build".
Windows 10
It is company policy to use only Windows 10 on this computer. Management has decided that the default web
browser for all users on this computer should be the latest stable version of Google Chrome. Other business
related software includes Notepad++, Mozilla Thunderbird, and WinRAR. This software should remain
installed and kept up-to-date.
AFA has also decided to up their logging capabilities and have asked you to install Sysmon with the
SwiftOnSecurity configuration. The configuration file has already been provided at 'C:\sysmon-config.xml.'
Install this at your earliest convenience.
Critical Services:
none
Authorized Administrators and Users
Authorized Administrators:
ealderson (you)
 password: samsep10l
ggoddard
 password: all$af3FA
lchong
 password: t3chn1t!on
oparker
 password: 123456Seven
Authorized Users:
cmoss
twellick
pprice
hdavis
sswailem
anayar
tcolby
dalderson
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
Malwarebytes, and possibly other antivirus products, may erroneously detect the CCS Client as
malware. If this happens, please ensure that CCSClient.exe has been manually added to the allow list
and restart the VM.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
WildCard26 Windows 11 README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure. You are being introduced to new
infrastructure within E-Corp, and must harden it to the best of your ability.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. The presence
of any non-work related media files and "hacking tools" on any computers is strictly prohibited. This company
currently does not use any centralized maintenance or polling tools to manage their IT equipment. This
computer is for official business use only by authorized users. Your job is to secure this computer, within the
guidelines of the scenario, while ensuring the availability of authorized business critical software and services.
Company policy states that Windows Action Center should be enabled and monitoring the security status of
desktop Windows operating systems at all times.
This is a critical computer in a production environment. Please do NOT attempt to install Windows "Feature
Updates" or "Insider Preview Builds." Please do NOT attempt to use the Windows recovery options "Reset this
PC" or "Go back to an earlier build".
Windows 11
It is company policy to use only Windows 11 on this computer. Management has decided that the default web
browser for all users on this computer should be the latest stable version of Google Chrome. Other business
related software includes Notepad++, 7-Zip, and Wireshark. These should remain installed and kept up-to-
date. Please ensure that the below services are kept in the original install location. Due to time restraints,
management requests that you do NOT install Windows Updates. However, you should ensure that the
computer is configured to automatically install updates.
Due to a recent security breach, the company has migrated the web application located on the Linux Mint
web server to this system. Apache2 and MariaDB are installed and running on this computer. These services
must remain installed at their current locations of C:\Apache24 and C:\MariaDB respectively. The web
application is located in the "C:\Apache24\htdocs" directory. You must keep this web application running and
accessible. Please only make minimal changes to the code when instructed.
Currently, the web application uses the MariaDB database "ecorp_directory". Please ensure that this database
remains intact and data is not altered. During the original attack, the database somehow lost all of its tables.
Please find and fix the issue to prevent further data loss.
In order to temporarily manage this system, this system has Windows Remote Management (WinRM)
enabled. The following users should be granted access to this system via WinRM: ealderson, lchong, tcolby,
sknowles, and twellick.
Critical Services:
Apache2 (HTTP)
MariaDB (SQL)
Windows Remote Management (WinRM)
Authorized Administrators and Users
Authorized Administrators:
twellick (you)
    password: 3Corp3x3cutive
jplofe
    password: AuditM4n@g3r
pmccleery
    password: root
wbraddock
    password: NetworkB0ss
ealderson
 password: samsep10l
lchong
 password: t3chn1t!on
sswailem
 password: data
Authorized Users:
pprice
sknowles
tcolby
jchutney
sweinsberg
sjacobs
lspencer
mralbern
jrobinson
gsheldern
coshearn
jlaslen
kshelvern
jtholdon
belkarn
bharper
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
Malwarebytes, and possibly other antivirus products, may erroneously detect the CCS Client as
malware. If this happens, please ensure that CCSClient.exe has been manually added to the allow list
and restart the VM.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
WildCard26 Windows Server 2019 README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. The presence
of any non-work related media files and "hacking tools" on any computers is strictly prohibited. This company
currently does not use any centralized maintenance or polling tools to manage their IT equipment. This
computer is for official business use only by authorized users. Your job is to secure this computer, within the
guidelines of the scenario, while ensuring the availability of authorized business critical software and services.
Company policy states that Windows Action Center should be enabled and monitoring the security status of
desktop Windows operating systems at all times.
This is a critical computer in a production environment. Please do NOT attempt to install Windows "Feature
Updates" or "Insider Preview Builds." Please do NOT attempt to use the Windows recovery options "Reset this
PC" or "Go back to an earlier build".
Windows Server 2019
It is company policy to use only Windows Server 2019 on this computer. Management has decided that the
default web browser for all users on this computer should be the latest stable version of Google Chrome.
Other business related software includes Notepad++, WinRAR, and Wireshark. This should remain installed
and kept up-to-date.
This server currently hosts an FTP file share utilizing FileZilla Server. This server is currently authorized to only
share C:\Users\Public\Documents to all anonymous users. Please ensure that this share remains available and
accessible to all anonymous users. Due to the anonymous nature of this share, it is critical that no sensitive
information is stored in this directory. FileZilla is currently configured to store all configuration files within
"C:\ProgramData\filezilla-server\" by the Windows Service Controller. Please ensure that the FileZilla Server
continues to use this directory for configuration.
Critical Services:
FileZilla Server (FTP)
Authorized Administrators and Users
Authorized Administrators:
ealderson (you)
 password: samsep10l
ggoddard
 password: all$af3FA
lchong
 password: t3chn1t!on
oparker
 password: 123456Seven
Authorized Users:
cmoss
twellick
pprice
hdavis
sswailem
anayar
tcolby
dalderson
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
Malwarebytes, and possibly other antivirus products, may erroneously detect the CCS Client as
malware. If this happens, please ensure that CCSClient.exe has been manually added to the allow list
and restart the VM.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
WildCard26 Windows Server 2022 README
Please read the entire README thoroughly before modifying anything on this computer.
Unique Identifier
If you have not yet entered a valid Unique Identifier, please do so immediately by double clicking on the "CCS
Set Unique Identifier" icon on the desktop. If you do not enter a valid Unique Identifier this VM may stop
functioning after a short period of time.
Forensics Questions
If there are "Forensics Questions" on your Desktop, you will receive points for answering these questions
correctly. Valid (scored) "Forensics Questions" will only be located directly on your Desktop. Please read all
"Forensics Questions" thoroughly before modifying this computer, as you may change something that
prevents you from answering the question correctly.
Competition Scenario
You work for Allsafe Forensics & Auditing (AFA), a new digital forensics & incident response company.
Recently, E-Corp contracted AFA to support their IT infrastructure. You are being introduced to new
infrastructure within E-Corp, and must harden it to the best of your ability.
Allsafe's security policies require that all user accounts be password protected. Employees are required to
choose secure passwords, however this policy may not be currently enforced on this computer. The presence
of any non-work related media files and "hacking tools" on any computers is strictly prohibited. This company
currently does not use any centralized maintenance or polling tools to manage their IT equipment. This
computer is for official business use only by authorized users. Your job is to secure this computer, within the
guidelines of the scenario, while ensuring the availability of authorized business critical software and services.
Company policy states that Windows Action Center should be enabled and monitoring the security status of
desktop Windows operating systems at all times.
This is a critical computer in a production environment. Please do NOT attempt to install Windows "Feature
Updates" or "Insider Preview Builds." Please do NOT attempt to use the Windows recovery options "Reset this
PC" or "Go back to an earlier build".
Windows Server 2022
It is company policy to use only Windows Server 2022 on this computer. Management has decided that the
default web browser for all users on this computer should be the latest stable version of Google Chrome.
Other business related software includes Notepad++, 7-Zip, and Wireshark. These should remain installed and
kept up-to-date. Please ensure that the below services are kept in the original install location. Due to time
restraints, management requests that you do NOT install Windows Updates. However, you should ensure that
the computer is configured to automatically install updates.
Due to frequent abuse of PowerShell, management has asked you and your team to enable powershell
logging features, such as script-block logging, for increased visibility in the environment. Furthermore,
management has also requested that event logs be protected from unauthorized reading by enabling
protected event logging with a valid certificate.
This server has been intended to be used as both a Domain Controller (DC) and Certificate Authority (CA).
Management has asked you and your team to review both AD DS and AD CS for misconfigurations and
remediate them immediately.
Critical Services:
Active Directory Domain Services (AD DS)
Active Directory Certificate Services (AD CS)
Authorized Administrators and Users
Authorized Administrators:
twellick (you)
    password: 3Corp3x3cutive
jplofe
    password: AuditM4n@g3r
pmccleery
    password: root
wbraddock
    password: NetworkB0ss
ealderson
 password: samsep10l
lchong
 password: t3chn1t!on
sswailem
 password: data
Authorized Users:
pprice
sknowles
tcolby
jchutney
sweinsberg
sjacobs
lspencer
mralbern
jrobinson
gsheldern
coshearn
jlaslen
kshelvern
jtholdon
belkarn
bharper
svc-ca
Competition Guidelines
In order to provide a better competition experience, you are NOT required to change the password of
the primary, auto-login, user account. Changing the password of a user that is set to automatically log in
may lock you out of your computer.
Authorized administrator passwords were correct the last time you did a password audit, but are not
guaranteed to be currently accurate.
Do not stop or disable the CCS Client service or process.
Do not remove any authorized users or their home directories.
The time zone of this image is set to UTC. Please do not change the time zone, date, or time on this
image.
You can view your current scoring report by double-clicking the "CCS Scoring Report" desktop icon.
JavaScript is required for some error messages that appear on the "CCS Scoring Report." To ensure that
you only receive correct error messages, please do not disable JavaScript.
Some security settings may prevent the Stop Scoring application from running. If this happens, the
safest way to stop scoring is to suspend the virtual machine. You should NOT power on the VM again
before deleting.
Malwarebytes, and possibly other antivirus products, may erroneously detect the CCS Client as
malware. If this happens, please ensure that CCSClient.exe has been manually added to the allow list
and restart the VM.
The CCS Competition System is the property of the University of Texas at San Antonio.
All rights reserved.
