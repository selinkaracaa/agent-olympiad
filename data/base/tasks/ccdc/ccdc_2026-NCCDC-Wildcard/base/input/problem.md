# NCCDC 2026 Wildcard

© NCCDC 2026. All Rights Reserved. 
2026 CCDC Wild Card Readme 
Welcome to the 2026 CCDC Wild Card event!  The goal for the Wild Card event is to score as many 
points as possible by finding and addressing as many misconfigurations, insecure settings, weaknesses, 
and vulnerabilities as you can on each VM (100 points are available on each VM) and to score as many 
points as you can on the injects/challenges presented to your team.  You may find malware, users that 
should not be on the system, insecure policy settings, users with admin privileges that should not have 
them, incorrect file permissions settings, and so on.  Please note that not every security issue is being 
scored – you can and will find issues on the VMs that do not award points when addressed.  Your team’s 
overall score (VM points plus inject/challenge points) will determine your final ranking in this 
competition. 
These VMs use the Cyber Competition System (CCS) developed by the CIAS (cias.utsa.edu).  CCS uses an 
agent (running on the VM) and a server.  The agent on the VM is called the “CCS Client”.  DO NOT STOP, 
MODIFY, OR REMOVE THE CCS CLIENT SERVICE ON YOUR VMs.  You will also notice a “CCS” directory 
on your VMs – do not modify, delete, or move any file in this directory.  To function properly, the VMs 
must have Internet access and be able to communicate with the CCS scoring server on TCP ports 80 and 
443.  The VMs are set to UTC time – please do not modify the time zone or time on the VMs. Do not 
delete or modify any files in the /opt/CCS or c:\CCS directories on any VM. 
Getting Started 
To access the VMs, you will need to connect to the Wild Card virtual environment using an HTML5 
compliant browser – any recent version of Chrome, Firefox, or Edge should work.  Other browsers, such 
as Safari, Brave, or Opera, may work but compatibility is not guaranteed.   
1. Open your browser and connect to https://wildcard.ciascompetitions.org/. You should see a 
login screen similar to the one below: 
 
 
2. Enter the username and password provided to you to login.  Each team member should use 
their own assigned login. 

 
© NCCDC 2026. All Rights Reserved. 
3. When you’ve successfully logged in you should see a screen similar to the one below 
 
 
4. Click on the “VMS” menu to see the VMs your account has access to. 
5. The VMs screen will look similar to the image below.  Clicking the “Open Web Console” button 
(the red arrow is pointing to it in the graphic below) will open the web console for that VM in a 
new browser tab.  Only web console access will be used during the Wild Card event. Right-
clicking on a specific VM will open a drop-down menu.  You can “Power On” a VM , “Reboot”, 
“Revert” a VM, and so on.  Please note selecting “Revert” will return the VM to its original 
starting configuration – you will lose all work you’ve done on that VM if you Revert it. This 
means your score for that VM goes back to zero. During the practice round you are welcome to 
revert your practice VMs as often as you need to allow other team members to work on them. 
 
 
 
The VM Desktop 
On the desktop of each VM, you will see several shortcuts with a CCDC icon. Here are descriptions of 
each shortcut: 
• CCS Scoring Report:  This shortcut opens a local webpage you will want to monitor closely when 
interacting with the VM.  This webpage will show your current score, your connection status to 
the scoring engine, any penalties occurred, and what security issues you’ve addressed on the 
VM.  Connection status lines should all be green if your VM is communicating with the scoring 
server:  
 
• CCS Readme:  This shortcut opens a webpage with a readme written for this VM or for multiple 
VMs in this event.  Please read the entire readme before interacting with the VM.  The readme 
will give you hints and information you will need to find and address some of the security issues 
on that VM.  For example, the readme may tell you about the organization’s password policy or 
detail what types of software are prohibited by company policy.  For example, if the corporate 

 
© NCCDC 2026. All Rights Reserved. 
policy prohibits the presence of media files on desktops then you will want to find and remove 
any media files (.mp3, .mp4, .mov, etc.…). 
• CCS Scoreboard:  This shortcut opens the web-based CCS scoreboard where you can see your 
team’s score compared to other teams that are competing at the same time.  The scoreboard 
will show you how many images you have connected to the system, your total score, and your 
total playing time on those images.  If that scoreboard URL opens to a blank page, just use the 
scoreboard from the portal.ecitadel.org web portal. 
 
A few more notes on the VMs 
 
- If you reset, revert, or start over on a VM your score will reset.  Your score is the current score  
of the active VM.  For example, if you worked on a Windows 10 VM and achieved a score of 90 
then reverted that VM to an earlier snapshot with a score of 0, your score would reset to 0.  Any 
points gained on that image prior to the reversion are lost. 
- The scoring system takes about a minute to recognize changes on the VM.  If you’ve made 
modifications to the VM, you may not see a score change for 60 to 90 seconds. 
- Not every security issue is scored on each VM.  You may find misconfigurations, incorrect 
settings, malware etc.. that are not scored even if you address them.   
- You will have the ability to power on and revert to snapshot.  You will not be able to create 
snapshots or clone any of the VMs. 
- Only one member of your team should access a VM’s web console at a time. If you and a 
teammate are both attempting to configure the same VM through different web console 
sessions you will be fighting each other for mouse and keyboard control. 
- There is no answer key for the practice images – the focus of the practice round is to ensure 
your team credentials work, you are able to access the web console of the VMs, and to 
familiarize yourself with the system.
