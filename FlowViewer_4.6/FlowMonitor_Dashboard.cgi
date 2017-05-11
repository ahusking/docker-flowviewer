#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_Dashboard.cgi creates a web page for controlling
#  the creation, removal and replacement of FlowMonitor Thumbnail
#  graphs which create the dashboard on both sides of the tool.
#
#  Description:
#
#  FlowMonitor_Dashboard.cgi creates a panel of smaller boxes, each
#  of which allows the users to adjust the Thumbnail in that position.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  filter_hash          The name of the Monitor to be used for Thumbnail     
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Original Version
#  J. Loiacono  04/15/2013      4.1     Made a little more user safe
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
if ($debug_monitor eq "Y") { print DEBUG "In FlowMonitor_Dashboard...\n"; }

$query_string = $ENV{'QUERY_STRING'};
$query_string =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge ;
($active_dashboard,$action,$filter_hash) = split(/\^/,$query_string);
($label,$filter_hash)  = split(/=/,$filter_hash);
if ($debug_monitor eq "Y") { print DEBUG "active_dashboard: $active_dashboard  action: $action   label: $label  filter_hash: $filter_hash\n"; }

$switch_dashboard = $active_dashboard;
$switch_dashboard =~ s/\~/ /;
$active_db_directory = $dashboard_directory;
for ($i=0;$i<=$#dashboard_titles;$i++) {
        if (($dashboard_titles[$i] eq $switch_dashboard) && ($i > 0)) { $active_db_directory = $other_dashboards[$i-1]; }
}

if ($action eq "List") {

	# Start the page ...
	
	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	
	# Load the FlowMonitors into an array
	
	@filters = (); @actives = (); @groups = (); @archives = ();
	@filters = <$filter_directory/*>;
	foreach $filter_file (@filters) {
	        if    ($filter_file =~ /\.fil/)     { push (@actives,$filter_file); }
	        elsif ($filter_file =~ /\.grp/)     { push (@groups,$filter_file); }
	        elsif ($filter_file =~ /\.archive/) { push (@archives,$filter_file); }
	}
	
	@actives  = sort(@actives); unshift (@actives,"start_actives");
	@groups   = sort(@groups); unshift (@groups,"start_groups");
	@archives = sort(@archives); unshift (@archives,"start_archives");
	@filters  = (@actives, @groups, @archives);
	
	push(@monitor_options," <option selected value=\"\">Select a FlowMonitor</option>\n");
	
	# Load the monitors into an HTML Select construct
	
	foreach $filter_file (@filters) {
	
	        if ($filter_file eq "start_actives") {
	                push(@monitor_options,"<option disabled> </option>\n");
	                push(@monitor_options,"<option disabled>--- Individuals</option>\n");
	                push(@monitor_options,"<option disabled> </option>\n");
	                next;
	        } elsif ($filter_file eq "start_groups") {
	                push(@monitor_options,"<option disabled> </option>\n");
	                push(@monitor_options,"<option disabled>--- Groups</option>\n");
	                push(@monitor_options,"<option disabled> </option>\n");
	                next;
	        } elsif ($filter_file eq "start_archives") {
	                push(@monitor_options,"<option disabled> </option>\n");
	                push(@monitor_options,"<option disabled>--- Archives</option>\n");
	                push(@monitor_options,"<option disabled> </option>\n");
	                next;
	        }
	
	        $monitor_file = $filter_file;
	        $monitor_file =~ s#.*/##;
	        open (FILTER,"<$filter_file");
	        while (<FILTER>) {
	                chop;
	                $key = substr($_,0,8);
	                if ($key eq " input: ") {
	                        ($input,$field,$field_value) = split(/: /);
	                        if (($field eq "monitor_label") || ($field eq "tracking_label"))  {
	                                $dash_monitor_label  = $field_value;
	                                ($dash_monitor_prefix,$dash_monitor_suffix) = split(/\./,$monitor_file);
	                                push(@monitor_options,"   <option value=$dash_monitor_prefix>$dash_monitor_label</option>\n");
	                        }
	                }
	        }
	        close(FILTER);
	}
	push(@monitor_options,"  </select>\n");
	
	print " <div id=content>\n";
	print " <fieldset class=level1>\n";
	
	# Left Top thumbnail
	
	print " <fieldset class=dashboard_left>\n";
	print " <legend class=level2>Left Top</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("1");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Right Top thumbnail
	
	print " <fieldset class=dashboard_right>\n";
	print " <legend class=level2>Right Top</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("2");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Left Middle Top thumbnail
	
	print " <fieldset class=dashboard_left>\n";
	print " <legend class=level2>Left Middle Top</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("3");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Right Middle Top thumbnail
	
	print " <fieldset class=dashboard_right>\n";
	print " <legend class=level2>Right Middle Top</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("4");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Left Middle Bottom thumbnail
	
	print " <fieldset class=dashboard_left>\n";
	print " <legend class=level2>Left Middle Bottom</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("5");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Right Middle Bottom thumbnail
	
	print " <fieldset class=dashboard_right>\n";
	print " <legend class=level2>Right Middle Bottom</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("6");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Left Bottom thumbnail
	
	print " <fieldset class=dashboard_left>\n";
	print " <legend class=level2>Left Bottom</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("7");
	print " </form>\n";
	print " </fieldset>\n";
	
	# Right Bottom thumbnail
	
	print " <fieldset class=dashboard_right>\n";
	print " <legend class=level2>Right Bottom</legend>\n";
	print " <form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard\">\n";
	print " <select class=dashboard_file name=selected_monitor>\n";
	foreach $monitor_option (@monitor_options) { print $monitor_option; }
	print " </select>\n";
	&print_type;
	&print_buttons("8");
	print " </form>\n";
	print " </fieldset>\n";
	
	print " </fieldset>\n";
	print " </div>\n";
	
	# ... end the page
	
	&create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor");

	exit;
}

