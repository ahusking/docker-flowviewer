#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_Group.cgi is invoked by FlowMonitor_Main.cgi to
#  collect information from the user to build a Group Monitor.
#
#  Description:
#  The script responds to an HTML form from the user in order to collect
#  information that will control the building of a group including,
#  component monitors, colors, and placements about the x-axis.
#
#  Input arguments (received from the form):
#  Name                 Description
#  -----------------------------------------------------------------------
#  monitor_label       Label used for identifying Monitor filter and HTML file
#  general_comment      Useful for explaining a particular set of Monitor graphs
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  02/22/2007      3.2     Original version
#  J. Loiacono  12/07/2007      3.3     Fixed color processing, Logo links
#  J. Loiacono  03/17/2011      3.4     Changed to new logo with 'Saved' link
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  01/26/2014      4.3     Fixed vertical legend for flows, pkts
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards
#  J. Loiacono  11/02/2014      4.5     FlowTracker to FlowMonitor rename
#                                       Fixed dashboard problem
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
use RRDs;

if ($debug_group eq "Y") { open (DEBUG,">$work_directory/DEBUG_GROUP"); }
if ($debug_group eq "Y") { print DEBUG "In FlowMonitor_Group.cgi...\n"; }

if (($ENV{'QUERY_STRING'}) ne "") {

	($active_dashboard,$action,$monitor_label) = split(/\^/,$ENV{'QUERY_STRING'});
	if ($action eq "Solicit") { $action = "Solicit Revision"; }
	if ($debug_group eq "Y") { print DEBUG "QUERY_STRING active_dashboard: $active_dashboard  action: $action  monitor_label: $monitor_label\n"; }

	# Retrieve input parameters from CGI form invocation (POST)
	
	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'}); 
	@pairs = split(/&/, $buffer); 
	foreach $pair (@pairs) { 
	    ($name, $value) = split(/=/, $pair);  
	    $value =~ tr/+/ /; 
	    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg; 
	    $FORM{$name} = $value;  
	} 

	if (($action eq "Adjust") || ($action eq "Done")) {
		$action         = $FORM{action};
		$monitor_label = $FORM{monitor_label};
	}

	$general_comment  = $FORM{general_comment};
	$revision_comment = $FORM{revision_comment};
	$notate_graphs    = $FORM{notate_graphs};

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);

} else {

	# Retrieve input parameters from initial FlowMonitor_Main.cgi invocation
	
	if ($debug_group eq "Y") { print DEBUG "NO QUERY_STRING   ARGV[0]: $ARGV[0]   ARGV[1]: $ARGV[1]\n"; }

	if ($ARGV[0] ne "") {
		$monitor_info = $ARGV[0];
		($active_dashboard,$monitor_info) = split(/\^/,$monitor_info);
		$monitor_info =~ s/~/ /g;
		($action,$monitor_label,$general_comment) = split(/\+/,$monitor_info);
		if ($action eq "Solicit") { $action = "Solicit Revision"; }
	}
	
	if ($ARGV[1] ne "") { 
		$monitor_label = $ARGV[1]; 
		$monitor_label =~ s/\\//g;
		$monitor_label =~ s/~/ /g;
	}
}
if ($debug_group eq "Y") { print DEBUG "active_dashboard: $active_dashboard  action: $action  component_label: $monitor_label\n"; }

$monitor_label =~ s/~/ /g;
$monitor_file = $monitor_label;
$monitor_file =~ s/^\s+//;
$monitor_file =~ s/\s+$//;
$monitor_file =~ s/\&/-/g;
$monitor_file =~ s/\//-/g;
$monitor_file =~ s/\(/-/g;
$monitor_file =~ s/\)/-/g;
$monitor_file =~ s/\./-/g;
$monitor_file =~ s/\s+/_/g;
$monitor_file =~ tr/[A-Z]/[a-z]/;

$group_file = $filter_directory ."/". $monitor_file .".grp";

if ($debug_group eq "Y") {
	print DEBUG "         ARGV[0]: $ARGV[0]\n";
	print DEBUG "         ARGV[1]: $ARGV[1]\n";
	print DEBUG "active_dashboard: $active_dashboard\n";
	print DEBUG "          action: $action\n";
	print DEBUG "    monitor_info: $monitor_info\n";
	print DEBUG "   monitor_label: $monitor_label\n";
	print DEBUG "    monitor_file: $monitor_file\n";
	print DEBUG " general_comment: $general_comment\n";
	print DEBUG "revision_comment: $revision_comment\n";
	print DEBUG "      group_file: $group_file\n";
}

if ($action eq "Done") {

	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
        print " <br>\n";
	print " <span class=text16>$monitor_label</span>\n";
        print " <br><br>\n";
	print " <table>\n";
        print " <tr><td colspan=2 align=left>You have successfully setup/revised a new Group Monitor. The graphs for this new Group Monitor will</td></tr>\n";
        print " <tr><td colspan=2 align=left>appear after the next FlowMonitor_Grapher run (e.g., < 5 minutes.)</td></tr>\n";
        print " <tr><td>&nbsp</td></tr>\n";
        print " <tr><td align=right>FlowMonitor: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$monitor_label</i></b></font></td></tr>\n";
        print " <tr><td align=right>Group File: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$group_file</i></b></font></td></tr>\n";
        print " <tr><td>&nbsp</td></tr>\n";
	print " </table>\n";
	print " <table>\n";
        print " <tr><td align=center><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print " <button class=links type=submit>Return</button></form></td></tr>\n";
	print " </table>\n";
	print " </div>\n";
	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");
	exit;
}

