#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_Management.cgi creates the web page for managaing
#  FlowMonitors (i.e., Modify, Remove, Archive, Restart.)
#
#  Description:
#
#  FlowMonitor_Management.cgi parses through existing FlowMonitor 
#  Filter files and creates the management web-page.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  none      
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface (reuses some FT_Main)
#  J. Loiacono  04/15/2013      4.1     Fixed rename/remove to include Dashboard
#  J. Loiacono  09/11/2013      4.2.1   Minor formatting changes
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

if ($debug_monitor eq "Y") { open (DEBUG,">>$work_directory/DEBUG_MONITOR_M"); }
if ($debug_monitor eq "Y") { print DEBUG "In FlowMonitor_Management.cgi\n"; }
if ($debug_monitor eq "Y") { print DEBUG "ENV: $ENV{'QUERY_STRING'}\n"; }

# Retrieve parameters for a 'Remove' or 'Revise' action

($active_dashboard,$action,$monitor_label,$device_revision) = split(/\^/,$ENV{'QUERY_STRING'});
if ($active_dashboard =~ "%5E") { ($active_dashboard,$action,$monitor_label) = split("%5E",$active_dashboard); }
if ($debug_monitor eq "Y") { print DEBUG "active_dashboard: $active_dashboard  action: $action  monitor_label: $monitor_label  device_revision: $device_revision\n"; }
if ($action eq "List")    { $action = "List Monitors"; }
if ($action eq "Solicit") { $action = "Solicit Revision"; }
if ($action eq "Revise")  { $action = "Revise Monitor"; }
if ($action eq "SolicitN"){ $action = "Solicit Rename"; }
if ($action eq "Rename")  { $action = "Rename Monitor"; }
if ($action eq "Archive") { $action = "Archive Monitor"; }
if ($action eq "Restart") { $action = "Restart Monitor"; }
if ($action eq "Remove")  { $action = "Remove Monitor"; }
if ($action eq "Proceed") { $action = "Proceed with Removal"; }
if ($device_revision ne "") { ($device_revision,$device_name_revision) = split(/=/,$device_revision); } chop($device_name_revision);

if ($active_dashboard eq "") {
	if (@dashboard_titles) {
		$active_dashboard = @dashboard_titles[0];
		$active_dashboard =~ s/ /~/;
	} else {
		$active_dashboard = "Main_Only";
	}
}

$monitor_label   =~ s/~/ /g;
$tm_monitor_file = $monitor_label;
$tm_monitor_file =~ s/^\s+//;
$tm_monitor_file =~ s/\s+$//;
$tm_monitor_file =~ s/\&/-/g;
$tm_monitor_file =~ s/\//-/g;
$tm_monitor_file =~ s/\(/-/g;
$tm_monitor_file =~ s/\)/-/g;
$tm_monitor_file =~ s/\./-/g;
$tm_monitor_file =~ s/\s+/_/g;
$tm_monitor_file =~ tr/[A-Z]/[a-z]/;

if ($debug_monitor eq "Y") { print DEBUG "action: $action   monitor_label: $monitor_label  tm_monitor_file: $tm_monitor_file\n"; }

$filter_file    = $filter_directory  ."/". $tm_monitor_file .".fil";
$group_file     = $filter_directory  ."/". $tm_monitor_file .".grp";
$archive_file   = $filter_directory  ."/". $tm_monitor_file .".archive";
$rrdtool_file   = $rrdtool_directory ."/". $tm_monitor_file .".rrd";

$html_directory = $monitor_directory ."/". $tm_monitor_file;
$html_file      = $html_directory ."/index.html";

&create_UI_top($active_dashboard);
&create_UI_service("FlowMonitor","service_top",$active_dashboard,$filter_hash);

# Create the FlowMonitor Management Content

