#! /usr/bin/perl
#
#  Purpose:
#  FV.cgi creates the main FlowViewer web page.
#
#  Description:
#
#  FV.cgi creates a web page with links to each tool and to the
#  Dashboard maangement function.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  none      
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Original Version.
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

if ($debug_viewer eq "Y") { open (DEBUG,">>$work_directory/DEBUG_VIEWER"); }
if ($debug_viewer eq "Y") { print DEBUG "In FV.cgi ... ARGV[0]: $ARGV[0]\n"; }

$active_dashboard = $ARGV[0];
$active_dashboard =~ s/\\//;

if (!@ARGV) {
	if (@dashboard_titles) {
		$active_dashboard = @dashboard_titles[0];
		$active_dashboard =~ s/ /~/;
	} else {
		$active_dashboard = "Main_Only";
	}
}
if ($debug_viewer eq "Y") { print DEBUG "active_dashboard: $active_dashboard  active_dashboard: $active_dashboard\n"; }

if (!-e $reports_directory) {

        unless (mkdir $reports_directory) {

                &notify_of_error($reports_directory);

        } else {

		chmod $html_dir_perms, $reports_directory;
	
	        if ($debug_viewer eq "Y") { print DEBUG "created directory: $reports_directory\n"; }
	
		$copy_command = "cp $cgi_bin_directory/FlowViewer.css $reports_directory";
		system($copy_command);
		chmod $html_file_perms, "$reports_directory/FlowViewer.css";
	
		$copy_command = "cp $cgi_bin_directory/FV_button.png $reports_directory";
		system($copy_command);
		chmod $html_file_perms, "$reports_directory/FV_button.png";
	
		$copy_command = "cp $cgi_bin_directory/FG_button.png $reports_directory";
		system($copy_command);
		chmod $html_file_perms, "$reports_directory/FG_button.png";
	
		$copy_command = "cp $cgi_bin_directory/FM_button.png $reports_directory";
		system($copy_command);
		chmod $html_file_perms, "$reports_directory/FM_button.png";

        	&create_UI_top($active_dashboard);
        	&create_UI_service("FlowViewer","service_top",$active_dashboard,$filter_hash);
        	&create_UI_sides($active_dashboard);

                print " <div id=content>\n";
                print " <br>\n";
                print " <table>\n";
                print " <tr><td>The directory for storing FlowViewer Report files has been created:</td></tr>\n";
                print " <tr><td>&nbsp</td></tr>\n";
                print " <tr><td><font color=$filename_color><b><i>$reports_directory</i></b></font></td></tr>\n";
                print " <tr><td>&nbsp</td></tr>\n";
                print " <tr><td>Please ensure this directory has adequate permissions for your</td></tr>\n";
                print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";
                print " </table>\n";
                print " <br>\n";
                print " <table>\n";
                print " <tr><td>&nbsp</td></tr>\n";
                print " <tr><td><form method=post action=\"$cgi_bin_short/FV.cgi\">\n";
                print " <button class=links type=submit>Proceed</button></form></td></tr>\n";
                print " </table>\n";
                print " </div>\n";

                &create_UI_service("FlowViewer","service_bottom",$active_dashboard,$filter_hash);
                &finish_the_page("FlowViewer");

                exit;
	}
}

if (!-e $work_directory) {

        &create_UI_top($active_dashboard);
        &create_UI_service("FlowViewer","service_top",$active_dashboard,$filter_hash);
        &create_UI_sides($active_dashboard);

        unless (mkdir $work_directory) {

                &notify_of_error($work_directory);

        } else {

                chmod $work_dir_perms, $work_directory;

                if ($debug_viewer eq "Y") { open (DEBUG,">>$work_directory/DEBUG_VIEWER"); }
	        if ($debug_viewer eq "Y") { print DEBUG "created directory: $work_directory\n"; }
	
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
                print " <tr><td><form method=post action=\"$cgi_bin_short/FV.cgi\">\n";
                print " <button class=links type=submit>Proceed</button></form></td></tr>\n";
                print " </table>\n";
                print " </div>\n";

                &create_UI_service("FlowViewer","service_bottom",$active_dashboard,$filter_hash);
                &finish_the_page("FlowViewer");

                exit;
        }
}

# Start the page ...

&create_UI_top($active_dashboard);
&create_UI_service("FlowViewer","service_top",$active_dashboard,$filter_hash);
&create_UI_sides($active_dashboard);

