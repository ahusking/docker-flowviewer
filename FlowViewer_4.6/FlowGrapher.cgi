#! /usr/bin/perl
#
#  Purpose:
#  FlowGrapher.cgi creates the FlowGrapher web page for inputting
#  selection criteria.
#
#  Description:
#
#  FlowGrapher.cgi will create an form for accepting parameters
#  to control the filtering and selection of Netflow data.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  none      
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  01/01/2006      2.0     Original distributed version.
#  J. Loiacono  01/26/2006      2.2     Added flow_select option
#  J. Loiacono  07/04/2006      3.0     Replaces create_FG_webpage
#  J. Loiacono  12/25/2006      3.1     New 300 second sample time
#  J. Loiacono  02/22/2007      3.2     [No Change to this module]
#  J. Loiacono  12/07/2007      3.3     Named Interfaces (thanks C. Kashimoto)
#                                       Saved Filters, Next Hop
#  J. Loiacono  03/17/2011      3.4     Can now change device w/o reset
#                                       Can limit stats to non-zero data points
#  J. Loiacono  05/08/2012      4.0     Major upgrade: IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards
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

if ($debug_grapher eq "Y") { open (DEBUG,">$work_directory/DEBUG_GRAPHER"); }
if ($debug_grapher eq "Y") { print DEBUG "In FlowGrapher... looking at query string\n"; }
$query_string = $ENV{'QUERY_STRING'};
$query_string =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge ;
$first_caret = index($query_string,"^");
$active_dashboard = substr($query_string,0,$first_caret);
$filter_hash_string = substr($query_string,$first_caret+1,255);
($label,$filter_hash) = split(/=/,$filter_hash_string);
if ($debug_grapher eq "Y") { print DEBUG "In FlowGrapher... active_dashboard: $active_dashboard   filter_hash: $filter_hash\n"; }

if ($active_dashboard eq "") {
	if (@dashboard_titles) {
		$active_dashboard = @dashboard_titles[0];
		$active_dashboard =~ s/ /~/;
	} else {
		$active_dashboard = "Main_Only";
	}
}

if (!-e $work_directory) {

        &create_UI_top($active_dashboard);
        &create_UI_service("FlowGrapher","service_top",$active_dashboard,$filter_hash);
        &create_UI_sides($active_dashboard);

        unless (mkdir $work_directory) { 

		&notify_of_error($work_directory);

	} else {

                chmod $work_dir_perms, $work_directory;

        	print " <div id=content>\n";
	        print " <br>\n";
	        print " <table>\n";
	        print " <tr><td>The directory for storing intermediate work files has been created:</td></tr>\n";
	        print " <tr><td>&nbsp</td></tr>\n";
	        print " <tr><td><font color=$filename_color><b><i>$work_directory</i></b></font></td></tr>\n";
	        print " <tr><td>&nbsp</td></tr>\n";
	        print " <tr><td>Please ensure this directory has adequate permissions for your</td></tr>\n";
	        print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";
	        print " </table>\n";
                print " <br>\n";
                print " <table>\n";
                print " <tr><td>&nbsp</td></tr>\n";
                print " <tr><td><form method=post action=\"$cgi_bin_short/FlowGrapher.cgi?$active_dashboard\">\n";
                print " <button class=links type=submit>Proceed</button></form></td></tr>\n";
                print " </table>\n";
                print " </div>\n";

	        &create_UI_service("FlowGrapher","service_bottom",$active_dashboard,$filter_hash);
	        &finish_the_page("FlowGrapher");
	
		if ($debug_grapher eq "Y") { open (DEBUG,">$work_directory/DEBUG_GRAPHER"); } 
	        if ($debug_grapher eq "Y") { print DEBUG "created directory: $graphs_directory\n"; }
	
	        exit;
	}
}

if (!-e $graphs_directory) {

        &create_UI_top($active_dashboard);
        &create_UI_service("FlowGrapher","service_top",$active_dashboard,$filter_hash);
        &create_UI_sides($active_dashboard);

        unless (mkdir $graphs_directory) { 

		&notify_of_error($graphs_directory);

	} else {

		chmod $html_dir_perms, $graphs_directory;

	        print " <div id=content>\n";
	        print " <br>\n";
	        print " <table>\n";
	        print " <tr><td>The directory for storing FlowGrapher Report files has been created:</td></tr>\n";
	        print " <tr><td>&nbsp</td></tr>\n";
	        print " <tr><td><font color=$filename_color><b><i>$graphs_directory</i></b></font></td></tr>\n";
	        print " <tr><td>&nbsp</td></tr>\n";
	        print " <tr><td>Please ensure this directory has adequate permissions for your</td></tr>\n";
	        print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";
	        print " </table>\n";
                print " <br>\n";
                print " <table>\n";
                print " <tr><td>&nbsp</td></tr>\n";
                print " <tr><td><form method=post action=\"$cgi_bin_short/FlowGrapher.cgi?$active_dashboard\">\n";
                print " <button class=links type=submit>Proceed</button></form></td></tr>\n";
                print " </table>\n";
                print " </div>\n";

	        &create_UI_service("FlowGrapher","service_bottom",$active_dashboard,$filter_hash);
	        &finish_the_page("FlowGrapher");
	
        	if ($debug_grapher eq "Y") { print DEBUG "created directory: $graphs_directory\n"; }

	        exit;
	}
}

# Start the page ...

&create_UI_top($active_dashboard);
&create_UI_service("FlowGrapher","service_top",$active_dashboard,$filter_hash);
&create_UI_sides($active_dashboard);

# Create the FlowGrapher Content

print " <div id=content>\n";
&create_filtering_form("FlowGrapher",$filter_hash);
&create_graphing_form($filter_hash);
&create_SiLK_form($filter_hash);
&create_submit_buttons("FlowGrapher");
print " </div>\n";

# ... end the page.

&create_UI_service("FlowGrapher","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowGrapher");

sub notify_of_error {

	my ($failed_directory) = @_;

        print " <div id=content>\n";
        print " <br>\n";
        print " <table>\n";
        print " <tr><td>Unable to create the directory for storing intermediate work files:</td></tr>\n";
        print " <tr><td>&nbsp</td></tr>\n";
        print " <tr><td><font color=$filename_color><b><i>$failed_directory</i></b></font></td></tr>\n";
        print " <tr><td>&nbsp</td></tr>\n";
        print " <tr><td>Please create this directory with adequate permissions for your</td></tr>\n";
        print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";

        print " </table>\n";
        print " </div>\n";

        &create_UI_service("FlowGrapher","service_bottom",$active_dashboard,$filter_hash);
        &finish_the_page("FlowGrapher");

        exit;
}