read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
@pairs = split(/&/, $buffer);
foreach $pair (@pairs) {
    ($name, $value) = split(/=/, $pair);
    $value =~ tr/+/ /;
    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
    $FORM{$name} = $value;
}

$dash_action       = $FORM{'dash_action'};
$selected_monitor = $FORM{'selected_monitor'};
$graph_type        = $FORM{'graph_type'};

if ($debug_monitor eq "Y") { print DEBUG "dash_action: $dash_action  selected_monitor: $selected_monitor  graph_type: $graph_type\n"; }
if (substr($dash_action,0,7) eq "RemoveI") {
	$position = substr($dash_action,8,1);
	$remove_dashboard = substr($dash_action,10,255);
	$dash_action = "Remove";
	$internal = 1;
} else {
	($dash_action,$position) = split(/_/,$dash_action);
	$remove_dashboard = $active_db_directory;
}

if (($dash_action eq "Install") && (($selected_monitor eq "") || ($graph_type eq ""))) {

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";

        print "  <table>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
	if ($selected_monitor eq "") {
		print " <tr><td>Must select a FlowMonitor</td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
	}
	if ($graph_type eq "") {
		print " <tr><td>Must select a FlowMonitor Type</td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
	}
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td align=center><form method=post action=\"$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        print "  </table>\n";

	# ... end the page
	
	print " </div>";
	&create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor");

	exit;
}