# Create the FlowViewer Content

print " <div id=main>\n";
print " <br><br>\n";
print " <span class=gold28>FlowViewer</span>\n";
print " <br>\n";
print " <span class=gold14>Powered by flow-tools and SiLK</span>\n";
print " <br><br>\n";
print " <span class=text16>Advancing Network Traffic Situational Awareness</span>\n";
print " <br><br><br>\n";
print " <table><tr><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
print " <td align=left>\n";
print "FlowViewer provides a dynamic web front-end to two powerful open-source netflow data collector and analyzers, flow-tools and SiLK. FlowViewer provides the user with the ability to quickly extract network management information of interest from voluminous quantities of stored netflow data. The user can configure a Dashboard of continuously updating FlowMonitors to maintain a situational awareness of his organization's network traffic. All generated reports and filters can be saved for future application. FlowViewer consists of three primary tools: FlowViewer, FlowGrapher and FlowMonitor. The user can switch between the tools preserving the previously specified filter.\n";
print " </td>\n";
print " <td>&nbsp&nbsp&nbsp&nbsp</td></tr></table>\n";

print " <br><br>\n";
print " <table><tr><td width=80 style=\"vertical-align: bottom\">\n";
print " <a href=$cgi_bin_short/FlowViewer.cgi?$active_dashboard><img src=$reports_short/FV_button.png></a>\n";
print " </td>\n";
print " <td width=450 align=left>\n";
print " <a href=$cgi_bin_short/FlowViewer.cgi?$active_dashboard><b><span class=goldlink12>FlowViewer</span></b></a> enables the user to create text based reports from filtered netflow data. Several different reporting formats are provided. Each of these reports can be sorted by column heading.\n";
print " </td></tr></table>\n";
print " <br><br>\n";

print " <table><tr><td width=80 style=\"vertical-align: bottom\">\n";
print " <a href=$cgi_bin_short/FlowGrapher.cgi?$active_dashboard><img src=$reports_short/FG_button.png></a>\n";
print " </td>\n";
print " <td width=450 align=left>\n";
print " <a href=$cgi_bin_short/FlowGrapher.cgi?$active_dashboard><b><span class=goldlink12>FlowGrapher</span></b></a> enables the user to graph the bandwidth used by a filtered subset of netflow data during a specified time period. Resulting reports include the graph and a textual listing of the largest flows.";
print " </td></tr></table>\n";
print " <br><br>\n";

print " <table><tr><td width=80 style=\"vertical-align: bottom\">\n";
print " <a href=$cgi_bin_short/FlowMonitor.cgi?$active_dashboard><img src=$reports_short/FM_button.png></a>\n";
print " </td>\n";
print " <td width=450 align=left>\n";
print " <a href=$cgi_bin_short/FlowMonitor.cgi?$active_dashboard><b><span class=goldlink12>FlowMonitor</span></b></a> enables the user to maintain a long-term history of a particular traffic subset. FlowMonitors consist of five graphs of traffic over sucessive longer time periods: Daily, Weekly, Monthly, Yearly, and Last 3 Years.";
print " </td></tr></table>\n";
print " <br><br><br><br>\n";

print " <table>\n";
print " <tr>\n";
print " <td align=center><a href=$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard^List><span class=goldlink16><b>Manage Dashboard</b></span></a></td>\n";
print " <td width=120></td>\n";
print " <td align=center><a href=$reports_short/FlowViewer.pdf><span class=goldlink16><b>User's Guide</b></span></a></td>\n";
print " </tr>\n";
print " </table>\n";

print " </div>\n";

# ... end the page

&create_UI_service("FlowViewer","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowViewer");

sub notify_of_error {

        my ($failed_directory) = @_;

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
        print " <div id=content>\n";
        print " <br>\n";
        print " <table>\n";
        print " <tr><td>Unable to create the following directory:</td></tr>\n";
        print " <tr><td>&nbsp</td></tr>\n";
        print " <tr><td><font color=$filename_color><b><i>$failed_directory</i></b></font></td></tr>\n";
        print " <tr><td>&nbsp</td></tr>\n";
        print " <tr><td>Please create this directory with adequate permissions for your</td></tr>\n";
        print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";
        print " </table>\n";
        print " </div>\n";
        print " </html>\n";

        exit;
}