if ($action eq "List Monitors") {

	&create_UI_sides($active_dashboard);
	print " <div id=content_scroll>\n";
	print "<br><b>Individual Monitors</b><br><br>\n\n";
	
	@filter_list = <$filter_directory/*>;
	@filter_list = sort(@filter_list);
	
	print "  <table>\n";
	
	foreach $filter_file (@filter_list) {
		
	        $tm_monitor_file = $filter_file; 
	        $tm_monitor_file =~ s#.*/##; 
	
	        open (FILTERS,"<$filter_file"); 
	        while (<FILTERS>) { 
	                chop;    
	                $key = substr($_,0,8);
	                if ($key eq " input: ") {
	
	                        ($input,$field,$field_value) = split(/: /);
	
	                        if (($field eq "monitor_label") || ($field eq "tracking_label")) { 
					$filter_label = $field_value;
	
					$filter_file   = "$filter_directory/$tm_monitor_file"; 
					($monitor_prefix,$monitor_suffix) = split(/\./,$tm_monitor_file);
					$filter_hash = "MT_" . $monitor_prefix;
	
					$file_label = $filter_label;
					$file_label =~ s/ /~/g;
	
					$monitor_link = "<a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$filter_hash>$filter_label</a>";
					$revise_link   = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Solicit^$file_label>Revise</a>";
					$rename_link   = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^SolicitN^$file_label>Rename</a>";
					$remove_link   = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Remove^$file_label>Remove</a>";
	
					if ($monitor_suffix eq "archive") {
						$num_archive++;
						$stop_link = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Restart^$file_label>Restart</a>";
						$rename_link = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^SolicitN^$file_label>Rename</a>";
						$revise_link = "";
						$archive_link = $monitor_link ."^^". $revise_link ."^^". $rename_link ."^^". $stop_link ."^^". $remove_link;
						$archive_links{$num_archive} = $archive_link;
						next;
					} elsif ($monitor_suffix eq "grp") {
						$num_group++;
						$revise_link = "<a href=$cgi_bin_short/FlowMonitor_Group.cgi?$active_dashboard^Solicit^$file_label>Revise</a>";
						$rename_link = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^SolicitN^$file_label>Rename</a>";
						$stop_link = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Archive^$file_label>Archive</a>"; 
						$group_link = $monitor_link ."^^". $revise_link ."^^". $rename_link ."^^". $stop_link ."^^". $remove_link;
						$group_links{$num_group} = $group_link;
						next;
					} else {
						$stop_link = "<a href=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Archive^$file_label>Archive</a>"; 
					}
	
					print "  <tr>\n";
					print "  <td class=tr_label>$monitor_link</td>\n";
					print "  <td class=tr_action>$revise_link</td>\n";
					print "  <td class=tr_action>$rename_link</td>\n";
					print "  <td class=tr_action>$stop_link</td>\n";
					print "  <td class=tr_action>$remove_link</td>\n";
					print "  </tr>\n";
	
				} else {
					next;
				}
			}
		}
	} 
	
	print "</table>";
	print "<table>";
	
	if ($num_group > 0) {
		print "   <br><b>Group Monitors</b><br><br>\n\n";
		@sorted_groups = sort { $a <=> $b} (keys %group_links);
		foreach $link_index (@sorted_groups) {
			($monitor_link,$revise_link,$rename_link,$stop_link,$remove_link) = split(/\^\^/,$group_links{$link_index});
			print "  <tr>\n";
			print "  <td class=tr_label>$monitor_link</td>\n";
			print "  <td class=tr_action>$revise_link</td>\n";
			print "  <td class=tr_action>$rename_link</td>\n";
			print "  <td class=tr_action>$stop_link</td>\n";
			print "  <td class=tr_action>$remove_link</td>\n";
			print "  </tr>\n";
		}
	}
	
	print "</table>";
	print "<table>";
	
	if ($num_archive > 0) {
		print "   <br><b>Archived Monitors</b><br><br>\n\n";
		@sorted_archives = sort { $a <=> $b } (keys %archive_links);
		foreach $link_index (@sorted_archives) {
			($monitor_link,$revise_link,$rename_link,$stop_link,$remove_link) = split(/\^\^/,$archive_links{$link_index});
			print "  <tr>\n";
			print "  <td class=tr_label>$monitor_link</td>\n";
			print "  <td class=tr_action>$revise_link</td>\n";
			print "  <td class=tr_action>$rename_link</td>\n";
			print "  <td class=tr_action>$stop_link</td>\n";
			print "  <td class=tr_action>$remove_link</td>\n";
			print "  </tr>\n";
		}
	}
	
	print "</table>";
	print " </div>\n";
}

elsif ($action eq "Solicit Revision") {

        $filter_hash = $tm_monitor_file;
	$filter_hash = "MT_" . $filter_hash;
	if ($device_revision ne "") { $filter_hash .= "^$device_revision"; }

        # Retrieve form input for Monitor to be modified

	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
	&create_filtering_form("FlowMonitor_Sol",$filter_hash);
	&create_monitor_form($filter_hash);
	&create_SiLK_form($filter_hash);
	&create_revision_form($filter_hash);
	&create_submit_buttons("FlowMonitor_Sol");

	print " </div>\n";
}

elsif ($action eq "Solicit Rename") {

	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";

        $button_text = "Rename Monitor";
        print "  <center>\n";
	print "  <br><br>Current FlowMonitor Name:<font color=$filename_color><b><i> $monitor_label </i></b></font>\n";
        print "  <form action=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Rename^$tm_monitor_file method=POST>\n";
        print "  <br><br><br>\n";
        print "  New FlowMonitor Name (Maximum 80 characters):\n";
        print "  <br><br>\n";
        print "  <span class=input_center>\n";
        print "  <input type=text style=\"clear: both\; width: 30em;\" name=new_name value=\"$new_name\">\n";
        print "  </span>\n";
        print "  <br><br><br>\n";
        print "  <input class=buttonc type=submit value=\"Rename the FlowMonitor\">\n";
        print "  <br><br><br>\n";
        print "  </form>\n";
        print "  </table>";

        print "  </center>\n";
        print " </div>\n";
}

