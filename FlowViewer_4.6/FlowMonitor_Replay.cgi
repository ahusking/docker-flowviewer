#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_Replay.cgi displays a saved FlowMonitor
#
#  Description:
#
#  FlowMonitor_Replay.cgi is invoked to display the selected saved
#  FlowMonitor in the display window.
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
if ($debug_monitor eq "Y") { print DEBUG "In FlowMonitor_Replay.cgi\n"; }

$query_string  = $ENV{'QUERY_STRING'};
$query_string  =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge;
($active_dashboard,$filter_hash_string) = split(/\^/,$query_string);
($label,$filter_hash) = split(/=/,$filter_hash_string);
$filter_source = substr($filter_hash,0,2);

&create_UI_top($active_dashboard);
&create_UI_service("FlowMonitor","service_top",$active_dashboard,$filter_hash);

# Create the FlowMonitor Replay Content

print " <div id=content_wide>\n";
&create_filter_output("FlowMonitor_Replay",$filter_hash);

($monitor_file,$suffix) = split(/\./,$filter_filename);
$MT_saved_directory = $save_short ."/". substr($monitor_file,0,25);

if ($debug_monitor eq "Y") { print DEBUG "FlowMonitor_Replay: filter_hash: $filter_hash  filter_filename: $filter_filename\n"; }

print " <center>\n";
print " <br><br><img src=$MT_saved_directory/daily.png>\n";
print " <br><br><br><hr><br><br><img src=$MT_saved_directory/weekly.png>\n";
print " <br><br><br><hr><br><br><img src=$MT_saved_directory/monthly.png>\n";
print " <br><br><br><hr><br><br><img src=$MT_saved_directory/yearly.png>\n";
print " <br><br><br><hr><br><br><img src=$MT_saved_directory/threeyears.png>\n";
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
                        $component_html  = "$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=MT_$component_file.fil";

                        $component_archive  = $rrdtool_directory ."/". $component_file .".archive";
                        if (-e $component_archive) { $component_html = "$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=MT_$component_file.archive"; }

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
}

print " </div>\n";

&create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowMonitor");
