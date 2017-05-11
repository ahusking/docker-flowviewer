#! /usr/bin/perl
#
#  Purpose:
#  FlowViewer_Replay.cgi re-displays a saved FlowViewer Report
#
#  Description:
#
#  FlowViewer_Replay.cgi builds the FlowViewer webpage framework
#  and simply copies the saved contents into the user's display.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  none      
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Original version.
#  J. Loiacono  04/15/2013      4.1     Removed extraneuos formatting
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards; empty flags field
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

if ($debug_viewer eq "Y") { open (DEBUG,">>$work_directory/DEBUG_SAVE"); } 

$query_string  = $ENV{'QUERY_STRING'};
$query_string  =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge;
($active_dashboard,$filter_hash_string) = split(/\^/,$query_string);
($label,$filter_hash) = split(/=/,$filter_hash_string);
$filter_source = substr($filter_hash,0,2);
$hash_file     = substr($filter_hash,3,255);

if ($active_dashboard eq "") {
	if (@dashboard_titles) {
		$active_dashboard = @dashboard_titles[0];
		$active_dashboard =~ s/ /~/;
	} else {
		$active_dashboard = "Main_Only";
	}
}

if (($filter_source eq "FL") || ($filter_source eq "SC")) {
	# Do a Replay of a currenly active FlowViewer Report for Filter savers
	$filter_hash   = "FV_" . $hash_file;
	$saved_FV_file = "$work_directory/$hash_file";
	$saved_FV_png  = "$graphs_directory/$hash_file.png";
	if ($filter_source eq "SC") { $is_scan_replay = 1; }
} else {
	$filter_hash   = "SV_" . $hash_file;
	$saved_FV_file = "$save_directory/$hash_file";
	$saved_FV_png  = "$save_directory/$hash_file.png";
}

if ($debug_viewer eq "Y") { print DEBUG "In FlowViewer_Replay.cgi  filter_source: $filter_source  filter_hash: $filter_hash  saved_suffix: $saved_suffix  saved_FV_png: $saved_FV_png  saved_FV_file: $saved_FV_file\n"; }

# Handle saved reports from previous (PV) FlowViewer Versions differently