elsif ($action eq "Rename Monitor") {

	# Retrieve new FlowMonitor name

        read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
        @pairs = split(/&/, $buffer);
        foreach $pair (@pairs) {
            ($name, $value) = split(/=/, $pair);
            $value =~ tr/+/ /;
            $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
            $FORM{$name} = $value;
        }

        $new_monitor_label = $FORM{new_name};
        $new_monitor_label = substr($new_monitor_label,0,80);

	# Retrieve old FlowMonitor name

        if (-e $group_file) { 
		$old_monitor_file = $filter_directory ."/". $tm_monitor_file .".grp";
	} elsif (-e $archive_file) {
		$old_monitor_file = $filter_directory ."/". $tm_monitor_file .".archive";
		$old_rrdtool_file = $rrdtool_directory ."/". $tm_monitor_file .".archive";
	} else {
		$old_monitor_file = $filter_directory ."/". $tm_monitor_file .".fil";
		$old_rrdtool_file = $rrdtool_directory ."/". $tm_monitor_file .".rrd";
	}

	$old_html_directory = "$monitor_directory/$tm_monitor_file";

        open  (OLD_FILTER,"<$old_monitor_file");
        while (<OLD_FILTER>) {
                chop;
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        ($input,$field,$field_value) = split(/: /);
                        if (($field eq "monitor_label") || ($field eq "tracking_label")) { $old_monitor_label = $field_value; }
                        if (($field eq "monitor_type")  || ($field eq "tracking_type"))  { $old_monitor_type  = $field_value; }
                }
        }
        close (OLD_FILTER);
	$is_group = 0; if ($old_monitor_type eq "Group") { $is_group = 1; }

	# Define new Filter, RRDtool, and HTML files and directory

	$tn_monitor_file = $new_monitor_label;
	$tn_monitor_file =~ s/^\s+//;
	$tn_monitor_file =~ s/\s+$//;
	$tn_monitor_file =~ s/\&/-/g;
	$tn_monitor_file =~ s/\//-/g;
	$tn_monitor_file =~ s/\(/-/g;
	$tn_monitor_file =~ s/\)/-/g;
	$tn_monitor_file =~ s/\./-/g;
	$tn_monitor_file =~ s/\s+/_/g;
	$tn_monitor_file =~ tr/[A-Z]/[a-z]/;
	
        if (-e $group_file) { 
		$new_monitor_file = $filter_directory ."/". $tn_monitor_file .".grp";
		$new_rrdtool_file = "";
	} elsif (-e $archive_file) {
		$new_monitor_file = $filter_directory ."/". $tn_monitor_file .".archive";
		$new_rrdtool_file = $rrdtool_directory ."/". $tn_monitor_file .".archive";
	} else {
		$new_monitor_file = $filter_directory ."/". $tn_monitor_file .".fil";
		$new_rrdtool_file = $rrdtool_directory ."/". $tn_monitor_file .".rrd";
	}

	$new_monitor_filter  = $filter_directory  ."/". $tn_monitor_file .".fil";
	$new_monitor_group   = $filter_directory  ."/". $tn_monitor_file .".grp";
	$new_monitor_archive = $filter_directory  ."/". $tn_monitor_file .".archive";

	$name_in_use = 0;
	if (-e $new_monitor_filter)  { $name_in_use = 1; $found_file = $new_monitor_filter; }
	if (-e $new_monitor_group)   { $name_in_use = 1; $found_file = $new_monitor_group; }
	if (-e $new_monitor_archive) { $name_in_use = 1; $found_file = $new_monitor_archive; }

	# Check to see if name available

	if (($name_in_use) || ($new_monitor_label eq ""))  {

		&create_UI_sides($active_dashboard);
		print " <div id=content>\n";
	
	        $button_text = "Rename Monitor";
	        print "  <center>\n";
		print "  <br><br>Current FlowMonitor Name:<font color=$filename_color><b><i> $old_monitor_label </i></b></font>\n";
	        print "  <form action=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Rename^$tm_monitor_file method=POST>\n";
	        print "  <br><br>\n";
		if ($name_in_use) {

                	$found_filter = $found_file;
                	$found_filter =~ s#.*/##;

        		print " <table>";
			print " <tr><td align=right><b>Error:&nbsp&nbsp</b></td><td align=left>The new Monitor name is in use, please provide a different name.</td></tr>\n";
			print " <tr><td align=right><b>Existing Filter:&nbsp&nbsp</b></td><td align=left>$found_filter</td></tr>\n";
			print " <tr><td>&nbsp</td></tr>\n";
			print " <tr><td>&nbsp</td></tr>\n";
        		print " </table>";
		} elsif ($new_monitor_label eq "") {
        		print " <table>";
			print " <tr><td align=right><b>Error:&nbsp&nbsp</b></td><td align=left>No name supplied.</td></tr>\n";
			print " <tr><td>&nbsp</td></tr>\n";
			print " <tr><td>&nbsp</td></tr>\n";
        		print " </table>";
		}
	        print "  New FlowMonitor Name (Maximum 80 characters):\n";
	        print "  <br><br>\n";
	        print "  <span class=input_center>\n";
	        print "  <input type=text style=\"clear: both\; width: 30em;\" name=new_name value=\"$new_name\">\n";
	        print "  </span>\n";
	        print "  <br><br><br>\n";
	        print "  <input class=buttonc type=submit value=\"Rename the FlowMonitor\">\n";
	        print "  <br><br><br>\n";
	        print "  </form>\n";
	
	        print "  </center>\n";
	        print " </div>\n";

		&create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
		&finish_the_page("FlowMonitor");

		exit;
	}

	$new_html_directory = "$monitor_directory/$tn_monitor_file";

	# Change Monitor label in new filter file

        open (OLD_FILTER,"<$old_monitor_file");
        open (NEW_FILTER,">$new_monitor_file");
        while (<OLD_FILTER>) {
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        ($input,$field,$field_value) = split(/: /);
                        if (($field eq "monitor_label") || ($field eq "tracking_label")) {
				print NEW_FILTER " input: monitor_label: $new_monitor_label\n";
                        } else {
				print NEW_FILTER $_;
                        }
                } else {
			print NEW_FILTER $_;
		}
        }
        close (OLD_FILTER);
        close (NEW_FILTER);
	chmod $filter_file_perms, $new_monitor_file;

	# Remove old filter file, rename RRDtool file and FlowMonitor HTML directory

	$remove_command = "rm \-f $old_monitor_file";
	system($remove_command);

	if ($new_rrdtool_file ne "") {
		$move_command = "mv $old_rrdtool_file $new_rrdtool_file";
		system($move_command);
		chmod $rrd_file_perms, $new_rrdtool_file;
	}

	$move_command = "mv $old_html_directory $new_html_directory";
	system($move_command);
	chmod $html_dir_perms, $new_html_directory;

	# Rename Dashboard file if it exists
	
	$db_monitor_file = $old_monitor_label;
	$db_monitor_file =~ s/^\s+//;
	$db_monitor_file =~ s/\s+$//;
	$db_monitor_file =~ s/\&/-/g;
	$db_monitor_file =~ s/\//-/g;
	$db_monitor_file =~ s/\(/-/g;
	$db_monitor_file =~ s/\)/-/g;
	$db_monitor_file =~ s/\./-/g;
	$db_monitor_file =~ s/\s+/_/g;
	$db_monitor_file =~ tr/[A-Z]/[a-z]/;
	
	$len_old_label = length($db_monitor_file);
	
	@all_dashboards = @other_dashboards;
	push (@all_dashboards,$dashboard_directory);

	foreach $dashboard (@all_dashboards) {

	        @dashboard_files = <$dashboard/*>;
		foreach $dashboard_file (@dashboard_files) {
			$file_w_suffix = $dashboard_file;
			$file_w_suffix =~ s#.*/##;
			$last_underscore = rindex($file_w_suffix,"_");
			$remove_underscore = substr($file_w_suffix,0,$last_underscore);
			$next_last_underscore = rindex($remove_underscore,"_");
			$dashboard_label  = substr($file_w_suffix,0,$next_last_underscore);
			$dashboard_suffix = substr($file_w_suffix,$next_last_underscore,255);
			if ($dashboard_label eq $db_monitor_file) {
				$new_dashboard_file = $dashboard . "/" . $tn_monitor_file . $dashboard_suffix;
				$move_command = "mv $dashboard_file $new_dashboard_file";
				system($move_command);
				chmod $html_dir_perms, $new_dashboard_file;
			}
		}
	}
	
	# Rename this Individual Monitor in any groups of which it is a component

	@containing_groups = ();
	@containing_group_names = ();

        @group_files = <$filter_directory/*.grp>;
        if ((!$is_group) && (@group_files != ())) {

                foreach $group_file (@group_files) {
		        open (GROUP_FILE,"<$group_file");
		        while (<GROUP_FILE>) {
	                	$key = substr($_,0,8);
		                if ($key eq " input: ") { 
                                        if (/monitor_label/) { 
						($record_type,$input_type,$group_label) = split(/: /,$_);
						if ($containing_group) {
							push(@containing_group_names,$group_label);
							$containing_group = 0;
						}
					}
					next;
		                } else {
		                        ($component_position,$component_label,$component_color) = split(/\^/);
		                        if ($old_monitor_label eq $component_label) { 
						push(@containing_groups,$group_file);
						$containing_group = 1;
					}
				}
			}
			close(GROUP_FILE);
		}

		$temp_group = "$work_directory/temp_group.grp";
                foreach $group_file (@containing_groups) { 

		        open (OLD_GROUP,"<$group_file");
		        open (TEMP_GROUP,">$temp_group");
		        while (<OLD_GROUP>) {
	                	$key = substr($_,0,8);
		                if ($key eq " input: ") { 
					print TEMP_GROUP $_;
		                } else {
		                        ($component_position,$component_label,$component_color) = split(/\^/);
		                        if ($old_monitor_label eq $component_label) { 
						$group_member = $component_position ."^". $new_monitor_label ."^". $component_color;
						print TEMP_GROUP "$group_member";
					} else {
						print TEMP_GROUP $_;
					}
				}
			}
			close(OLD_GROUP);
			close(TEMP_GROUP);

			$move_command = "mv $temp_group $group_file";
        		system($move_command);
			chmod $filter_file_perms, $group_file;
		}
	}

	# Output the changed information

	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
	print "  <br><br>\n";
        print "  <table>";
	print "  <tr><td align=right>&nbsp&nbsp</td><td align=left><b>FlowMonitor has been Successfully Renamed</b></td></tr>\n";
	print "  <tr><td>&nbsp</td></tr>\n";
	print "  <tr><td align=right>Old Monitor File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$old_monitor_file</i></b></font></td></tr>\n";
        if (!$is_group) { 
	print "  <tr><td align=right>Old RRDtool File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$old_rrdtool_file</i></b></font></td></tr>\n";
	}
	print "  <tr><td align=right>Old HTML Directory: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$old_html_directory</i></b></font></td></tr>\n";
	print "  <tr><td align=right>Old Monitor Name: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$old_monitor_label</i></b></font></td></tr>\n";
	print "  <tr><td>&nbsp</td></tr>\n";
	print "  <tr><td align=right>New Monitor File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$new_monitor_file</i></b></font></td></tr>\n";
        if (!$is_group) { 
	print "  <tr><td align=right>New RRDtool File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$new_rrdtool_file</i></b></font></td></tr>\n";
	}
	print "  <tr><td align=right>New HTML Directory: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$new_html_directory</i></b></font></td></tr>\n";
	print "  <tr><td align=right>New Monitor Name: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$new_monitor_label</i></b></td></tr>\n";

	if (@containing_group_names != ()) {
		print "  <tr><td>&nbsp</td></tr>\n";
		print "  <tr><td align=right>&nbsp&nbsp</td><td align=left>The FlowMonitor reference was renamed in the following Groups</td></tr>\n";
		print "  <tr><td>&nbsp</td></tr>\n";
	}
	foreach $containing_group_name (@containing_group_names) {
		print "  <tr><td align=right>Updated Group: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$containing_group_name</i></b></font></td></tr>\n";
	}
		
        print "  </table>\n";
	print "  <br>\n";
        print "  <table>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        print "  </table>\n";
        print "  </div>\n";
}

elsif ($action eq "Remove Monitor") {

        if (-e $group_file) {
                $is_group = 1;
        	$filter_group = $filter_file;
        	$filter_group =~ s/\.fil/\.grp/;
	} elsif (-e $archive_file) {
		$is_archive = 1;
	        open  (FILTER_ARCHIVE,"<$archive_file");
	        while (<FILTER_ARCHIVE>) {
	                chop;
	                $key = substr($_,0,8);
	                if ($key eq " input: ") {
	                        ($input,$field,$field_value) = split(/: /);
	                        if (($field eq "monitor_type") || ($field eq "tracking_type")) { $archive_type  = $field_value; }
	                }
	        }
	        close (FILTER_ARCHIVE);
		$is_group = 0; if ($archive_type eq "Group") { $is_group = 1; }
        } else {
                @group_files = <$filter_directory/*.grp>;
                foreach $group_file (@group_files) {
                        $is_a_member = 0;
                        open (GROUP_FILE,"<$group_file");
                        while (<GROUP_FILE>) {
                                $key = substr($_,0,8);
                                if ($key eq " input: ") {
                                        if (/monitor_label/) { ($record_type,$input_type,$group_label) = split(/: /,$_); }
                                        next;
                                } else {
                                        ($component_position,$component_label,$component_color) = split(/\^/);
                                        if ($monitor_label eq $component_label) { $is_a_member = 1; }
                                }
                        }
                        if ($is_a_member) { push(@member_groups,$group_label); }
                }
        }

        # Output the summary web page

        $filter_file  =~ s#.*/##;
        $rrdtool_file =~ s#.*/##;

        $html_file = $html_directory;
        $html_file =~ s#.*/##;

        $file_label = $monitor_label;
        $file_label =~ s/ /~/g;

	&create_UI_sides($active_dashboard);
	print " <div id=content_wide>\n";
	print "<br><b>Remove FlowMonitor</b><br><br>\n\n";

        print "  <br>\n";
        print "  <table>\n";
        print "  <tr><td colspan=2>If you proceed, all files and directories associated with:</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td width=140 align=right><b>FlowMonitor: &nbsp&nbsp</b></td><td align=left><font color=$filename_color><b><i>$monitor_label</i></b></font></td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td colspan=2>will be moved to your Work directory, under subdirectory:</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td width=140 align=right><b>Subdirectory: &nbsp&nbsp</b></td><td align=left><font color=$filename_color><b><i>$work_directory</i></b></font></td></tr>\n";
        print "  <tr><td align=right> &nbsp&nbsp</td><td><font color=$filename_color><b><i>/$html_file</i></b></td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td colspan=2>If you proceed in error, you will still be able recreate this FlowMonitor by moving the FlowMonitor files back to the</td></tr>\n";
        print "  <tr><td colspan=2>operational directories, verifying that directory permissions are correct, and recreating and repopulating (.png files)</td></tr>\n";
        print "  <tr><td colspan=2>the Monitor HTML sub-directory. That would be:</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";

	$temp_filter = $filter_file;
       	if ($is_group)   { 
		$temp_filter =~ s/\.fil/\.grp/;
       		if ($is_archive) { $temp_filter =~ s/\.grp/\.archive/; }
	}
       	if ($is_archive) { $temp_filter =~ s/\.fil/\.archive/; }

        if ($is_group) {
        	print "  <tr><td align=right>1) Move: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$work_directory/$temp_filter</i></b></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>2) Recreate & &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$monitor_directory/$html_file</i></b></font> directory.</td></tr>\n";
        	print "  <tr><td align=right>Repopulate: &nbsp&nbsp</td><td align=left>&nbsp</td></tr>\n";
        } else {
		print "  <tr><td align=right>1) Move: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$work_directory/$html_file/$temp_filter</i></b></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>2) Move: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$work_directory/$html_file/$rrdtool_file</i></b></font></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$rrdtool_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
		print "  <tr><td align=right>3) &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>If this Monitor was on the Dashboard, either re-create the Dashboard entry, or copy Dashboard file</i></b></font></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$dashboard_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>4) Recreate & &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$monitor_directory/$html_file</i></b></font> &nbsp directory.</td></tr>\n";
        	print "  <tr><td align=right>Repopulate: &nbsp&nbsp</td><td align=left>&nbsp</td></tr>\n";
        }
        print "  <tr><td>&nbsp</td></tr>\n";

        if ($#member_groups > -1) {
        	print "  <tr><td colspan=2>This monitor was found to be a component of the following Groups:</td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
                foreach $member_group (@member_groups) { print "  <tr><td>&nbsp</td><td align=left><font color=$filename_color><b><i>$member_group</i></b></font></td></tr>\n"; }
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td colspan=2>This Monitor will be removed from each of the Groups listed above.</td></tr>\n";
        }
        print "  </table>\n";

        print "  <table>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
	print "  <tr>";
        print "  <td align=left><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Proceed^$file_label\">\n";
        print "  <button class=links type=submit>Proceed</button></form></td>\n";
       	print "  <td>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "  <td align=center><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td>\n";
	print "  </tr>";

        print "  </table>\n";
        print "  </div>\n";
}

