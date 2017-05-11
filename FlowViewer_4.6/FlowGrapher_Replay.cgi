#! /usr/bin/perl
#
#  Purpose:
#  FlowGrapher_Replay.cgi re-displays a saved FlowGrapher report.
#
#  Description:
#
#  FlowGrapher_Replay.cgi builds the FlowGrapher webpage framework
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
#  J. Loiacono  08/07/2013      4.2     Accomodations for Linear processing
#  J. Loiacono  09/11/2013      4.2.1   Mods for Linear for FlowMonitor
#                                       Set dates to index ascending
#  J. Loiacono  12/25/2013      4.3     Fixed replay of negative detail lines
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards and Analysis
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
$query_string  =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge ;
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

if ($filter_source eq "FL") {
	# Do a Replay of a currenly active FlowGrapher Report for Filter savers
	$filter_hash   = "FG_" . $hash_file;
	$saved_FG_file = "$work_directory/$hash_file";
	$saved_FG_png  = "$graphs_short/$hash_file.png";

} else {
	$filter_hash   = "SV_" . $hash_file;
	$saved_FG_file = "$save_directory/$hash_file";
	$saved_FG_png  = "$save_short/$hash_file.png";
}

if ($debug_grapher eq "Y") { print DEBUG "In FlowGrapher_Replay.cgi   filter_source: $filter_source  filter_hash: $filter_hash  hash_file: $hash_file\n"; }
if ($debug_grapher eq "Y") { print DEBUG "active_dashboard: $active_dashboard   saved_FG_file: $saved_FG_file\n"; }