if ($filter_source eq "PV") {

        ($directory,$saved_label) = $saved_FV_file =~ m/(.*\/)(.*)$/;
        $last_underscore = rindex($saved_label,"_"); $len_label = $last_underscore - 16;
        $pv_report_name = substr($saved_label,16,$len_label);
        $pv_suffix = &get_suffix;
        $filter_hash = "PV_FlowViewer_replay_$pv_suffix";
        $pv_filter_file = "$work_directory/FlowViewer_replay_$pv_suffix";

        &create_UI_top($active_dashboard);
        &create_UI_service("FlowViewer","service_top",$active_dashboard,$filter_hash);
        print " <div id=content_wide>\n";

        $grep_command = "grep Multiplier: $saved_FV_file";
        open(GREP,"$grep_command 2>&1|");
        while (<GREP>) {
                chop;
                ($field_name,$field_value) = split(/plier: /);
                $FILTER{sampling_multiplier} = $field_value;
        }

        open(SAVED,"<$saved_FV_file");
        chomp (@saved_FV_lines = <SAVED>);
        close SAVED;

        $header_line = 1;
        $first_blank = 1;

        foreach $saved_FV_line (@saved_FV_lines) {

                if ($saved_FV_line =~ "Packets") {
                        $print_header = 1;
                        $header_line = 0;
                }

                &type_of_line;

                if ($header_line) {
                        if ($saved_FV_line =~ "Report:") {
                                $start_report = index($saved_FV_line,"Report:");
                                $start_report--;
                                $saved_FV_line = substr($saved_FV_line,$start_report,300);
                                $first_half  = substr($saved_FV_line,0,57);
                                $second_half = substr($saved_FV_line,57,400);
                        } else {
                                $first_half  = substr($saved_FV_line,0,57);
                                $second_half = substr($saved_FV_line,57,400);
                        }
                }

                if (($header_line) && ($regular_line)) {

                        $last_field = "";

                        if ($saved_FV_line =~ "Report:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $report_name = $field_value;
				&get_report_number;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{sort_field} = $field_value;

                        } elsif ($saved_FV_line =~ "Start Time:") {

                                ($field_name,$field_value) = split(/: /,$first_half);
                                ($pv_mn,$pv_da,$pv_yr,$pv_time) = split(/\s+/,$field_value);
                                $pv_mn = substr($pv_mn,0,3);
                                $pv_mn = &convert_month($pv_mn);
                                chop $pv_da;
                                if (length($pv_da) == 1) { $pv_da = "0" . $pv_da; }
                                $pv_start = $pv_mn ."/". $pv_da ."/". $pv_yr;
                                $FILTER{start_date} = $pv_start;
                                $FILTER{start_time} = $pv_time;

                                ($field_name,$field_value) = split(/: /,$second_half);
                                ($pv_mn,$pv_da,$pv_yr,$pv_time) = split(/\s+/,$field_value);
                                $pv_mn = substr($pv_mn,0,3);
                                $pv_mn = &convert_month($pv_mn);
                                chop $pv_da;
                                if (length($pv_da) == 1) { $pv_da = "0" . $pv_da; }
                                $pv_end = $pv_mn ."/". $pv_da ."/". $pv_yr;
                                $FILTER{end_date} = $pv_end;
                                $FILTER{end_time} = $pv_time;

                        } elsif ($saved_FV_line =~ "Device:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{device_name} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{exporter} = $field_value;

                        } elsif ($saved_FV_line =~ "Source:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_addresses} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_addresses} = $field_value;

                                $last_field = "source_addresses";

                        } elsif ($saved_FV_line =~ "Source Port:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_ports} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_ports} = $field_value;

                                $last_field = "source_ports";

                        } elsif ($saved_FV_line =~ "Src I/F Name:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
				$lparen = index($field_value,"\(");
				$rparen = index($field_value,"\)");
				$start_index = $lparen + 1;
				$len_index = $rparen - $lparen - 1;
				$sif_names = substr($field_value,$start_index,$len_index);
                                $FILTER{sif_names} = $sif_names;

                                ($field_name,$field_value) = split(/:/,$second_half);
				$lparen = index($field_value,"\(");
				$rparen = index($field_value,"\)");
				$start_index = $lparen + 1;
				$len_index = $rparen - $lparen - 1;
				$dif_names = substr($field_value,$start_index,$len_index);
                                $FILTER{dif_names} = $dif_names;

                                $last_field = "sif_names";

                        } elsif ($saved_FV_line =~ "Source I/F:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_ifs} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_ifs} = $field_value;

                                $last_field = "source_ifs";

                        } elsif ($saved_FV_line =~ "Source AS:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_ases} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_ases} = $field_value;

                                $last_field = "source_ases";

                        } elsif ($saved_FV_line =~ "TOS Field:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{tos_fields} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{tcp_flags} = $field_value;

                                $last_field = "tos_fields";

                        } elsif ($saved_FV_line =~ "Include if:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $include_key = substr($field_value,1,3);
                                if ($include_key eq "Any") { $FILTER{flow_select} = 1; }
                                if ($include_key eq "End") { $FILTER{flow_select} = 2; }
                                if ($include_key eq "Sta") { $FILTER{flow_select} = 3; }
                                if ($include_key eq "Ent") { $FILTER{flow_select} = 4; }

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{protocols} = $field_value;

                                $last_field = "flow_select";

                        } elsif ($saved_FV_line =~ "Cutoff Lines:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{cutoff_lines} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{cutoff_octets} = $field_value;

                        } elsif ($saved_FV_line =~ "Lines Cutoff:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{cutoff_lines} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{cutoff_octets} = $field_value;

                        } elsif ($saved_FV_line =~ "Description:") {

                                ($field_name,$field_value) = split(/: /,$first_half);
                                $description = $field_value . $second_half;
                                $description =~ s/\s+$//;
                                $FILTER{description} = $description;
                                $pv_report_name = $description;
                        }

                } elsif (($header_line) && ($continuation_line)) {

                        if ($last_field eq "source_addresses") {
                                $FILTER{source_addresses} .= $first_half;
                                $FILTER{dest_addresses} .= $second_half;
                        }
                        if ($last_field eq "source_ports") {
                                $FILTER{source_ports} .= $first_half;
                                $FILTER{dest_ports} .= $second_half;
                        }
                        if ($last_field eq "source_ifs") {
                                $FILTER{source_ifs} .= $first_half;
                                $FILTER{dest_ifs} .= $second_half;
                        }
                        if ($last_field eq "sif_names") {
                                $FILTER{sif_names} .= $first_half;
                                $FILTER{dif_names} .= $second_half;
                        }
                        if ($last_field eq "source_ases") {
                                $FILTER{source_ases} .= $first_half;
                                $FILTER{dest_ases} .= $second_half;
                        }
                        if ($last_field eq "tos_fields") {
                                $FILTER{tos_fields} .= $first_half;
                                $FILTER{tcp_flags} .= $second_half;
                        }
                        if ($last_field eq "flow_select") {
                                $FILTER{protocols} .= $second_half;
                        }
                }

                if (($saved_FV_line =~ "Cutoff") && ($noformat)) {
                        $print_header = 1;
                        $header_line = 0;
                }

                if ($header_line) { next; }

                if ($print_header) {

                        # Save a temporary filter for the user to invoke a new report from existing report

                        foreach $field_name (keys (%FILTER)) {
                                if ($field_name eq "description") { next; }
                                if (($field_name ne "sif_names") && ($field_name ne "dif_names"))  { $FILTER{$field_name} =~ s/\s+//g; }
                                $FILTER{$field_name} =~ s/,/, /g;
                        }

                        $device_name = $FILTER{device_name};
			$stat_report = $FILTER{stat_report};
			$print_report = $FILTER{print_report};
                        $exporter = $FILTER{exporter};
                        $start_date = $FILTER{start_date};
                        $start_time = $FILTER{start_time};
                        $end_date = $FILTER{end_date};
                        $end_time = $FILTER{end_time};
                        $source_addresses = $FILTER{source_addresses};
                        $dest_addresses = $FILTER{dest_addresses};
                        $source_ports = $FILTER{source_ports};
                        $dest_ports = $FILTER{dest_ports};
                        $source_ifs = $FILTER{source_ifs};
                        $sif_names = $FILTER{sif_names};
                        $dest_ifs = $FILTER{dest_ifs};
                        $dif_names = $FILTER{dif_names};
                        $source_ases = $FILTER{source_ases};
                        $dest_ases = $FILTER{dest_ases};
                        $tos_fields = $FILTER{tos_fields};
                        $tcp_flags = $FILTER{tcp_flags};
                        $protocols = $FILTER{protocols};
                        $flow_select = $FILTER{flow_select};
                        $cutoff_lines = $FILTER{cutoff_lines};
                        $cutoff_octets = $FILTER{cutoff_octets};
                        $description = $FILTER{description};
                        $sampling_multiplier = $FILTER{sampling_multiplier};
			$sort_field = $FILTER{sort_field};

                        start_saved_file($pv_filter_file);

                        print "  <br>\n";
                        print "  <span class=text16>$pv_report_name</span>\n";
                        print "  <br>\n";

                        &create_filter_output("FlowViewer",$filter_hash);

			if (!$noformat) {
				($h1,$h2,$h3,$h4,$h5,$h6,$h7) = split(/\s+/,$saved_FV_line);
				if ($merge_one) { $h1 = $h1 ." ". $h2; $h3 = $h4; $h4 = $h5; $h5 = $h6; $h6 = ""; $h7 = "";}
				if ($merge_two) { $h1 = $h1 ." ". $h2; $h2 = $h3 ." ". $h4; $h3 = $h5; $h4 = $h6; $h5 = $h7; $h6 = ""; $h7 = "";}
				$num_columns = 6;
				if ($h6 eq "") { $num_columns = 5; }
				if ($h5 eq "") { $num_columns = 4; }
				if ($h6 =~ "Avg") { 
					$num_columns = 6;
					$h6 = "Avg Rate(bps)";
				}
				if ($sampling_multiplier > 0) {
					if ($h6 ne "") { $h6 .= "*"; $h5 .= "*"; $h4 .= "*"; $h3 .= "*";}	
					if (($h6 eq "") && ($h5 ne "")) { $h5 .= "*"; $h4 .= "*"; $h3 .= "*"; }	
					if (($h6 eq "") && ($h5 eq "")) { $h4 .= "*"; $h3 .= "*"; $h2 .= "*"; }	
				}
				print "<br>\n";
				print "<table><tr>\n";
				print "<td>$h1</td>\n";
				print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$h2</td>\n";
				print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$h3</td>\n";
				print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$h4</td>\n";
				if ($num_columns >= 5) { print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$h5</td>\n"; }
				if ($num_columns == 6) { print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$h6</td>\n"; }
				print "</tr>\n";
			} else {
				print " <font face=courier><pre>\n";
			}

                        $print_header = 0;
                        $first_blank = 0;
			next;
                }

                if ($saved_FV_line =~ "Map")        { next; }
                if ($saved_FV_line =~ "shape=rect") { next; }
                if ($saved_FV_line =~ "map>")       { next; }

		if (!$noformat) {
	                ($x1,$x2,$x3,$x4,$x5,$x6,$x7) = split(/\s+/,$saved_FV_line);
			if (($num_columns == 4) && ($x4 =~ "B")) { $x3 = $x3 ." ". $x4; $x4 = $x5; $x5 = ""; }
			if (($num_columns == 5) && ($x5 =~ "B")) { $x4 = $x4 ." ". $x5; $x5 = $x6; $x6 = ""; }
			if (($num_columns == 6) && ($x5 =~ "B")) { $x4 = $x4 ." ". $x5; $x5 = $x6; $x6 = $x7; $x7 = ""; }
	                print "<tr><td>$x1</td><td>&nbsp&nbsp&nbsp&nbsp&nbsp$x2</td><td align=right>&nbsp&nbsp&nbsp&nbsp&nbsp$x3</td>";
	                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$x4</td><td>&nbsp&nbsp&nbsp&nbsp&nbsp$x5</td>\n";
	                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$x6</td></td><tr>";
		} else {
			print "$saved_FV_line\n";
		}
        }

        print " </table>\n";
        print " </font>\n";
        print " </div>\n";

        &create_UI_service("FlowViewer","service_bottom",$active_dashboard,$filter_hash);
        &finish_the_page("FlowViewer");
        exit;
}

# Load the saved FlowViewer file

open(SAVED,"<$saved_FV_file");
chomp (@saved_FV_lines = <SAVED>);
close SAVED;

foreach $saved_FV_line (@saved_FV_lines) {
        $line_number++;
        if ($saved_FV_line =~ /BEGIN FILTERING/) { $found_parameters = 1; next; }
        if ($found_parameters) {
                if ($saved_FV_line =~ /END FILTERING/) {
                        $found_parameters = 0;
                        $head_line = 1;
                        next;
                }
                ($field,$field_value) = split(/: /,$saved_FV_line);
                if ($field eq "device_name")         { $device_name = $field_value; }
                if ($field eq "sampling_multiplier") { $sampling_multiplier = $field_value; }
                if ($field eq "resolve_addresses")   { $resolve_addresses = $field_value; }
                if ($field eq "stat_report")         { $stat_report = $field_value; }
                if ($field eq "print_report")        { $print_report = $field_value; }
                if ($field eq "unit_conversion")     { $unit_conversion = $field_value; }
                if ($field eq "IPFIX")               { $IPFIX = $field_value; }
		if ($field eq "Description")         { $report_name = $field_value; }
		if ($field eq "flow_analysis")       { $flow_analysis = $field_value; }
		next;
	}
        if ($head_line) {
                ($head1,$head2,$head3,$head4,$head5,$head6,$head7,$head_8) = split(/ : /,$saved_FV_line);
                $head_line = 0;
		if ($head1 =~ /<table>/) { $scan_report = 1; }
		$start_report_line = $line_number;
                next;
        }
}
$report_lines = $line_number;

if (($stat_report == 8)  || ($stat_report == 9)  || ($stat_report == 11)) { $country_report = 1; }
if (($stat_report == 10) || ($stat_report == 21) || ($stat_report == 23) || ($stat_report == 26)) { $rate_report = 1; }

if ($filter_source eq "FL") { $report_name = "FlowViewer Report from $device_name &nbsp&nbsp&nbsp [Filter Saved]"; }
if ($filter_source eq "SC") { $report_name = "FlowViewer Report from $device_name"; }

# Start the page ...

&create_UI_top($active_dashboard);
&create_UI_service("FlowViewer","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";
print " <span class=text16>$report_name</span>\n";

# Replay the FlowViewer Content

&create_filter_output("FlowViewer",$filter_hash);

if ($filter_source eq "SV") { 
	$piechart_link = "$save_short/$hash_file.png";
	$piechart_full = "$save_directory/$hash_file.png";
} else { 
	$piechart_link = "$graphs_short/$hash_file.png";
	$piechart_full = "$graphs_directory/$hash_file.png";
}
if (-e $piechart_full) { print " <center><img src=$piechart_link></center>\n"; }

# Output the column headers

if ($scan_report) {

	for ($m=$start_report_line;$m<=$report_lines;$m++) {
		print $saved_FV_lines[$m];
		if ($saved_FV_lines[$m] =~ /were discovered/) { print "<br>\n"; }
	}
	print "<tr><td>&nbsp</td></tr>\n";
	print "<tr><td>&nbsp</td></tr>\n";
	print " </table>\n";
	print " </div>\n";
	
	# ... end the page
	
	&create_UI_service("FlowViewer_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowViewer");
	exit;
}

if ($stat_report == 30) {
	$start_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Start^$ascend>Start</a>";
	$end_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^End^$ascend>End</a>";
	$sif_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Sif^$ascend>Sif</a>";
	$source_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Source^$ascend>Source</a>";
	$srcp_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^SrcP^$ascend>SrcP</a>";
	$dif_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Dif^$ascend>Dif</a>";
	$dest_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Dest^$ascend>Dest</a>";
	$dstp_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^DstP^$ascend>DstP</a>";
	$proto_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Proto^$ascend>Proto</a>";
	$flags_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Flags^$ascend>Flags</a>";
} else {
	$source_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Source^$ascend>$head1</a>";
	$dest_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Dest^$ascend>$head2</a>";
	$octfl_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^OctFlow^$ascend>Octs/Flow</a>";
	$pktfl_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^PktFlow^$ascend>Pkts/Flow</a>";
	$country_link= "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Country^$ascend>Country</a>";
}
if ($sampling_multiplier <= 1) {
        $flows_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Flows^$ascend>Flows</a>";
        $octets_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Octets^$ascend>Octets</a>";
        $packets_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Packets^$ascend>Packets</a>";
        $mbps_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Mbps^$ascend>Avg. Rate</a>";
} else {
        $flows_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Flows^$ascend>Flows*</a>";
        $octets_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Octets^$ascend>Octets*</a>";
        $packets_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Packets^$ascend>Packets*</a>";
        $mbps_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Mbps^$ascend>Avg. Rate*</a>";
}

if (((!$IPFIX) && ($print_report > 0)) || (($IPFIX) && ($print_report > 0) && ($print_report < 12)) || ($stat_report == 99)) {
	print "<pre><font face=\"Courier New\">\n";
	$start_report_line = $start_report_line - 1;

} elsif ($stat_report == 30) {

	print "  <br>\n";
	print "  <center>\n";
	print "  <table>\n";
	print "  <tr>\n";
	print "<td align=left>$start_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$end_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$sif_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$source_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$srcp_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$dif_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$dest_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$dstp_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$proto_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$flags_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$packets_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=right>$octets_link</td>\n";
	print "  </tr>\n";
	print "  <tr><td>&nbsp&nbsp</td></tr>\n";

} else {

	print "  <br>\n";
	print "  <center>\n";
	print "  <table>\n";
	print "  <tr>\n";
	print "<td align=left>$source_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	if ($head2 ne "Flows") {
	        print "<td align=left>$dest_link</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	}
	print "  <td align=right>$flows_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "  <td align=right>$octets_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "  <td align=right>$packets_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	if ($rate_report) { print "  <td align=right>$mbps_link</td>\n"; }
	if ($flow_analysis) {
		if ($rate_report) { print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n"; }
		print "<td align=right>$octfl_link</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$pktfl_link</td>\n";
		if ($country_report) { 
			print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
			print "<td align=right>$country_link</td>\n";
		}
	}
	print "  </tr>\n";
	print "  <tr><td>&nbsp&nbsp</td></tr>\n";

	$short_fields = 0;
	if ($resolve_columns == 0) {
	        if (($stat_report ==  5) || ($stat_report ==  6) || ($stat_report ==  7)) { $short_fields = 1; }
	        if (($stat_report >= 12) && ($stat_report <= 23))                         { $short_fields = 1; }
	}
	
	# Determine whether to translate interface indexes
	
	if (($resolve_columns != 0) && (($stat_report == 17) || ($stat_report == 18) || ($stat_report == 23))) {
	        $short_fields = 1;
	        $interface_names = 0;
	        $test_if = 1;
	        $if_name = dig_if($test_if);
	        if ($if_name ne "NO_TRANSLATIONS") { $interface_names = 1; $short_fields = 0; }
	}
}

# Output report lines

for ($m=$start_report_line;$m<=$report_lines;$m++) {

	chop; 

	if (((!$IPFIX) && ($print_report > 0)) || (($IPFIX) && ($print_report > 0) && ($print_report < 12)) || ($stat_report == 99)) {
		if (($m == $start_report_line) and ($print_report == 5)) { $saved_FV_lines[$m] .= "    "; }
		print "$saved_FV_lines[$m]\n";
		next;
	}

        if ($saved_FV_lines[$m] eq "") { next; }

	if ($stat_report == 30) {

		if ($IPFIX) {
			($s_silk,$e_silk,$dur,$sif,$source,$srcp,$dif,$dest,$dstp,$proto,$flags,$packets,$octets) = split(/ /,$saved_FV_lines[$m]);
			($s_dy,$s_tm)   = split(/T/,$s_silk);
			($yr,$mon,$day) = split(/\//,$s_dy);
			$smd            = $mon . $day;
			$start          = $smd .".". $s_tm;
			($e_dy,$e_tm)   = split(/T/,$e_silk);
			($yr,$mon,$day) = split(/\//,$e_dy);
			$emd            = $mon . $day;
			$end            = $emd .".". $e_tm;
		} else {
			($start,$end,$sif,$source,$srcp,$dif,$dest,$dstp,$proto,$flags,$packets,$octets) = split(/\s+/,$saved_FV_lines[$m]);
		}

		if ($date_format =~ /DMY/) {
		        $start_mnth = substr($start,0,2);
		        $start_date = substr($start,2,2);
		        $temp_mnth = $start_mnth;
		        substr($start,0,2) = $start_date;
		        substr($start,2,2) = $temp_mnth;
		        $end_mnth = substr($end,0,2);
		        $end_date = substr($end,2,2);
		        $temp_mnth = $end_mnth;
		        substr($end,0,2) = $end_date;
		        substr($end,2,2) = $temp_mnth;
		}

		print "  <tr>\n";
		print "<td align=left>$start</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$end</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$sif</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$source</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$srcp</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$dif</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$dest</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$dstp</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$proto</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$flags</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$packets</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$octets</td>\n";
	        print "</tr>\n";

	} else {

		if ($flow_analysis) {
			if ($head2 eq "Flows") {
				if ($country_report) {
					($x,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow,$country) = split(/ \^ /,$saved_FV_lines[$m]);
				} else {
					($x,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow) = split(/ \^ /,$saved_FV_lines[$m]);
				}
			} elsif (($head3 eq "Flows") && ($rate_report)) {

				($x,$y,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow,$flow_rate) = split(/ \^ /,$saved_FV_lines[$m]);

			} elsif (($head3 eq "Flows") && (!$rate_report)) {
				if ($country_report) {
					($x,$y,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow,$country) = split(/ \^ /,$saved_FV_lines[$m]);
				} else {
					($x,$y,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow) = split(/ \^ /,$saved_FV_lines[$m]);
				}
			}
		} else {
		        if ($head2 eq "Flows") {
		                ($x,$flows,$octets,$packets) = split(/ \^ /,$saved_FV_lines[$m]);
		        } elsif (($head3 eq "Flows") && ($rate_report)) {
		                ($x,$y,$flows,$octets,$packets,$flow_rate) = split(/ \^ /,$saved_FV_lines[$m]);
		        } elsif (($head3 eq "Flows") && (!$rate_report)) {
		                ($x,$y,$flows,$octets,$packets) = split(/ \^ /,$saved_FV_lines[$m]);
		        }
		}
	
	        # Print to screen
	
	        print "<tr>\n";
	        print "<td align=left>$x</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        if ($head3 eq "Flows") {
	                print "<td align=left>$y</td>\n";
	                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        }
	        print "<td align=righright>$flows</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$octets</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$packets</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        if ($rate_report) { print "<td align=right>$flow_rate</td>\n"; }
		if ($flow_analysis) {
			if ($rate_report) { print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n"; }
			print "<td align=right>$oct_per_flow</td>\n";
			print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
			print "<td align=right>$pkt_per_flow</td>\n";
			if ($country_report) { 
				print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td align=right>$country</td>\n";
			}
		}
	        print "</tr>\n";
	}
}

print "<tr><td>&nbsp</td></tr>\n";
print "<tr><td>&nbsp</td></tr>\n";
print " </table>\n";
print " </div>\n";

# ... end the page

if ($is_scan_replay) {
	&create_UI_service("FlowViewer_Main","service_bottom",$active_dashboard,$filter_hash);
} else {
	&create_UI_service("FlowViewer","service_bottom",$active_dashboard,$filter_hash);
}
&finish_the_page("FlowViewer");

sub dig_if {

        my ($if_number) = @_;
        $if_name = $if_number;

        if ($device_name ne "") {
                $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Devices";
        } elsif ($exporter ne "") {
                $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Exporters";
        }

        open (NAMED,"<$interfaces_file");
        chomp (@interfaces = <NAMED>);
        close (NAMED);

        foreach $interface (@interfaces) {
                if (($interface eq "") || (substr($interface,0,1) eq "#")) { next; }
                ($device,$interface_index,$interface_name) = split(/:/,$interface);
                if (($device eq $device_name) || ($device eq $exporter)) {
                        if ($interface_index eq $if_number) { $if_name = $interface_name; }
                        $found_device = 1;
                }
        }
        if ($found_device == 0) { $if_name = "NO_TRANSLATIONS"; }
        return $if_name;
}

sub type_of_line {

	$regular_line      = 0;
	$continuation_line = 1;

	if ($saved_FV_line =~ "Report:")              { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Start Time:")          { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Device:")              { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Source:")              { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Source Port:")         { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Source I/F:")          { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FV_line =~ "Src I/F Name:")        { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Source AS:")           { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "TOS Field:")           { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Include if:")          { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Lines Cutoff:")        { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Sampling Multiplier:") { $regular_line = 1; $continuation_line = 0; }
	if ($saved_FV_line =~ "Description:")         { $regular_line = 1; $continuation_line = 0; }
}

sub get_report_number {

	$noformat  = 0;
	$merge_one = 0;
	$merge_two = 0;

	if ($report_name =~ "Summary")                  { $FILTER{stat_report} = 99; }
	if ($report_name =~ "UDP/TCP Source Port")      { $FILTER{stat_report} = 6; }
	if ($report_name =~ "UDP/TCP Destination Port") { $FILTER{stat_report} = 5; }
	if ($report_name =~ "UDP/TCP Port")             { $FILTER{stat_report} = 6; }
	if ($report_name =~ "Destination IP")           { $FILTER{stat_report} = 8; }
	if ($report_name =~ "Source IP")                { $FILTER{stat_report} = 9; }
	if ($report_name =~ "Source/Destination IP")    { $FILTER{stat_report} = 10; }
	if ($report_name =~ "Source or Destination IP") { $FILTER{stat_report} = 11; }
	if ($report_name =~ "IP Protocol")              { $FILTER{stat_report} = 12; }
	if ($report_name =~ "Input Interface")          { $FILTER{stat_report} = 17; $noformat = 1; }
	if ($report_name =~ "Output Interface")         { $FILTER{stat_report} = 18; $noformat = 1; }
	if ($report_name =~ "Input/Output Interface")   { $FILTER{stat_report} = 23; $noformat = 1; }
	if ($report_name =~ "Source AS")                { $FILTER{stat_report} = 19; $merge_one = 1; }
	if ($report_name =~ "Destination AS")           { $FILTER{stat_report} = 20; $merge_one = 1; }
	if ($report_name =~ "Source/Destination AS")    { $FILTER{stat_report} = 21; $merge_two = 1; }
	if ($report_name =~ "IP ToS")                   { $FILTER{stat_report} = 22; }
	if ($report_name =~ "Source Prefix")            { $FILTER{stat_report} = 24; $merge_one = 1; }
	if ($report_name =~ "Destination Prefix")       { $FILTER{stat_report} = 25; $merge_one = 1; }
	if ($report_name =~ "Source/Destination Prefix"){ $FILTER{stat_report} = 26; $merge_two = 1; }
	if ($report_name =~ "Exporter IP")              { $FILTER{stat_report} = 27; }

	if ($report_name =~ "Flow Times")               { $FILTER{print_report} = 1; $noformat = 1; }
	if ($report_name =~ "AS Numbers")               { $FILTER{print_report} = 4; $noformat = 1; }
	if ($report_name =~ "132 Columns")              { $FILTER{print_report} = 5; $noformat = 1; }
	if ($report_name =~ "1 Line with Tags")         { $FILTER{print_report} = 9; $noformat = 1; }
	if ($report_name =~ "AS Aggregation")           { $FILTER{print_report} = 10; $noformat = 1; }
	if ($report_name =~ "Port Aggregation")         { $FILTER{print_report} = 11; $noformat = 1; }
	if ($report_name =~ "Source Prefix Aggr")       { $FILTER{print_report} = 12; $noformat = 1; }
	if ($report_name =~ "Destination Prefix Aggr")  { $FILTER{print_report} = 13; $noformat = 1; }
	if ($report_name =~ "Prefix Aggregation")       { $FILTER{print_report} = 14; $noformat = 1; }
	if ($report_name =~ "Full Catalyst")            { $FILTER{print_report} = 24; $noformat = 1; }
}