elsif ($action eq "Proceed with Removal") {

        if (!-e $work_directory) {
                mkdir $work_directory, $work_dir_perms || die "Cannot mkdir Work directory: $work_directory: $!";
                chmod $work_dir_perms, $work_directory;
        }

        if (-e $group_file) { $is_group = 1; }

	if (-e $archive_file) {
		$is_archive = 1;
	        open  (FILTER_ARCHIVE,"<$archive_file");
	        while (<FILTER_ARCHIVE>) {
	                chop;
	                $key = substr($_,0,8);
	                if ($key eq " input: ") {
	                        ($input,$field,$field_value) = split(/: /);
	                        if (($field eq "monitor_type") || ($field eq "tracking_type")) { $archive_type  = $field_value; }
	                }
	        }
	        close (FILTER_ARCHIVE);
		$is_group = 0; if ($archive_type eq "Group") { $is_group = 1; }
        }

	# Create a temporary directory in $work_directory

        $html_file = $html_directory;
        $html_file =~ s#.*/##;
	$temp_monitor_dir = "$work_directory/$html_file";
	$mkdir_command = "mkdir $temp_monitor_dir";
        system($mkdir_command);
        chmod $work_dir_perms, $temp_monitor_dir;

        # Remove directory and contents

	$copy_command = "cp $html_directory/\* $temp_monitor_dir";
        system($copy_command);
        $rmdir_command = "rm -rf $html_directory";
        system($rmdir_command);

        # Move filter (or Archived) file to temp directory

        $filter_archive = $filter_file;
        $filter_archive =~ s/\.fil/\.archive/;

        $filter_group = $filter_file;
        $filter_group =~ s/\.fil/\.grp/;

        $mv_command = "mv  $filter_file $temp_monitor_dir";
        system($mv_command);

        $mv_command = "mv  $filter_group $temp_monitor_dir";
        system($mv_command);

        $mv_command = "mv  $filter_archive $temp_monitor_dir";
        system($mv_command);

        # Move rrd (or Archived) file to work directory

        $rrdtool_archive = $rrdtool_file;
        $rrdtool_archive =~ s/\.rrd/\.archive/;

        $mv_command = "mv  $rrdtool_archive $rrdtool_file";
        system($mv_command);

        $mv_command = "mv  $rrdtool_file $temp_monitor_dir";
        system($mv_command);

	# Remove from Dashboards if it is there

	@all_dashboards = @other_dashboards;
	push(@all_dashboards,$dashboard_directory);

	foreach $dashboard (@all_dashboards) {
	        @dashboard_files = <$dashboard/*>;
		foreach $dashboard_file (@dashboard_files) {
			$file_w_suffix = $dashboard_file;
			$file_w_suffix =~ s#.*/##;
			$last_underscore = rindex($file_w_suffix,"_");
			$position = substr($file_w_suffix,$last_underscore+1,1);
			$remove_underscore = substr($file_w_suffix,0,$last_underscore);
			$next_last_underscore = rindex($remove_underscore,"_");
			$dashboard_label  = substr($file_w_suffix,0,$next_last_underscore);
			$dashboard_suffix = substr($file_w_suffix,$next_last_underscore,255);
			if ($dashboard_label eq $tm_monitor_file) {
				open(VARIABLES,">$work_directory/FM_Dash_remove");
				$dash_action = "dash_action=RemoveI_" . "$position" .":". $dashboard;
				print VARIABLES "$dash_action";
				close (VARIABLES);
				$ENV{QUERY_STRING}="$dash_action";
				$ENV{CONTENT_LENGTH}=255;
				$command = "$cgi_bin_directory/FlowMonitor_Dashboard.cgi?$active_dashboard < $work_directory/FM_Dash_remove";
				system($command);
				$rm_command = "rm -f $work_directory/FM_Dash_remove";
				if ($debug_files ne "Y") { system($rm_command); }
			}
		}
	}

        # Remove this Monitor from any groups of which it is a component

        if (!$is_group) {

                @group_files = <$filter_directory/*.grp>;

                foreach $group_file (@group_files) {

                        @group_lines = ();
                        $found_removal = 0;

                        open(GROUP_FILE,"<$group_file");
                        while (<GROUP_FILE>) {

                                $key = substr($_,0,8);
                                push(@group_lines,$_);

                                if ($key eq " input: ") {
                                        if (/monitor_label/) { ($record_type,$input_type,$group_label) = split(/: /,$_); }
                                        next;
                                } else {
                                        ($component_position,$component_label,$component_color) = split(/\^/);
                                        $component_hundreds = substr($component_position,0,1);

                                        if ($monitor_label eq $component_label) {
                                                ($removed_position,$removed_label,$removed_color) = split(/\^/);
                                                $removed_hundreds = substr($removed_position,0,1);
                                                $found_removal = 1;
                                                pop(@group_lines);
                                                next;
                                        }

                                        if (($found_removal) && ($component_hundreds eq $removed_hundreds)) {
                                                pop(@group_lines);
                                                $component_position--;
                                                $replaced_line = $component_position ."^". $component_label ."^". $component_color;
                                                push(@group_lines,$replaced_line);
                                        }
                                }
                        }
                        close (GROUP_FILE);

                        if ($found_removal) {
                                push(@removed_groups,$group_label);
                                open(GROUP_FILE,">$group_file");
                                foreach $group_line (@group_lines) { print GROUP_FILE $group_line; }
                                close (GROUP_FILE);
                        }
                }
        }

        # Output the summary web page

        $filter_file  =~ s#.*/##;
        $rrdtool_file =~ s#.*/##;

	&create_UI_sides($active_dashboard);
	print " <div id=content_wide>\n";
	print "<br><b>Proceeding with FlowMonitor Removal</b><br><br>\n\n";

        print "  <br>\n";
        print "  <table>\n";
        print "  <tr><td colspan=2>All files and directories associated with:</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td width=140 align=right><b>FlowMonitor: &nbsp&nbsp</b></td><td align=left><font color=$filename_color><b><i>$monitor_label</i></b></font></td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td colspan=2>have been moved to your Work directory, under subdirectory:</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td width=140 align=right><b>Subdirectory: &nbsp&nbsp</b></td><td align=left><font color=$filename_color><b><i>$work_directory</i></b></font></td></tr>\n";
        print "  <tr><td align=right> &nbsp&nbsp</td><td><font color=$filename_color><b><i>/$html_file</i></b></td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td colspan=2>If necessary, you can recreate this FlowMonitor by moving the FlowMonitor files back to the operational directories,</td></tr>\n";
        print "  <tr><td colspan=2>recreate and repopulate (.png files) the Monitor sub-directory and verify that directory permissions are correct.</td></tr>\n";
        print "  <tr><td colspan=2>That would be:</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";

	$temp_filter = $filter_file;
       	if ($is_group)   { 
		$temp_filter =~ s/\.fil/\.grp/;
       		if ($is_archive) { $temp_filter =~ s/\.grp/\.archive/; }
	}
       	if ($is_archive) { $temp_filter =~ s/\.fil/\.archive/; }

        if ($is_group) {
        	print "  <tr><td align=right>1) Move: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$work_directory/$html_file/$temp_filter</i></b></font></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_directory</i></b></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>2) Recreate & &nbsp</td><td align=left><font color=$filename_color><b><i>$monitor_directory/$html_file</i></b></font> directory</td></tr>\n";
        	print "  <tr><td align=right>Repopulate: &nbsp&nbsp</td><td align=left>&nbsp</td></tr>\n";
        } else {
        	print "  <tr><td align=right>1) Move: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$work_directory/$html_file/$temp_filter</i></b></font></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>2) Move: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$work_directory/$html_file/$rrdtool_file</i></b></font></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$rrdtool_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>3) &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp</td><td>If this Monitor was on the Dashboard, either re-create the Dashboard entry, or copy Dashboard file</i></b></font></td></tr>\n";
        	print "  <tr><td align=right>Back to: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$dashboard_directory</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>4) Recreate & &nbsp</td><td align=left><font color=$filename_color><b><i>$monitor_directory/$html_file</i></b></font> directory</td></tr>\n";
        	print "  <tr><td align=right>Repopulate: &nbsp&nbsp</td><td align=left>&nbsp</td></tr>\n";
        }
        print "  <tr><td>&nbsp</td></tr>\n";

        if ($#removed_groups > -1) {
        	print "  <tr><td colspan=2>This Monitor component was removed from the following Groups:</td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
                foreach $group_label (@removed_groups) { print "  <tr><td>&nbsp</td><td align=left><font color=$filename_color><b><i>$group_label</i></b></font></td></tr>\n"; }
        	print "  <tr><td>&nbsp</td></tr>\n";
		print "  <tr><td colspan=2>If you recreate the Monitor, and you want to restore the listed groups back</td></tr>\n";
		print "  <tr><td colspan=2>to their original state, you will have to revise each Group and add the</td></tr>\n";
		print "  <tr><td colspan=2>Monitor back in.</td></tr>\n";
        }
        print "  </table>\n";

        print "  <table>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        print "  </table>\n";
        print "  </div>\n";
}