if ($filter_source eq "PV") {

        ($directory,$saved_label) = $saved_FG_file =~ m/(.*\/)(.*)$/;
        $last_underscore = rindex($saved_label,"_"); $len_label = $last_underscore - 16;
        $pv_report_name = substr($saved_label,16,$len_label);
        $pv_suffix = &get_suffix;
        $filter_hash = "PV_FlowGrapher_replay_$pv_suffix";
        $pv_filter_file = "$work_directory/FlowGrapher_replay_$pv_suffix";

        &create_UI_top($active_dashboard);
        &create_UI_service("FlowGrapher","service_top",$active_dashboard,$filter_hash);
        print " <div id=content_wide>\n";

        open(SAVED,"<$saved_FG_file");
        chomp (@saved_FG_lines = <SAVED>);
        close SAVED;

        $header_line = 1;
	$first_blank = 1;

        foreach $saved_FG_line (@saved_FG_lines) {

		if (($saved_FG_line eq "") || ($saved_FG_line =~ "graph.png")) { 
			$print_header = 1;
			$header_line = 0;
		}

                &type_of_line;

		if ($header_line) {
	                if ($saved_FG_line =~ "Report:") {
				$start_report = index($saved_FG_line,"Report:");
				$start_report--;
				$saved_FG_line = substr($saved_FG_line,$start_report,300);
	                	$first_half  = substr($saved_FG_line,0,57);
	                	$second_half = substr($saved_FG_line,57,400);
			} else {
	                	$first_half  = substr($saved_FG_line,0,57);
	                	$second_half = substr($saved_FG_line,57,400);
			}
		}

                if (($header_line) && ($regular_line)) {

                        $last_field = "";

                        if ($saved_FG_line =~ "Report:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
				if ($field_value =~ /Bits/)    { $FILTER{graph_type} = "bps"; }
				if ($field_value =~ /Packets/) { $FILTER{graph_type} = "pps"; }
				if ($field_value =~ /Flows/)   { $FILTER{graph_type} = "fpsi"; }

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{bucket_size} = $field_value;

                        } elsif ($saved_FG_line =~ "Start Time:") {

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

                        } elsif ($saved_FG_line =~ "Device:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{device_name} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{exporter} = $field_value;

                        } elsif ($saved_FG_line =~ "Source:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_addresses} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_addresses} = $field_value;

                                $last_field = "source_addresses";

                        } elsif ($saved_FG_line =~ "Source Port:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_ports} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_ports} = $field_value;

                                $last_field = "source_ports";

                        } elsif ($saved_FG_line =~ "Src I/F Name:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{sif_names} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dif_names} = $field_value;

                                $last_field = "sif_names";

                        } elsif ($saved_FG_line =~ "Source I/F:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_ifs} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_ifs} = $field_value;

                                $last_field = "source_ifs";

                        } elsif ($saved_FG_line =~ "Source AS:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{source_ases} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{dest_ases} = $field_value;

                                $last_field = "source_ases";

                        } elsif ($saved_FG_line =~ "TOS Field:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{tos_fields} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{tcp_flags} = $field_value;

                                $last_field = "tos_fields";

                        } elsif ($saved_FG_line =~ "Include if:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $include_key = substr($field_value,1,3);
                                if ($include_key eq "Any") { $FILTER{flow_select} = 1; }
                                if ($include_key eq "End") { $FILTER{flow_select} = 2; }
                                if ($include_key eq "Sta") { $FILTER{flow_select} = 3; }
                                if ($include_key eq "Ent") { $FILTER{flow_select} = 4; }

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{protocols} = $field_value;

                                $last_field = "flow_select";

                        } elsif ($saved_FG_line =~ "Detail Lines:") {

                                ($field_name,$field_value) = split(/:/,$first_half);
                                $FILTER{detail_lines} = $field_value;

                                ($field_name,$field_value) = split(/:/,$second_half);
                                $FILTER{graph_multiplier} = $field_value;

                        } elsif ($saved_FG_line =~ "Sampling Multiplier:") {

                                ($field_name,$field_value) = split(/plier: /,$saved_FG_line);
                                $FILTER{sampling_multiplier} = $field_value;

                        } elsif ($saved_FG_line =~ "Description:") {

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

		if ($header_line) { next; }

		if (($print_header) && ($first_blank))  { 

		        # Save a temporary filter for the user to invoke a new report from existing report
		
		        foreach $field_name (keys (%FILTER)) { 
				if ($field_name eq "description") { next; }
				$FILTER{$field_name} =~ s/\s+//g; 
				$FILTER{$field_name} =~ s/,/, /g;
			}
		
		        $device_name = $FILTER{device_name};
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
		        $detail_lines = $FILTER{detail_lines};
		        $description = $FILTER{description};
		        $graph_multiplier = $FILTER{graph_multiplier};
		        $graph_type = $FILTER{graph_type};
		        $bucket_size = $FILTER{bucket_size};
		        $sampling_multiplier = $FILTER{sampling_multiplier};
		
		        start_saved_file($pv_filter_file);

	                print "  <br>\n";
	                print "  <span class=text16>$pv_report_name</span>\n";
	                print "  <br>\n";

			&create_filter_output("FlowGrapher",$filter_hash);

			$print_header = 0;
			$first_blank = 0;
		}

                if ($saved_FG_line =~ "graph.png") {

                	print "$saved_FG_line\n";
	                print " <br>\n";
        		print " <table>\n";
			print " <tr>\n";
			print " <td>Start</td>";
			print " <td>&nbsp&nbsp&nbsp&nbsp&nbspEnd</td>";
			print " <td>&nbsp&nbsp&nbsp&nbsp&nbspLen</td>";
			print " <td>&nbsp&nbsp&nbsp&nbsp&nbspSource Host</td>";
			print " <td>&nbsp&nbsp&nbsp&nbsp&nbspPort</td>";
			print " <td>&nbsp&nbsp&nbsp&nbsp&nbspDestination Host</td>";
			print " <td>&nbsp&nbsp&nbsp&nbsp&nbspPort</td>";
			if ($graph_type eq "bps")   { 
				if ($sampling_multiplier ne "") { 
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspTotal Bytes*</td>";
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspMbps*</td><tr>";
				} else {
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspTotal Bytes</td>";
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspMbps</td><tr>";
				}
			}
			if ($graph_type eq "pps")   { 
				if ($sampling_multiplier ne "") { 
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspTotal Packets*</td>";
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspKpps*</td><tr>";
				} else {
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspTotal Packets</td>";
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspKpps</td><tr>";
				}
			}
			if ($graph_type =~ "fps")   { 
				if ($sampling_multiplier ne "") { 
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspTotal Flows*</td>";
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspKfps*</td><tr>";
				} else {
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspTotal Flows</td>";
					print " <td>&nbsp&nbsp&nbsp&nbsp&nbspKfps</td><tr>";
				}
			}
			next;
		}

                if ($saved_FG_line =~ "Map")          { next; }
		if ($saved_FG_line =~ "shape=rect")   { next; }
                if ($saved_FG_line =~ "Total Bytes")  { next; }
                if ($saved_FG_line =~ "Total Flows")  { next; }
                if ($saved_FG_line =~ "Total Packets"){ next; }

		($x1,$x2,$x3,$x4,$x5,$x6,$x7,$x8,$x9,$x10) = split(/\s+/,$saved_FG_line);
		print "<tr><td>$x1</td><td>&nbsp&nbsp&nbsp&nbsp&nbsp$x2</td><td align=right>&nbsp&nbsp&nbsp&nbsp&nbsp$x3</td>";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$x4</td><td>&nbsp&nbsp&nbsp&nbsp&nbsp$x5</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp$x6</td><td>&nbsp&nbsp&nbsp&nbsp&nbsp$x7</td><td align=right>&nbsp&nbsp&nbsp&nbsp&nbsp$x8</td>";
		print "<td align=right>&nbsp&nbsp&nbsp&nbsp&nbsp$x9</td><td>&nbsp&nbsp&nbsp&nbsp&nbsp$x10</td></tr>\n";
        }

        print " </table>\n";
        print " </font>\n";
        print " </div>\n";

        &create_UI_service("FlowGrapher","service_bottom",$active_dashboard,$filter_hash);
        &finish_the_page("FlowGrapher");
        exit;
}

# Load the saved FlowGrapher file

open(SAVED,"<$saved_FG_file");
chomp (@saved_FG_lines = <SAVED>);
close SAVED;

foreach $saved_FG_line (@saved_FG_lines) {
	$line_number++;
        if ($saved_FG_line =~ /BEGIN FILTERING/) { $found_parameters = 1; next; }
        if ($found_parameters) {
                if ($saved_FG_line =~ /END FILTERING/) { 
			$start_detail_lines = $line_number;
			$found_parameters = 0;
			next;
		}
                ($field,$field_value) = split(/: /,$saved_FG_line);
                if ($field eq "device_name")         { $device_name = $field_value; }
                if ($field eq "sampling_multiplier") { $sampling_multiplier = $field_value; }
                if ($field eq "resolve_addresses")   { $resolve_addresses = $field_value; }
                if ($field eq "graph_type")          { if    ($field_value eq "Bits")      { $graph_type = "bps";  $LINEAR = 1; } 
						       elsif ($field_value eq "Bits_P")    { $graph_type = "bps"; }
						       elsif ($field_value eq "Packets")   { $graph_type = "pps";  $LINEAR = 1; }
						       elsif ($field_value eq "Packets_P") { $graph_type = "pps"; }
						       elsif ($field_value eq "Flows")     { $graph_type = "fpsi"; $LINEAR = 1; }
						       elsif ($field_value eq "Flows_I")   { $graph_type = "fpsi"; }
						       elsif ($field_value eq "Flows_P")   { $graph_type = "fpsa"; }
						       else  {$graph_type = $field_value; 
							      $LINEAR = 1;
							      if ($graph_type eq "bpsa")  { $LINEAR = 0; }
							      if ($graph_type eq "ppsa")  { $LINEAR = 0; }
							      if ($graph_type eq "fpsa")  { $LINEAR = 0; }
							      if ($graph_type eq "fpsia") { $LINEAR = 0; }
							      if ($graph_type eq "fpsaa") { $LINEAR = 0; } } }
                if ($field eq "detail_lines")        { $detail_lines = $field_value; }
                if ($field eq "Description")         { $report_name = $field_value; }
                if ($field eq "IPFIX")               { $IPFIX = $field_value; }
                if ($field eq "filter_hash")         { if ($saved_FG_line =~ /FA_/) { $analysis_save = 1; } }
                next;
        }
	if ($saved_FG_line =~ /END ANALYSIS/) {
		$past_analysis_hosts = 1;
		last;
	}
	if (!$past_analysis_hosts) {
		next;
	}
}
if ($past_analysis_hosts) { $start_detail_lines = $line_number; }

if (($filter_source eq "FL") || ($filter_source eq "SF")) { $report_name = "FlowGrapher Report from $device_name &nbsp&nbsp&nbsp [Filter Saved]"; }

# Start the page ...

&create_UI_top($active_dashboard);
&create_UI_service("FlowGrapher","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";
print " <span class=text16>$report_name</span>\n";

# Replay the FlowGrapher Content

&create_filter_output("FlowGrapher",$filter_hash);

print " <br>\n";
print " <center><img src=$saved_FG_png></center>\n";

if ($analysis_save) {

	$line_number = 0;
	foreach $saved_FG_line (@saved_FG_lines) {
		$line_number++;
		if ($line_number <= $start_detail_lines) { next; }
		print "$saved_FG_line\n";
	}

} elsif (!$IPFIX && $LINEAR) {

	# Adjust column headers for selected output type

        $flows_txt = "Flows";
        $bytes_txt = "Bytes";
        $pckts_txt = "Packets";
        $ambps_txt = "Agg Mbps";

        if ($sampling_multiplier > 1) {
                $flows_txt .= "*";
                $bytes_txt .= "*";
                $pckts_txt .= "*";
                $ambps_txt .= "*";
        }

        # Create column headers with sort links

        $dur_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dur^$ascend>Duration</a>";
        $source_link = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Source^$ascend>Source Host</a>";
        $sport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Sport^$ascend>S Port</a>";
        $dest_link   = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dest^$ascend>Destination Host</a>";
        $dport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dport^$ascend>D Port</a>";
        $flows_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Flows^$ascend>$flows_txt</a>";
        $bytes_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Bytes^$ascend>$bytes_txt</a>";
        $pckts_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Pckts^$ascend>$pckts_txt</a>";
        $agg_rate    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^aRate^$ascend>$ambps_txt</a>";

        print "<br>\n";
        print "<table>\n";
        print "<tr>\n";
        print "<td align=left>$dur_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=left>$source_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=left>$sport_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=left>$dest_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=left>$dport_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=right>$flows_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=right>$bytes_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=right>$pckts_link</td>\n";
        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
        print "<td align=right>$agg_rate</td>\n";
        print "</tr>\n";
        print "<tr><td>&nbsp&nbsp</td></tr>\n";

	# Output detail lines
	
	$end_detail_lines = $start_detail_lines + abs($detail_lines);
	for ($m=$start_detail_lines;$m<=$end_detail_lines;$m++) {
	
	        if ($saved_FG_lines[$m] eq "") { next; }
	
                ($indx,$dur,$sip,$sp,$dip,$dp,$flows,$bytes,$pckts,$agg_rate) = split(/\s+/,$saved_FG_lines[$m]);

                # Print to screen

                print "<tr>\n";
                print "<td align=right>$dur</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=left>$sip</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=right>$sp</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=left>$dip</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=right>$dp</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=right>$flows</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=right>$bytes</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=right>$pckts</td>\n";
                print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
                print "<td align=right>$agg_rate</td>\n";
                print "</tr>\n";
        }

} else {

	# Adjust column headers for selected output type
	
	if ($graph_type =~ "pps") {
	        $totals_txt = "Total Packets";
	        $ps_txt = "Kpps";
	} else {
	        $totals_txt = "Total Bytes";
	        $ps_txt = "Mbps";
	}
	
	if ($sampling_multiplier > 1) {
	        $totals_txt .= "*";
	        $ps_txt     .= "*";
	}
	
	if ($debug_grapher eq "Y") { print DEBUG "done with saved FlowGrapher file: $saved_FG_file\n"; }
	
	# Create column headers with sort links
	
	$start_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Start^1>Start</a>";
	$end_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^End^1>End</a>";
	$len_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Len^$ascend>Len</a>";
	$source_link = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Source^$ascend>Source Host</a>";
	$sport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Sport^$ascend>S Port</a>";
	$dest_link   = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dest^$ascend>Destination Host</a>";
	$dport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dport^$ascend>D Port</a>";
	$bytes_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Bytes^$ascend>$totals_txt</a>";
	$mbps_link   = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Mbps^$ascend>$ps_txt</a>";
	
	print "<br>\n";
	print "<table>\n";
	print "<tr>\n";
	print "<td align=left>$start_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$end_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$len_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$source_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$sport_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$dest_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=left>$dport_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=right>$bytes_link</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td align=right>$mbps_link</td>\n";
	print "</tr>\n";
	print "<tr><td>&nbsp&nbsp</td></tr>\n";
	
	# Output detail lines
	
	$end_detail_lines = $start_detail_lines + abs($detail_lines);
	for ($m=$start_detail_lines;$m<=$end_detail_lines;$m++) {
	
	        if ($saved_FG_lines[$m] eq "") { next; }
	
	        ($s_epoch,$s_tm,$e_tm,$len,$sip,$sp,$dip,$dp,$tb,$mbps) = split(/\s+/,$saved_FG_lines[$m]);
	
	        # Print to screen
	
	        print "<tr>\n";
	        print "<td align=left>$s_tm</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=left>$e_tm</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$len</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=left>$sip</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$sp</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=left>$dip</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$dp</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$tb</td>\n";
	        print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	        print "<td align=right>$mbps</td>\n";
	        print "</tr>\n";
	}
}

print "<tr><td>&nbsp</td></tr>\n";
print "<tr><td>&nbsp</td></tr>\n";
print " </table>\n";
print " </div>\n";

# ... end the page

&create_UI_service("FlowGrapher","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowGrapher");

sub type_of_line {

        $regular_line      = 0;
        $continuation_line = 1;

        if ($saved_FG_line =~ "Report:")             { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Start Time:")         { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Device:")             { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Source:")             { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Source Port:")        { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Source I/F:")         { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Src I/F Name:")       { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Source AS:")          { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "TOS Field:")          { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Include if:")         { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Detail Lines:")       { $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Sampling Multiplier:"){ $regular_line = 1; $continuation_line = 0; }
        if ($saved_FG_line =~ "Description:")        { $regular_line = 1; $continuation_line = 0; }
}