# Create the GROUPS directory if it doesn't exist

$groups_directory = "$monitor_directory/GROUPS";
if (!-e $groups_directory) {
        mkdir $groups_directory, $html_dir_perms || die "cannot mkdir $groups_directory: $!";
        chmod $html_dir_perms, $groups_directory;
}

# Load the colors

$colors_file = "$cgi_bin_directory/FlowGrapher_Colors";

open (COLORS,"<$colors_file") || die "Can't open colors file; $colors_file\n";
while (<COLORS>) {
	chop;
	($red,$green,$blue,$color_1,$color_2) = split(/\s+/);
	$color_name = $color_1;
	if ($color_2 ne "") { $color_name = $color_1 . " " . $color_2; }
	$R = &dec2hex($red);   if (length($R) < 2) { $R = "0" . $R; }
	$G = &dec2hex($green); if (length($G) < 2) { $G = "0" . $G; }
	$B = &dec2hex($blue);  if (length($B) < 2) { $B = "0" . $B; }
	$hex_colors{$color_name} =  $R . $G . $B;
	if ($color_1 eq "auto") {
		if (substr($color_2,0,5) eq "mixed") {
			$num_color = substr($color_2,5,1);
			if ($num_color > $largest_mixed) { $largest_mixed = $num_color; }
		}
		if (substr($color_2,0,4) eq "blue") {
			$num_color = substr($color_2,4,1);
			if ($num_color > $largest_blue) { $largest_blue = $num_color; }
		}
		if (substr($color_2,0,3) eq "red") {
			$num_color = substr($color_2,3,1);
			if ($num_color > $largest_red) { $largest_red = $num_color; }
		}
		if (substr($color_2,0,5) eq "green") {
			$num_color = substr($color_2,5,1);
			if ($num_color > $largest_green) { $largest_green = $num_color; }
		}
		if (substr($color_2,0,6) eq "violet") {
			$num_color = substr($color_2,6,1);
			if ($num_color > $largest_violet) { $largest_violet = $num_color; }
		}
	}
}
$hex_colors{"standard"} = $rrd_area;
sub dec2hex($) { return sprintf("%lx", $_[0]) }

# Retrieve existing group information for revision

if ($action eq "Solicit Revision") {

	open (GROUP,"<$group_file");
	while (<GROUP>) {
	        chop;
	        $key = substr($_,0,8);
	        if ($key eq " input: ") {
	                ($input,$field,$field_value) = split(/: /);
	                if ($field eq "general_comment")  { $general_comment = $field_value; }
		}
	}
	close (GROUP);
}

# Revise Group Comments

if ($action eq "Revise Group Comments") {

	open (GROUP,"<$group_file");
	while (<GROUP>) {
		$next_line = $_;
	        $key = substr($_,0,8);
	        if ($key eq " input: ") {
	                ($input,$field,$field_value) = split(/: /);
	                if ($field eq "general_comment") { $next_line = " input: general_comment: $general_comment\n"; }
	                if ($field eq "revision")  { $revision_num++; }
		}
		push (@group_lines,$next_line);
	}
	close (GROUP);

	open (GROUP,">$group_file");
	foreach $input_line (@group_lines) { print GROUP $input_line; }
	close (GROUP);

	if (($revision_comment ne "") && ($revision_num < 3)) {
		open (GROUP,">>$group_file");
		$revision_date = time - 60;
        	print GROUP " input: revision: $notate_graphs|$revision_date|$revision_comment\n";
		close (GROUP);
	}

	chmod $filter_file_perms, $group_file;
}

# Add a new component