elsif ($action eq "Archive Monitor") {

        $filter_archive = $filter_file;
        $filter_archive =~ s/\.fil/\.archive/;
        $mv_command = "mv $filter_file $filter_archive";

        # Check to see if this archive is a group file

        $group_file = $filter_file;
        $group_file =~ s/\.fil/\.grp/;

        if (-e $group_file) {
                $is_group = 1;
                $filter_archive = $group_file;
                $filter_file    =~ s/\.fil/\.grp/;
                $filter_archive =~ s/\.grp/\.archive/;
                $mv_command = "mv $group_file  $filter_archive";
        }

        system($mv_command);

        if (!$is_group) {
                $rrdtool_archive = $rrdtool_file;
                $rrdtool_archive =~ s/\.rrd/\.archive/;
                $mv_command = "mv $rrdtool_file $rrdtool_archive";
                system($mv_command);
        }

	# Remove from Dashboards if it is there

	@all_dashboards = @other_dashboards;
	push(@all_dashboards,$dashboard_directory);

	foreach $dashboard (@all_dashboards) {
	        @dashboard_files = <$dashboard/*>;
		foreach $dashboard_file (@dashboard_files) {
			$file_w_suffix = $dashboard_file;
			$file_w_suffix =~ s#.*/##;
			$last_underscore = rindex($file_w_suffix,"_");
			$position = substr($file_w_suffix,$last_underscore+1,1);
			$remove_underscore = substr($file_w_suffix,0,$last_underscore);
			$next_last_underscore = rindex($remove_underscore,"_");
			$dashboard_label  = substr($file_w_suffix,0,$next_last_underscore);
			$dashboard_suffix = substr($file_w_suffix,$next_last_underscore,255);
			if ($dashboard_label eq $tm_monitor_file) {
				open(VARIABLES,">$work_directory/FM_Dash_remove");
				$dash_action = "dash_action=RemoveI_" . "$position" .":". $dashboard;
				print VARIABLES "$dash_action";
				close (VARIABLES);
				$ENV{QUERY_STRING}="$dash_action";
				$ENV{CONTENT_LENGTH}=255;
				$command = "$cgi_bin_directory/FlowMonitor_Dashboard.cgi < $work_directory/FM_Dash_remove";
				system($command);
				$rm_command = "rm -f $work_directory/FM_Dash_remove";
				if ($debug_files ne "Y") { system($rm_command); }
			}
		}
	}

	&create_UI_sides($active_dashboard);
	print " <div id=content_wide>\n";
	print "<br><b>Archive FlowMonitor</b><br><br>\n\n";

        print "  <br>\n";
        print "  <table>\n";
        print "  <tr><td width=160 align=right>The Filter File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_file</i></b></font></td></tr>\n";
        print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
        print "  <tr><td width=160 align=right>has been renamed: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_archive</i></b></font></td></tr>\n";
        print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
        if (!$is_group) {
        	print "  <tr><td align=right>The RRDtool File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$rrdtool_file</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>has been renamed: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$rrdtool_archive</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
	}
        print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
        print "  </table>\n";
        print "  <table>\n";
        print "<tr><td align=left>Links to the graphs have been moved to the Archived Monitors section at the bottom\n";
        print "of the Manage All FlowMonitors pulldown. FlowMonitor_Collector will stop collecting\n";
        print "data for this Monitor. However, for historical purposes, the Monitor has not been\n";
        print "removed from any Groups it may belong to. You may restart this Monitor by clicking on\n";
        print "the Restart option now available for the listed Monitor in the Achives section of the\n";
        print "the Manage All FlowMonitors pulldown. You may have to refresh your screen.</td></tr>\n";
        print "  </table>\n";

        print "  <table>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        print "  </table>\n";
        print "  </div>\n";
}

