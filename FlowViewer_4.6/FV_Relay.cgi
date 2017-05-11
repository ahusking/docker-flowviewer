#! /usr/bin/perl
#
# This script is used to 'relay' your users to the new version. 
# Replace the previous version of FV.cgi with this file. That is,  
# in the old directory, copy this file over top of the old FV.cgi 
# and when your users go to the site they're familiar with they will be re-  
# directed to the new version. Modify according to your environment.

### Modify this line to point to the v4.6 FlowViewer_Configuration.pm file
require "/var/www/cgi-bin/FlowViewer_4.6/FlowViewer_Configuration.pm";
###

print "Content-type:text/html\n\n";
print "<html>\n";
print "<head>\n";
print "<title>\n";
print "FlowViewer $version\n";
print "</title>\n";
print "<style type=text/css><!-- A { text-decoration:none } --></style>";
print "</head>\n";
print "<body text=$text_color link=$link_color vlink=$vlink_color>";
print "<pre>";

print "\n\n\n";
print "            <b>FlowViewer has been upgraded to Version 4.6</b>\n\n";
print "            Version 4.6:\n\n";
print "            1. Corrects processing for SiLK local timezones for FlowViewer and FlowGrapher\n";
print "            2. Fixes FlowGrapher's ability to examine "smallest" detaiil lines (e.g., -100 for smallest 100 flows)
print "            3. Fixes improper listing of very old Saved files
print "\n";
print "            Please click below to use FlowViewer v4.6:\n";
print "\n";
print "            <a href=$FlowViewer_service://$FlowViewer_server/$cgi_bin_short/FV.cgi>FlowViewer v4.6</a>\n";
print "\n";
print "            Remember to change your bookmarks.  Thanks.\n";
print "</body>\n";
print "</html>\n";
