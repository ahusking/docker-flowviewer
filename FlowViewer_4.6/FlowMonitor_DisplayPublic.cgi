#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_DisplayPublic.cgi displays a selected FlowMonitor.
#
#  Description:
#
#  FlowMonitor_DisplayPublic.cgi is invoked to display the selected monitor
#  in the Public display window.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  filter_hash          Name of the Monitor to be displayed
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Original Version.
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards
#  J. Loiacono  11/02/2014      4.5     FlowTracker to FlowMonitor rename
#
#$Author$
#$Date$
#$Header$
#
###########################################################################
#
#               BEGIN EXECUTABLE STATEMENTS
#
 
use FlowViewer_Configuration;
use FlowViewer_Utilities;
use FlowViewer_UI;

if ($debug_monitor eq "Y") { open (DEBUG,">$work_directory/DEBUG_MONITOR"); }
if ($debug_monitor eq "Y") { print DEBUG "In FlowMonitor_DisplayPublic.cgi\n"; }

$query_string  = $ENV{'QUERY_STRING'};
$query_string  =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge;
($active_dashboard,$filter_hash_string) = split(/\^/,$query_string);
($label,$filter_hash) = split(/=/,$filter_hash_string);
$main_dashboard = "Main_Only";

if ($debug_monitor eq "Y") { print DEBUG "FlowMonitor_DisplayPublic: filter_hash: $filter_hash\n"; }

print "Content-type:text/html\n\n";
print "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01//EN\"\n";
print "\"http://www.w3.org/TR/html4/strict.dtd\">\n\n";
print "<html lang=en>\n";
print "<head>\n";
print "<meta http-equiv=Content-Type content=\"text/html; charset=utf-8\">\n";
print "<title>FlowViewer - Maintaining Network Traffic Situational Awareness</title>\n";
print "<link rel=\"stylesheet\" href=\"$reports_short/FlowViewer.css\" type=\"text/css\">\n";
print "</head>\n";
print "<body>\n";
print "<center>\n";
print "<br>\n";
print "\n";

print "<div id=container>\n";
print " <div id=title_left>\n";
print "  <a href=$monitor_short/index.html><span class=link16>$left_title</span></a>\n";
print " </div>\n";
print " <div id=title_right>\n";
print "  <a href=$monitor_short/index.html><span class=link16>$right_title</span></a>\n";
print " </div>\n";
print " <div id=title_center>\n";
print "  <a href=$monitor_short/index.html><span class=text20>FlowViewer</span></a>\n";
print "  <p>\n";
print "  <a href=$monitor_short/index.html><span class=text12>Powered by flow-tools and SiLK</span></a>\n";
print " </div>\n";
print "\n";

print " <div class=gradient_down id=service_top></div>\n";
print " <div id=content_wide>\n";

&create_filter_output("FlowMonitor",$filter_hash);

($monitor_file,$suffix) = split(/\./,$filter_filename);

print " <center>\n";
print " <br><br><img src=$monitor_short/$monitor_file/daily.png usemap=#MonitorGraph_Map_1>\n";
print " <br><br><br><hr><br><br><img src=$monitor_short/$monitor_file/weekly.png usemap=#MonitorGraph_Map_2>\n";
print " <br><br><br><hr><br><br><img src=$monitor_short/$monitor_file/monthly.png usemap=#MonitorGraph_Map_3>\n";
print " <br><br><br><hr><br><br><img src=$monitor_short/$monitor_file/yearly.png usemap=#MonitorGraph_Map_4>\n";
print " <br><br><br><hr><br><br><img src=$monitor_short/$monitor_file/threeyears.png usemap=#MonitorGraph_Map_5>\n";
print " </center>\n";

if ($suffix eq "archive") {
        $archive_file = "$filter_directory/$filter_filename";
        open (FILTER,"<$archive_file");
        while (<FILTER>) {
                chop;
                $key = substr($_,0,28);
                if ($key eq " input: monitor_type: Group") {
                        $is_group = 1;
                        last;
                } else {
                        next;
                }
        }
}

if ($suffix eq "grp") { $is_group = 1; }

if ($is_group) {

	$group_file = "$filter_directory/$filter_filename";
        open (FILTER,"<$group_file");
        while (<FILTER>) {
                chop;
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        next;
                } else {
                        ($component_position,$component_label,$component_color) = split(/\^/);
                        $component_file = $component_label;
                        $component_file =~ s/^\s+//;
                        $component_file =~ s/\s+$//;
                        $component_file =~ s/\&/-/g;
                        $component_file =~ s/\//-/g;
                        $component_file =~ s/\(/-/g;
                        $component_file =~ s/\)/-/g;
                        $component_file =~ s/\./-/g;
                        $component_file =~ s/\s+/_/g;
                        $component_file =~ tr/[A-Z]/[a-z]/;
                        $component_html  = "$cgi_bin_short/FlowMonitor_DisplayPublic.cgi?$main_dashboard^filter_hash=MT_$component_file.fil";

                        $component_archive  = $rrdtool_directory ."/". $component_file .".archive";
                        if (-e $component_archive) { $component_html = "$cgi_bin_short/FlowMonitor_DisplayPublic.cgi?$main_dashboard^filter_hash=MT_$component_file.archive"; }

                        push (@component_links,$component_html);
                }
        }

        for ($k=1;$k<=5;$k++) {
                print "   <map name=MonitorGraph_Map_$k>\n";
                $num_link = 0;
                foreach $component_link (@component_links) {
                        $num_link++;
                        $x1 = 75;
                        $y1 = 217 + ($num_link * 14);
                        $x2 = 350;
                        $y2 = $y1 + 14;
                        print " <area shape=rect coords=\"$x1,$y1,$x2,$y2\" href=$component_link>\n";
                }
                print " </map>\n";
        }

} else {

	print "   <map name=MonitorGraph_Map_1>\n";
	print "   <area shape=rect coords=450,270,570,290 href=$cgi_bin_short/FlowMonitor_Dumper.cgi?$active_dashboard^24_hours^$monitor_file^>\n";
	print "   </map>\n";
	print "   <map name=MonitorGraph_Map_2>\n";
	print "   <area shape=rect coords=450,270,570,290 href=$cgi_bin_short/FlowMonitor_Dumper.cgi?$active_dashboard^7_days^$monitor_file^>\n";
	print "   </map>\n";
	print "   <map name=MonitorGraph_Map_3>\n";
	print "   <area shape=rect coords=450,270,570,290 href=$cgi_bin_short/FlowMonitor_Dumper.cgi?$active_dashboard^4_weeks^$monitor_file^>\n";
	print "   </map>\n";
	print "   <map name=MonitorGraph_Map_4>\n";
	print "   <area shape=rect coords=450,270,570,290 href=$cgi_bin_short/FlowMonitor_Dumper.cgi?$active_dashboard^12_months^$monitor_file^>\n";
	print "   </map>\n";
	print "   <map name=MonitorGraph_Map_5>\n";
	print "   <area shape=rect coords=450,270,570,290 href=$cgi_bin_short/FlowMonitor_Dumper.cgi?$active_dashboard^3_years^$monitor_file^>\n";
	print "   </map>\n";
}

print " </div>\n";
print " <div class=gradient_down id=service_bottom>\n";
print " <a href=$monitor_short/index.html><span class=link16>Return to List of Monitors</span></a>\n";
print "</div>\n";
print "</div>\n";
print "</body>\n";
print "</html>\n";