elsif ($action eq "Restart Monitor") {

        $filter_archive = $filter_file;
        $filter_archive =~ s/\.fil/\.archive/;

        # Check to see if this archive is not a group file

        $is_group = 0;
        open  (ARCHIVE_FILTER,"<$filter_archive");
        while (<ARCHIVE_FILTER>) {
                chop;
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        ($input,$field,$field_value) = split(/: /);
                        if (($field eq "monitor_type") || ($field eq "tracking_type")) {
				if ($field_value eq "Group") { 
					$is_group = 1;
					last;
				}
			}
		}
	}
        close (ARCHIVE_FILTER);

        if ($is_group) { $filter_file =~ s/\.fil/\.grp/; }

        # Move the archive back to it's original form

        $mv_command = "mv $filter_archive $filter_file";
        system($mv_command);

        if (!$is_group) {
                $rrdtool_archive = $rrdtool_file;
                $rrdtool_archive =~ s/\.rrd/\.archive/;
                $mv_command = "mv $rrdtool_archive $rrdtool_file";
                system($mv_command);
        }

	&create_UI_sides($active_dashboard);
	print " <div id=content_wide>\n";
	print "<br><b>Restart FlowMonitor</b><br><br>\n\n";

        print "  <br>\n";
        print "  <table>\n";
        print "  <tr><td width=160 align=right>The archived Filter File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_archive</i></b></font></td></tr>\n";
        print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
        print "  <tr><td width=160 align=right>has been renamed: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$filter_file</i></b></font></td></tr>\n";
        print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
        if (!$is_group) {
        	print "  <tr><td align=right>The archived RRDtool File: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$rrdtool_archive</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td align=right>has been renamed: &nbsp&nbsp</td><td align=left><font color=$filename_color><b><i>$rrdtool_file</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
	}
        print "  <tr><td>&nbsp</td><td>&nbsp</td></tr>\n";
        print "  </table>\n";
        print "  <table>\n";
        print "<tr><td align=left>Links to the graphs have been restored to the Active Monitors section at the top\n";
        print "of the Manage All FlowMonitors pulldown. You may have to refresh your screen. FlowMonitor_Collector\n";
        print "will resume collecting data for this Monitor.</td></tr>\n";
        print "  </table>\n";

        print "  <table>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        print "  </table>\n";
        print "  </div>\n";

} else {
	&create_UI_sides($active_dashboard);
	print " <div id=content_wide>\n";
        print "  </div>\n";
}

&create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowMonitor");