if ($dash_action eq "Install") {

	if ($debug_monitor eq "Y") { print DEBUG "In Install section...  active_dashboard: $active_dashboard   active_db_directory: $active_db_directory\n"; }
	
	# Remove the existing monitor in this position if it is there

	while ($existing_thumbnail = <$active_db_directory/*>) {
		if ($existing_thumbnail =~ /$position.png/) { 
			$rm_command = "rm -f $existing_thumbnail";
			$replacement = 1; 
			$assigned_position = $position;
			last;
		}

		($thumb_file,$thumb_suffix) = split(/\./,$existing_thumbnail);
		$thumb_pos = substr($thumb_file,-1,1);
		if (($thumb_pos % 2 == 0) && ($thumb_pos > $highest_even)) { $highest_even = $thumb_pos; }
		if (($thumb_pos % 2 == 1) && ($thumb_pos > $highest_odd )) { $highest_odd  = $thumb_pos; }
	}
	
	if ($replacement) {

		system($rm_command);

	} else {
		if ($position % 2 == 0) {
			if ($highest_even == 0) { $assigned_position = 2; }
			if ($highest_even == 2) { $assigned_position = 4; }
			if ($highest_even == 4) { $assigned_position = 6; }
			if ($highest_even == 6) { $assigned_position = 8; }
		} else {
			if ($highest_odd  == 0) { $assigned_position = 1; }
			if ($highest_odd  == 1) { $assigned_position = 3; }
			if ($highest_odd  == 3) { $assigned_position = 5; }
			if ($highest_odd  == 5) { $assigned_position = 7; }
		}
	}

	$thumbnail_command = "$cgi_bin_directory/FlowMonitor_Thumbnail $active_dashboard $selected_monitor $graph_type $assigned_position";
	system($thumbnail_command);

	$cgi_link = "$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard^List";
        print "Content-type:text/html\n\n";
        print "<head>";
        print "<META HTTP-EQUIV=Refresh CONTENT=\"0; URL=$cgi_link\">";
        print "</head>";
        print "<title>Manage FlowViewer Dashboard</title>";

} elsif ($dash_action eq "Remove") {

	if ($debug_monitor eq "Y") { print DEBUG "In Remove section. dash_action: $dash_action  position: $position  remove_dashboard: $remove_dashboard  selected_monitor: $selected_monitor  graph_type: $graph_type\n"; }

	if ($position >= 7) {

        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$position.png")     { $remove_file = $thumbnail_file; }
		}

		$remove_command = "rm -f $remove_file";
		system($remove_command);
	}

	if (($position < 7) && ($position >= 5)) {

		$moveup_index = $position + 2;

        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$moveup_index.png") { $moveup_file = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$position.png")     { $remove_file = $thumbnail_file; }
		}

		$remove_command = "rm -f $remove_file";
		system($remove_command);

		$destination_file = $moveup_file;
		$destination_file =~ s/_$moveup_index.png/_$position.png/;
		$move_command = "mv $moveup_file $destination_file";
		system($move_command);
	}

	if (($position < 5) && ($position >= 3)) {

		$newslot_index = $position;
		$moveup_index  = $position + 2;
        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$moveup_index.png") { $moveup_file = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$newslot_index.png"){ $remove_file = $thumbnail_file; }
		}
		$remove_command = "rm -f $remove_file";
		system($remove_command);
		$destination_file = $moveup_file;
		$destination_file =~ s/_$moveup_index.png/_$newslot_index.png/;
		$move_command = "mv $moveup_file $destination_file";
		system($move_command);

		$newslot_index = $position + 2;
		$moveup_index  = $position + 4;
        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$moveup_index.png") { $moveup_file = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$newslot_index.png"){ $remove_file = $thumbnail_file; }
		}
		$destination_file = $moveup_file;
		$destination_file =~ s/_$moveup_index.png/_$newslot_index.png/;
		$move_command = "mv $moveup_file $destination_file";
		system($move_command);
	}

	if ($position < 3) {

		$newslot_index = $position;
		$moveup_index  = $position + 2;
        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$moveup_index.png") { $moveup_file = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$newslot_index.png"){ $remove_file = $thumbnail_file; }
		}
		$remove_command = "rm -f $remove_file";
		system($remove_command);
		$destination_file = $moveup_file;
		$destination_file =~ s/_$moveup_index.png/_$newslot_index.png/;
		$move_command = "mv $moveup_file $destination_file";
		system($move_command);

		$newslot_index = $position + 2;
		$moveup_index  = $position + 4;
        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$moveup_index.png") { $moveup_file = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$newslot_index.png"){ $remove_file = $thumbnail_file; }
		}
		$destination_file = $moveup_file;
		$destination_file =~ s/_$moveup_index.png/_$newslot_index.png/;
		$move_command = "mv $moveup_file $destination_file";
		system($move_command);

		$newslot_index = $position + 4;
		$moveup_index  = $position + 6;
        	while ($thumbnail_file = <$remove_dashboard/*>) {
                	if ($thumbnail_file =~ "_$moveup_index.png") { $moveup_file = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$newslot_index.png"){ $remove_file = $thumbnail_file; }
		}
		$destination_file = $moveup_file;
		$destination_file =~ s/_$moveup_index.png/_$newslot_index.png/;
		$move_command = "mv $moveup_file $destination_file";
		system($move_command);
	}

	if (!$internal) {
		$cgi_link = "$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard^List";
	        print "Content-type:text/html\n\n";
	        print "<head>";
	        print "<META HTTP-EQUIV=Refresh CONTENT=\"0; URL=$cgi_link\">";
	        print "</head>";
	        print "<title>Manage FlowViewer Dashboard</title>";
	}

} elsif ($dash_action eq "MoveUp") {

	if ($position >= 3) {

		$destination_index = $position - 2;

        	while ($thumbnail_file = <$active_db_directory/*>) {
                	if ($thumbnail_file =~ "_$destination_index.png") { $moved_file  = $thumbnail_file; }
                	if ($thumbnail_file =~ "_$position.png")          { $moving_file = $thumbnail_file; $move_ok = 1; }
		}

		if ($move_ok) {
			$temp_command = "mv $moved_file $active_db_directory/temp_thumbnail";
			system($temp_command);
	
			$destination_file = $moving_file;
			$destination_file =~ s/_$position.png/_$destination_index.png/;
			$move_command = "mv $moving_file $destination_file";
			system($move_command);
	
			$destination_file = $moved_file;
			$destination_file =~ s/_$destination_index.png/_$position.png/;
			$return_command = "mv $active_db_directory/temp_thumbnail $destination_file";
			system($return_command);
		}
	}

	$cgi_link = "$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard^List";
        print "Content-type:text/html\n\n";
        print "<head>";
        print "<META HTTP-EQUIV=Refresh CONTENT=\"0; URL=$cgi_link\">";
        print "</head>";
        print "<title>Manage FlowViewer Dashboard</title>";

} elsif ($dash_action eq "MoveDown") {

	if ($position <= 6) {

		$destination_index = $position + 2;

        	while ($thumbnail_file = <$active_db_directory/*>) {
                	if ($thumbnail_file =~ "_$destination_index.png") { $moved_file  = $thumbnail_file; $move_ok = 1; }
                	if ($thumbnail_file =~ "_$position.png")          { $moving_file = $thumbnail_file; }
		}

		if ($move_ok) {
			$temp_command = "mv $moved_file $active_db_directory/temp_thumbnail";
			system($temp_command);
	
			$destination_file = $moving_file;
			$destination_file =~ s/_$position.png/_$destination_index.png/;
			$move_command = "mv $moving_file $destination_file";
			system($move_command);
	
			$destination_file = $moved_file;
			$destination_file =~ s/_$destination_index.png/_$position.png/;
			$return_command = "mv $active_db_directory/temp_thumbnail $destination_file";
			system($return_command);
		}
	}

	$cgi_link = "$cgi_bin_short/FlowMonitor_Dashboard.cgi?$active_dashboard^List";
        print "Content-type:text/html\n\n";
        print "<head>";
        print "<META HTTP-EQUIV=Refresh CONTENT=\"0; URL=$cgi_link\">";
        print "</head>";
        print "<title>Manage FlowViewer Dashboard</title>";

}

sub print_type {
	print " <select class=dashboard_type name=graph_type>\n";
	print " <option selected value=\"\">Type\n";
	print " <option value=>\n";
	print " <option value=Daily>Daily\n";
	print " <option value=Weekly>Weekly\n";
	print " <option value=Monthly>Monthly\n";
	print " <option value=Yearly>Yearly\n";
	print " <option value=3Years>3 Years\n";
	print " </select>\n";
}

sub print_buttons {

	my ($position) = @_;

	print " <p style=\"line-height: 80%;\">&nbsp</p>\n";
	print " <center>\n";
	print " <button class=dashboard type=submit name=dash_action value=Install_$position>Install New FlowMonitor</button>\n";
	print " <button class=dashboard type=submit name=dash_action value=Remove_$position>Remove Current FlowMonitor</button>\n";
	print " <button class=dashboard type=submit name=dash_action value=MoveUp_$position>Move FlowMonitor Up</button>\n";
	print " <button class=dashboard type=submit name=dash_action value=MoveDown_$position>Move FlowMonitor Down</button>\n";
}
