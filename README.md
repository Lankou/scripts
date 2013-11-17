scripts for my own convenience
=======

my little scripts!


**db-backup**

makes backup for certain PostgreSQL user. all database owned by this user will be backed up

assign user name in variable `PGUSER` in line 23 before use

**ddns-check**

keep-alive check for `ddns-up`. most variables are hardcoded.

**ddns-up**

a simple and unreliable bash script for updating DNSPod DDNS record.

variables:  
`LOGIN` = your login email address  
`PASS` = your password  
`DOMAIN` = your domain name (example.com)
`SUBDOM` = your subdomain name (**subdomain**.example.com, the bold part)  

you can also change `GETIPURL` for your own url to get the external IP. if you do, also check function `getip_post()` on line 45 to process the result.

**makenow**

a script to build AOKP for multiple devices

for example, `makenow maguro mako hammerhead` will build for targets `maguro`, `mako` and `hammerhead` respectively.

if build fails in the middle of the process, script will abort so you can know something went wrong instead of wasting time to build next target.

after each target's zip being generated, it will upload the file to the designated server by rsync

variables:  
`workdir` = aokp repo directory  
`backupdir` = directory to put the finished builds into  
`remotedir` = remote directory to upload to  
`remote` = remote server address, use public key authentication please! please also include user name (e.g. user@server.com)  
`remoteowner` = change file's owner after upload (e.g. `www-data`)  
`logdir` = where to put the build time logs  
`logfile` = log file name  
`buildlog` = where to put the compilation log  

**opticron**

i made this to optimize the png files in wordpress that being uploaded. not really useful i think.. just a quick dirty script

**pushrom**

push the aokp rom built today to device.

e.g. `pushrom hammerhead` will push `aokp_xxxxx_hammerhead_today.zip` to connected device's `/sdcard/`  

change the variables you see fit!

**sc**

hmm..