if ($action eq "Add this Component") {

	$add_label    = $FORM{add_label};
	$add_location = $FORM{add_location};
	$add_color    = $FORM{add_color};

	$add_label =~ s/~/ /g;
	$add_file = $add_label;
	$add_file =~ s/^\s+//;
	$add_file =~ s/\s+$//;
	$add_file =~ s/\&/-/g;
	$add_file =~ s/\//-/g;
	$add_file =~ s/\(/-/g;
	$add_file =~ s/\)/-/g;
	$add_file =~ s/\./-/g;
	$add_file =~ s/\s+/_/g;
	$add_file =~ tr/[A-Z]/[a-z]/;

	$add_filter_file = "$filter_directory/$add_file.fil";
	open (COMPONENT,"<$add_filter_file");
	@add_lines = <COMPONENT>;
	close (COMPONENT);

	$group_monitor_type = "Bits per Second";
	foreach $add_line (@add_lines) {
		if ($add_line =~ / input: monitor_type/) {
			($left_part,$add_monitor_type) = split(/type: /,$add_line);
			if ($add_monitor_type =~ /fps/) { $group_monitor_type = "Flows per Second"; }
			if ($add_monitor_type =~ /pps/) { $group_monitor_type = "Packets per Second"; }
			last;
		}
	}

	open (GROUP,"<$group_file");
	@group_lines = <GROUP>;
	close (GROUP);

	foreach $group_line (@group_lines) {
		if ($group_line =~ / input:/) { push (@input_lines,$group_line); }
		else { push (@components,$group_line); }
	}

	$largest_above = 100;
	$largest_below = 200;

	foreach $component (@components) {

		($component_position,$component_label,$component_color) = split(/\^/,$component);

		if (($component_position<200) && ($component_position>$largest_above)) { $largest_above = $component_position; }
		if (($component_position>200) && ($component_position>$largest_below)) { $largest_below = $component_position; }

		if ($component_color =~ /auto mixed/) { 
			$next_mixed = substr($component_color,10,1);
			if ($component_position < 200) {
				if ($next_mixed > $largest_mixed_above) { $largest_mixed_above = $next_mixed; }
				$last_mixed_above = $next_mixed;
			}
			if ($component_position > 200) {
				if ($next_mixed > $largest_mixed_below) { $largest_mixed_below = $next_mixed; }
				$last_mixed_below = $next_mixed;
			}
		} 
		if ($component_color =~ /auto blue/) { 
			$next_blue = substr($component_color,9,1);
			if ($component_position < 200) {
				if ($next_blue > $largest_blue_above) { $largest_blue_above = $next_blue; }
				$last_blue_above = $next_blue;
			}
			if ($component_position > 200) {
				if ($next_blue > $largest_blue_below) { $largest_blue_below = $next_blue; }
				$last_blue_below = $next_blue;
			}
		} 
		if ($component_color =~ /auto red/) { 
			$next_red = substr($component_color,8,1);
			if ($component_position < 200) {
				if ($next_red > $largest_red_above) { $largest_red_above = $next_red; }
				$last_red_above = $next_red;
			}
			if ($component_position > 200) {
				if ($next_red > $largest_red_below) { $largest_red_below = $next_red; }
				$last_red_below = $next_red;
			}
		} 
		if ($component_color =~ /auto violet/) { 
			$next_violet = substr($component_color,11,1);
			if ($component_position < 200) {
				if ($next_violet > $largest_violet_above) { $largest_violet_above = $next_violet; }
				$last_violet_above = $next_violet;
			}
			if ($component_position > 200) {
				if ($next_violet > $largest_violet_below) { $largest_violet_below = $next_violet; }
				$last_violet_below = $next_violet;
			}
		} 
		if ($component_color =~ /auto green/) { 
			$next_green = substr($component_color,10,1);
			if ($component_position < 200) {
				if ($next_green > $largest_green_above) { $largest_green_above = $next_green; }
				$last_green_above = $next_green;
			}
			if ($component_position > 200) {
				if ($next_green > $largest_green_below) { $largest_green_below = $next_green; }
				$last_green_below = $next_green;
			}
		} 
	}

	$add_color_value = $add_color;
	$add_color =~ s/_/ /;

	if (($add_location eq "above") && ($add_color eq "auto mixed"))  { 
		if ($largest_mixed_above == $largest_mixed) {
			if ($last_mixed_above == $largest_mixed_above) { 
				$add_color = "auto mixed1";
			} else {
				$add_color .= $last_mixed_above + 1; }
		} else {
			$add_color .= $largest_mixed_above + 1;
		}
	}
	if (($add_location eq "above") && ($add_color eq "auto blue"))  { 
		if ($largest_blue_above == $largest_blue) {
			if ($last_blue_above == $largest_blue_above) { 
				$add_color = "auto blue1";
			} else {
				$add_color .= $last_blue_above + 1; }
		} else {
			$add_color .= $largest_blue_above + 1;
		}
	}
	if (($add_location eq "above") && ($add_color eq "auto red"))  { 
		if ($largest_red_above == $largest_red) {
			if ($last_red_above == $largest_red_above) { 
				$add_color = "auto red1";
			} else {
				$add_color .= $last_red_above + 1; }
		} else {
			$add_color .= $largest_red_above + 1;
		}
	}
	if (($add_location eq "above") && ($add_color eq "auto violet"))  { 
		if ($largest_violet_above == $largest_violet) {
			if ($last_violet_above == $largest_violet_above) { 
				$add_color = "auto violet1";
			} else {
				$add_color .= $last_violet_above + 1; }
		} else {
			$add_color .= $largest_violet_above + 1;
		}
	}
	if (($add_location eq "above") && ($add_color eq "auto green"))  { 
		if ($largest_green_above == $largest_green) {
			if ($last_green_above == $largest_green_above) { 
				$add_color = "auto green1";
			} else {
				$add_color .= $last_green_above + 1; }
		} else {
			$add_color .= $largest_green_above + 1;
		}
	}

	if (($add_location eq "below") && ($add_color eq "auto mixed"))  { 
		if ($largest_mixed_below == $largest_mixed) {
			if ($last_mixed_below == $largest_mixed_below) { 
				$add_color = "auto mixed1";
			} else {
				$add_color .= $last_mixed_below + 1; }
		} else {
			$add_color .= $largest_mixed_below + 1;
		}
	}
	if (($add_location eq "below") && ($add_color eq "auto blue"))  { 
		if ($largest_blue_below == $largest_blue) {
			if ($last_blue_below == $largest_blue_below) { 
				$add_color = "auto blue1";
			} else {
				$add_color .= $last_blue_below + 1; }
		} else {
			$add_color .= $largest_blue_below + 1;
		}
	}
	if (($add_location eq "below") && ($add_color eq "auto red"))  { 
		if ($largest_red_below == $largest_red) {
			if ($last_red_below == $largest_red_below) { 
				$add_color = "auto red1";
			} else {
				$add_color .= $last_red_below + 1; }
		} else {
			$add_color .= $largest_red_below + 1;
		}
	}
	if (($add_location eq "below") && ($add_color eq "auto violet"))  { 
		if ($largest_violet_below == $largest_violet) {
			if ($last_violet_below == $largest_violet_below) { 
				$add_color = "auto violet1";
			} else {
				$add_color .= $last_violet_below + 1; }
		} else {
			$add_color .= $largest_violet_below + 1;
		}
	}
	if (($add_location eq "below") && ($add_color eq "auto green"))  { 
		if ($largest_green_below == $largest_green) {
			if ($last_green_below == $largest_green_below) { 
				$add_color = "auto green1";
			} else {
				$add_color .= $last_green_below + 1; }
		} else {
			$add_color .= $largest_green_below + 1;
		}
	}

	$add_component = $add_label ."^". $add_color ."\n";;

	# Determine new position

	if (($add_location eq "above") && ($largest_above == 100)) {
		$add_component = $largest_above+1 ."^". $add_component;
		push (@new_group,$add_component);
	}

	foreach $component (@components) {

		($component_position,$component_label,$component_color) = split(/\^/,$component);
		push (@new_group,$component);
		if (($add_location eq "above") && ($component_position == $largest_above)) {
			$add_component = $largest_above+1 ."^". $add_component;
			push (@new_group,$add_component);
		}
		if (($add_location eq "below") && ($component_position == $largest_below)) {
			$add_component = $largest_below+1 ."^". $add_component;
			push (@new_group,$add_component);
		}
	}

	if (($add_location eq "below") && ($largest_below == 200)) {
		$add_component = $largest_below+1 ."^". $add_component;
		push (@new_group,$add_component);
	}

	# Rewrite group file

	open (GROUP,">$group_file");
	foreach $component (@new_group)    { print GROUP $component; }
	foreach $input_line (@input_lines) { print GROUP $input_line; }
	close (GROUP);
	chmod $filter_file_perms, $group_file;
}

# Adjust the group

if ($action eq "Adjust the Group") {

	open (GROUP,"<$group_file");
	@group_lines = <GROUP>;
	close (GROUP);

	foreach $group_line (@group_lines) {
		if ($group_line =~ / input:/) { 
			push (@input_lines,$group_line);
		} else { 
			push (@components,$group_line); 

			($component_position,$component_label,$component_color) = split(/\^/,$group_line);

			if ($component_color =~ /auto mixed/) { 
				$next_blue = substr($component_color,10,1);
				if ($component_position < 200) {
					if ($next_mixed > $largest_mixed_above) { $largest_mixed_above = $next_mixed; }
				}
				if ($component_position > 200) {
					if ($next_mixed > $largest_mixed_below) { $largest_mixed_below = $next_mixed; }
				}
			} 
			if ($component_color =~ /auto blue/) { 
				$next_blue = substr($component_color,9,1);
				if ($component_position < 200) {
					if ($next_blue > $largest_blue_above) { $largest_blue_above = $next_blue; }
				}
				if ($component_position > 200) {
					if ($next_blue > $largest_blue_below) { $largest_blue_below = $next_blue; }
				}
			} 
			if ($component_color =~ /auto red/) { 
				$next_red = substr($component_color,8,1);
				if ($component_position < 200) {
					if ($next_red > $largest_red_above) { $largest_red_above = $next_red; }
				}
				if ($component_position > 200) {
					if ($next_red > $largest_red_below) { $largest_red_below = $next_red; }
				}
			} 
			if ($component_color =~ /auto violet/) { 
				$next_violet = substr($component_color,11,1);
				if ($component_position < 200) {
					if ($next_violet > $largest_violet_above) { $largest_violet_above = $next_violet; }
				}
				if ($component_position > 200) {
					if ($next_violet > $largest_violet_below) { $largest_violet_below = $next_violet; }
				}
			} 
			if ($component_color =~ /auto green/) { 
				$next_green = substr($component_color,10,1);
				if ($component_position < 200) {
					if ($next_green > $largest_green_above) { $largest_green_above = $next_green; }
				}
				if ($component_position > 200) {
					if ($next_green > $largest_green_below) { $largest_green_below = $next_green; }
				}
			} 
		}
	}

	$largest_red_above++;
	$largest_blue_above++;
	$largest_green_above++;
	$largest_violet_above++;
	$largest_mixed_above++;
	$largest_red_below++;
	$largest_blue_below++;
	$largest_green_below++;
	$largest_violet_below++;
	$largest_mixed_below++;

	foreach $component (@components) {
		$num_components++;
		chop $component;	
		($component_position,$component_label,$component_color) = split(/\^/,$component);

		$new_color = "new_color_" . $component_position;
		$component_color = $FORM{$new_color};
		$component_color =~ s/_/ /;
		
		if ($component_position < 200) {
			if ($component_color eq "auto red") { $component_color = "auto_red" . $largest_red_above; }
			if ($component_color eq "auto blue") { $component_color = "auto_blue" . $largest_blue_above; }
			if ($component_color eq "auto green") { $component_color = "auto_green" . $largest_green_above; }
			if ($component_color eq "auto violet") { $component_color = "auto_violet" . $largest_violet_above; }
			if ($component_color eq "auto mixed") { $component_color = "auto_mixed" . $largest_mixed_above; }
		} else {
			if ($component_color eq "auto red") { $component_color = "auto_red" . $largest_red_below; }
			if ($component_color eq "auto blue") { $component_color = "auto_blue" . $largest_blue_below; }
			if ($component_color eq "auto green") { $component_color = "auto_green" . $largest_green_below; }
			if ($component_color eq "auto violet") { $component_color = "auto_violet" . $largest_violet_below; }
			if ($component_color eq "auto mixed") { $component_color = "auto_mixed" . $largest_violet_mixed }
		}

		$component = $component_position ."^". $component_label ."^". $component_color;
		push (@adjusted_components,$component);

		$adjust_component_color = $component_color;
		$adjust_component_color =~ s/_/ /;
		$component_data =  $component_label ."^". $adjust_component_color;
		$placements{$component_position} = $component_data;

		if (($component_position<200) && ($component_position>$largest_above)) { $largest_above = $component_position; }
		if (($component_position>200) && ($component_position>$largest_below)) { $largest_below = $component_position; }
	}

	foreach $position (keys (%placements)) {
		($component_label,$component_color) = split(/\^/,$placements{$position});
		$new_position = "new_position_" . $position;
		$move_component = $FORM{$new_position};
		if ($move_component eq "move_away") {
			if (($position == $largest_above) || ($position == $largest_below)) { next; }
			$temp_component = $placements{$position+1};
			$placements{$position+1} = $placements{$position};
			$placements{$position} = $temp_component;
		} elsif ($move_component eq "move_closer") {
			if (($position == 101) || ($position == 201)) { next; }
			$temp_component = $placements{$position-1};
			$placements{$position-1} = $placements{$position};
			$placements{$position} = $temp_component;
		} elsif ($move_component eq "remove") { 
			if ($position < 200) {
				if ($position == $largest_above) { 
					delete $placements{$position};
					$largest_above--;
					next;
				}
				for ($i=$position+1;$i<=$largest_above;$i++) { $placements{$i-1} = $placements{$i}; }
				delete $placements{$largest_above};
				$largest_above--;
			}
			if ($position > 200) {
				if ($position == $largest_below) { 
					delete $placements{$position};
					$largest_below--;
					next;
				}
				for ($i=$position+1;$i<=$largest_below;$i++) { $placements{$i-1} = $placements{$i}; }
				delete $placements{$largest_below};
				$largest_below--;
			}
		}
	}

	@sorted_keys = sort keys(%placements);
	foreach $position (@sorted_keys) {
		$component = $position ."^". $placements{$position};
		push (@sorted_components,$component);
	}

	open (GROUP,">$group_file");
	foreach $component (@sorted_components) { print GROUP "$component\n"; }
	foreach $input_line (@input_lines) { print GROUP $input_line; }
	close (GROUP);
	chmod $filter_file_perms, $group_file;
}

print " <div id=content_wide>\n";
print " <span class=text16>$monitor_label</span>\n";
print " <br>\n";

$end_rrd   = time;
$start_rrd = $end_rrd - 86400; 

# Gather existing components (if any) of this group

$num_components = 0;
$first_below    = 1;

open (GROUP,"<$group_file") || die "Can't open group file: $group_file";
while (<GROUP>) {
	$num_components++;
	chop;	

	if (/ input:/) { 
		$num_components--;
        	($input,$field,$field_value) = split(/: /);
                if ($field eq "revision") {  
     
                        ($notate_graphs,$revision_date,$revision_comment) = split(/\|/,$field_value);   
                        $revision_date_out = epoch_to_date($revision_date,"LOCAL");  
                        $revision_date_out =~ s/:/\\:/g; 
     
                        if ($notate_graphs eq "Y") {    
                                if ($vrule_1 eq "") {  
					$revision_date = $start_rrd + 21600;
                                        $vrule_1 = " VRULE:$revision_date#$rrd_vrule_color:\"$revision_date_out\\: $revision_comment\\n\"";  
                                        next; }   
                                elsif ($vrule_2 eq "") {  
					$revision_date = $start_rrd + 43200;
                                        $vrule_2 = " VRULE:$revision_date#$rrd_vrule_color:\"$revision_date_out\\: $revision_comment\\n\"";  
                                        next; }   
                                elsif ($vrule_3 eq "") {  
					$revision_date = $start_rrd + 64800;
                                        $vrule_3 = " VRULE:$revision_date#$rrd_vrule_color:\"$revision_date_out\\: $revision_comment\\n\"";  
                                        next; }   
                        }        
		}
		next;
	}

	($component_position,$component_label,$component_color) = split(/\^/,$_);

	$component_rrd = "$work_directory/COMPONENT_SAMPLE$num_components.rrd";

	$DEF_parameters  .= "DEF:flowbits$num_components=$component_rrd:flowbits:AVERAGE ";
        $AREA_parameters .= "COMMENT:\"     \" ";

	if ($component_position < 200) {
		$AREA_parameters .= "AREA:flowbits$num_components#$hex_colors{$component_color}:\"$component_label\\n\":STACK ";
	} elsif (($component_position >= 200) && ($first_below)) {
		$DEF_parameters .= "CDEF:flowbits_below$num_components=flowbits$num_components,-1,* ";
		$AREA_parameters .= "AREA:flowbits_below$num_components#$hex_colors{$component_color}:\"$component_label\\n\" ";
		$first_below = 0;
	} else {
		$DEF_parameters .= "CDEF:flowbits_below$num_components=flowbits$num_components,-1,* ";
		$AREA_parameters .= "AREA:flowbits_below$num_components#$hex_colors{$component_color}:\"$component_label\\n\":STACK ";
	}
}

# Generate Sample Graph from Sample RRDtool database

$rm_command = "rm -rf $monitor_directory/GROUPS/*";
system($rm_command);

$suffix = rand();
$suffix = int ($suffix * 100);
$graph_file      = "$monitor_directory/GROUPS/GROUP_SAMPLE$suffix.png";
$graph_file_link = "$monitor_short/GROUPS/GROUP_SAMPLE$suffix.png";

if ($num_components == 0) {

	$rrdtool_file    = "$work_directory/COMPONENT_SAMPLE.rrd";
	$rrdtool_command = "$rrdtool_bin_directory/rrdtool create $rrdtool_file ".  
			   "--step 300 ". 
	                   "--start $start_rrd ". 
	                   "DS:flowbits:GAUGE:600:U:U ".  
	                   "RRA:AVERAGE:0.5:1:600 ";  

	system($rrdtool_command);  
	chmod $rrd_file_perms, $rrdtool_file; 

	$DEF_parameters  .= "DEF:flowbits0$num_components=$rrdtool_file:flowbits:AVERAGE ";
        $AREA_parameters .= "COMMENT:\"     \" ";
	$AREA_parameters .= "AREA:flowbits0$num_components#FFFFFF::STACK ";
}

for ($i=1;$i<=$num_components;$i++) {

	$rrdtool_file    = "$work_directory/COMPONENT_SAMPLE$i.rrd";
	$rrdtool_command = "$rrdtool_bin_directory/rrdtool create $rrdtool_file ".  
			   "--step 300 ". 
	                   "--start $start_rrd ". 
	                   "DS:flowbits:GAUGE:600:U:U ".  
	                   "RRA:AVERAGE:0.5:1:600 ";  

	system($rrdtool_command);  
	chmod $rrd_file_perms, $rrdtool_file; 

	$num_point = 0;
	for ($j=1;$j<=4;$j++) { 
	        for ($k=-36;$k<36;$k++) { 
	                $num_point++;  
	                $next_time = $start_rrd + ($num_point * 300);  
	                $x = ($k / 36) * 3.14159; 
			$sinx = sin ($x);
	                $next_value = int(300000 + ($sinx * 30000)); 
			RRDs::update ("$rrdtool_file","$next_time:$next_value");
			$ERR=RRDs::error;
			if (($debug_group eq "Y") && ($ERR ne "")) { print DEBUG "RRDs ERR: $ERR\n"; }
	        }        
	} 
}

$monitor_label_out = $monitor_label;
$monitor_label =~ s/\s+$//;
$monitor_label_out =~ s/\s+/_/g;
$rrd_title = $monitor_label_out . "_Sample";

@graph_parameters = 
        ('--title',"$rrd_title", 
        '--start',$start_rrd, 
        '--end',$end_rrd, 
        '--width',$rrd_width, 
        '--height',$rrd_height, 
        '--interlace', 
        '--vertical-label',"\"$group_monitor_type\"", 
        $rrd_slope_mode, 
        "--color=FONT#$rrd_font", 
        "--color=BACK#$rrd_back", 
        "--color=CANVAS#$rrd_canvas", 
        "--color=GRID#$rrd_grid", 
        "--color=MGRID#$rrd_mgrid", 
        "--color=FRAME#$rrd_frame", 
        "--color=SHADEA#$rrd_frame", 
        "--color=SHADEB#$rrd_frame", 
        '--lower-limit',$rrd_lower_limit, 
	'--alt-autoscale',
	$DEF_parameters,
        "COMMENT:\"\\n\"", 
	$AREA_parameters,
        "COMMENT:\"\\n\"", 
        "COMMENT:\"     \"", 
        $vrule_1, 
        "COMMENT:\"     \"", 
        $vrule_2, 
        "COMMENT:\"     \"", 
        $vrule_3);

$rrdgraph_command = "$rrdtool_bin_directory/rrdtool graph " . "$graph_file " . "@graph_parameters " . ">/dev/null";
if ($debug_group eq "Y") { print DEBUG "rrdgraph_command: $rrdgraph_command\n"; }
system($rrdgraph_command);
chmod $monitor_file_perms, $graph_file;

print " <br>\n";
print " <img src=$graph_file_link>\n";
print " <br><hr><br>\n";

# Clean up temporary COMPONENT RRD files

$cleanup_command = "rm $work_directory/COMPONENT_SAMPLE*";
if ($debug_files ne "Y") { system($cleanup_command); }

# Build list of existing monitors to select from

print " <br>\n";
print " <table>\n";
print " <tr><td align=center colspan=2><b>Select an existing Monitor to be a component of this Group:</b></td></tr>\n";
print " <tr><td width=300>&nbsp</td><td width=300>&nbsp</td></tr>\n";
print " <tr><td align=right><form action=$cgi_bin_short/FlowMonitor_Group.cgi?$active_dashboard^Adjust^ method=POST>\n";
print " Select a Component: &nbsp&nbsp</td><td align=left> <select name=add_label length=15>\n";  

while ($filter_file = <$filter_directory/*>) { 
        ($directory,$monitor) = $filter_file =~ m/(.*\/)(.*)$/; 
        ($monitor,$extension) = split(/\./,$monitor); 

	if ($extension eq "fil") {
		$grep_command = "egrep '(tracking_label|monitor_label)' $filter_file";
		open(GREP,"$grep_command 2>&1|"); 
		while (<GREP>) {
			chop;
			($input,$label,$monitor) = split(/:/);
			$monitor = substr($monitor,1,100);
			print "    <option value=\"$monitor\">$monitor\n";  
		}
	}
}
print "    </select></td></tr>\n\n"; 

print " <tr><td align=right>Place this Component: &nbsp&nbsp</td><td align=left><select name=add_location length=15>\n";  
print " <option selected value=above>Above the X-axis\n";  
print " <option value=below>Below the X-axis\n";  
print " </select></td></tr>\n"; 

print " <tr><td align=right>Select a Color: &nbsp&nbsp</td><td align=left><select name=add_color length=15>\n";  

if (substr($add_color,0,9) eq "auto blue") { 
	print "<option selected value=auto_blue>Auto Blue\n";  
	print "<option value=auto_red>Auto Red\n";  
	print "<option value=auto_green>Auto Green\n";  
	print "<option value=auto_violet>Auto Violet\n";  
	print "<option value=auto_mixed>Auto Mixed\n";  
} elsif (substr($add_color,0,8) eq "auto red") { 
	print "<option selected value=auto_red>Auto Red\n";  
	print "<option value=auto_blue>Auto Blue\n";  
	print "<option value=auto_green>Auto Green\n";  
	print "<option value=auto_violet>Auto Violet\n";  
	print "<option value=auto_mixed>Auto Mixed\n";  
} elsif (substr($add_color,0,10) eq "auto green") { 
	print "<option selected value=auto_green>Auto Green\n";  
	print "<option value=auto_red>Auto Red\n";  
	print "<option value=auto_blue>Auto Blue\n";  
	print "<option value=auto_violet>Auto Violet\n";  
	print "<option value=auto_mixed>Auto Mixed\n";  
} elsif (substr($add_color,0,11) eq "auto violet") { 
	print "<option selected value=auto_violet>Auto Violet\n";  
	print "<option value=auto_red>Auto Red\n";  
	print "<option value=auto_blue>Auto Blue\n";  
	print "<option value=auto_green>Auto Green\n";  
	print "<option value=auto_mixed>Auto Mixed\n";  
} else {
	print "<option selected value=auto_mixed>Auto Mixed\n";  
	print "<option value=auto_green>Auto Green\n";  
	print "<option value=auto_violet>Auto Violet\n";  
	print "<option value=auto_red>Auto Red\n";  
	print "<option value=auto_blue>Auto Blue\n";  
}

open (COLORS,"<$cgi_bin_directory/FlowGrapher_Colors");
while (<COLORS>) {
	($r,$g,$b,$color1,$color2) = split(/\s+/,$_);
	$next_color = "$color1";
	$next_value = "$color1";
	if ($color2 ne "") { $next_color = $color1 ." ". $color2; }
	if ($color2 ne "") { $next_value = $color1 ."_". $color2; }
	$color_choice=  "    <option value=$next_value>$next_color\n";  
	print $color_choice;
	push(@color_choices,$color_choice);
}
print " </select></td></tr>\n"; 
print " </table>\n";
print " <br>\n";
print " <table>\n";
print " <td><button class=links type=submit name=action value=\"Add this Component\">Add Component</button></td>\n";
print " <td width=70></td>\n";
print " <td><button class=links type=reset name=action value=\"Reset Values\">Reset Values</button></td>\n";
print " </table>\n";
print " <input type=hidden name=monitor_label value=\"$monitor_label\">\n"; 
print " <input type=hidden name=general_comment value=\"$general_comment\">\n"; 
print " </form>\n";
print " <br>\n";
print " <br><hr><br>\n";

# List the components so that a user can modify them, their position, their order, or their color

print " <br>\n";
print " <form action=$cgi_bin_short/FlowMonitor_Group.cgi?$active_dashboard^Adjust^ method=POST>";
print " <table>\n";
print " <tr><td align=center colspan=7><b>This group is composed of these components:</b></td></tr>\n";
print " <tr><td>&nbsp</td></tr>\n";

open (GROUP,"<$group_file");
@components = <GROUP>;
close (GROUP);

$num_components = 0;
foreach $component (@components) {

	$num_components++;

	if ($component =~ / input:/) { $num_components--; next; }

	chop $component;	
	($component_position,$component_label,$component_color) = split(/\^/,$component);

	$component_label =~ s/~/ /g;
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
	$component_file = "MT_" . $component_file;

	$component_link = "<a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$component_file>$component_label</a>";

	$component_color_value = $component_color;
	$component_color_value =~ s/ /_/;
	$color_link = "<font color=$hex_colors{$component_color}>$component_color</font>";

	$axis_position  = substr($component_position,0,1);
	$stack_position = substr($component_position,1,2);
	if ($axis_position == 1) {
		$component_position_out = "Above ";
	} else {
		$component_position_out = "Below ";
	}
	$component_position_out .= $stack_position;

	$next_component = $component_position ."##". $component_position_out ."##". $component_link ."##". $color_link ."##". $component_color ."##". $component_color_value;
	if ($component_position < 200) { push (@upper_components,$next_component); }
	if ($component_position > 200) { push (@lower_components,$next_component); }
}

# Print out components that appear ABOVE the axis

@reversed_uppers = reverse (@upper_components);
foreach $upper_component (@reversed_uppers) {

	($component_position,$component_position_out,$component_link,$color_link,$component_color,$component_color_value) = split(/##/,$upper_component);

	print " <tr><td width=300 align=right>$component_link&nbsp&nbsp&nbsp&nbsp</td><td width=60>$component_position_out</td><td width=120><b>&nbsp&nbsp&nbsp&nbsp $color_link</b></td>\n";

	$new_color = "new_color_" . $component_position;
	print "<td width=80 align=right>New Color:&nbsp</td><td width=120><select name=$new_color length=15>\n";  
	print "<option selected value=$component_color_value>$component_color\n";  
	print "<option value=auto_blue>Auto Blue\n";  
	print "<option value=auto_red>Auto Red\n";  
	print "<option value=auto_green>Auto Green\n";  
	print "<option value=auto_violet>Auto Violet\n";  
	print "<option value=auto_mixed>Auto Mixed\n";  
	foreach $color_choice (@color_choices) { print $color_choice; }
	print "</select></td>"; 

	$new_position = "new_position_" . $component_position;
	print "<td width=60 align=right>Move:&nbsp</td><td width=120><select name=$new_position length=15>\n";  
	print "<option selected value=leave_alone>Leave Alone\n";  
	print "<option value=move_away>Move Away from Axis\n";  
	print "<option value=move_closer>Move Closer to Axis\n";  
	print "<option value=remove>Remove\n";  
	print "</select></td></tr>\n"; 
}
print " </table>\n";

# Print out components that appear BELOW the axis

if (@lower_components) { print " <hr>\n"; }

print " <table>\n";
foreach $lower_component (@lower_components) {

	($component_position,$component_position_out,$component_link,$color_link,$component_color,$component_color_value) = split(/##/,$lower_component);

	print " <tr><td width=300 align=right>$component_link&nbsp&nbsp&nbsp&nbsp</td><td width=60>$component_position_out</td><td width=120><b>&nbsp&nbsp&nbsp&nbsp $color_link</b></td>\n";

	$new_color = "new_color_" . $component_position;
	print "<td width=80 align=right>New Color:&nbsp</td><td width=120><select name=$new_color length=15>\n";  
	print "<option selected value=$component_color_value>$component_color\n";  
	print "<option value=auto_blue>Auto Blue\n";  
	print "<option value=auto_red>Auto Red\n";  
	print "<option value=auto_green>Auto Green\n";  
	print "<option value=auto_violet>Auto Violet\n";  
	print "<option value=auto_mixed>Auto Mixed\n";  
	foreach $color_choice (@color_choices) { print $color_choice; }
	print "</select></td>"; 

	$new_position = "new_position_" . $component_position;
	print "<td width=60 align=right>Move:&nbsp</td><td width=120><select name=$new_position length=15>\n";  
	print "<option selected value=leave_alone>Leave Alone\n";  
	print "<option value=move_away>Move Away from Axis\n";  
	print "<option value=move_closer>Move Closer to Axis\n";  
	print "<option value=remove>Remove\n";  
	print "</select></td>\n"; 
}

print " </table>\n";
print " <br>\n";
print " <table>\n";
print " <td><button class=links type=submit name=action value=\"Adjust the Group\">Adjust the Group</button></td>\n";
print " <td width=70></td>\n";
print " <td><button class=links type=reset name=action value=\"Reset Values\">Reset Values</button></td>\n";
print " </table>\n";
print " <input type=hidden name=monitor_label value=\"$monitor_label\">\n"; 
print " <input type=hidden name=general_comment value=\"$general_comment\">\n"; 
print " </form>\n";
print " <br>\n";
print " <br><hr =800><br>\n";

# List out current Comment and Revision input

print "<form action=$cgi_bin_short/FlowMonitor_Group.cgi?$active_dashboard^Adjust^ method=POST>";
print " <br>\n";
print " <table>\n";
print " <tr><td align=center colspan=2><b>Change Comment or add a Revision Mark (Maximum three revisions):</b></td></tr>\n";
print " <tr><td>&nbsp</td></tr>\n";
print " <tr><td align=right>General Comment:&nbsp</td><td><input type=text class=left_group name=general_comment value=\"$general_comment\"></td></tr>\n"; 
$revision_comment = "";
print " <tr><td align=right>Revision Comment:&nbsp</td><td><input type=text class=left_group name=revision_comment value=\"$revision_comment\">\n"; 
print " <tr><td align=right>Notate Graphs:&nbsp</td><td><select name=notate_graphs width=4>\n";   
print "    <option selected value=N>N\n";
print "    <option value=Y>Y\n";
print "    </select> (To notate graphs with time and description of revision)";
print "</td></tr>\n";
print " </table>\n";
print " <br>\n";
print " <table>\n";
print " <td><button class=links type=submit name=action value=\"Revise Group Comments\">Revise Comments</button></td>\n";
print " <td width=70></td>\n";
print " <td><button class=links type=reset name=action value=\"Reset Values\">Reset Values</button></td>\n";
print " </table>\n";
print " <input type=hidden name=monitor_label value=\"$monitor_label\">\n"; 
print " </form>\n";
print " <br>\n";
print " <br><hr><br>\n";

# Print Done button

print " <br>\n";

print " <form action=$cgi_bin_short/FlowMonitor_Group.cgi?$active_dashboard^Done^ method=POST>";
print " <table>";
print " <input type=hidden name=monitor_label value=\"$monitor_label\">\n"; 
print " <input type=hidden name=general_comment value=\"$general_comment\">\n"; 
print " <input type=hidden name=revision_comment value=\"$revision_comment\">\n"; 
print " <td><button class=links type=submit name=action value=Done>Done</button></td>\n";
print " </table>";
print " </form>";

print " </div>\n";

&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowMonitor_Main");
