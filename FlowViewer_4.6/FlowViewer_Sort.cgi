#! /usr/bin/perl
#
#  Purpose:
#  FlowViewer_Sort.cgi sorts FlowViewer detail line output and
#  redisplays the page.
#
#  Description:
#  The script is invoked by the user clicking on a column heading of the
#  FlowViewer output page. A temporary file that contains a copy of the
#  report is read in and sorted. A new page is output
#
#  Input arguments (received from the form):
#  Name                 Description
#  -----------------------------------------------------------------------
#  sort_column          Identifies which column to sort on
#  filter_hash          Identifies which temporary files to use
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  12/07/2007      3.3     Original released version
#  J. Loiacono  12/28/2007      3.3.1   Fixed sorting of host names
#  J. Loiacono  03/17/2011      3.4     Dynamic Resolved column widths
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  04/15/2013      4.1     Removed extraneuos formatting
#  J. Loiacono  01/26/2014      4.3     Introduced Detect Scanning
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
if ($debug_viewer eq "Y") { print DEBUG "In FlowViewer_Sort.cgi\n"; }

# Retrieve the form inputs
 
($active_dashboard,$filter_hash,$sort_column,$ascend) = split(/\^/,$ENV{'QUERY_STRING'});

($filter_source,$part2,$part3,$saved_suffix) = split(/_/,$filter_hash);
$png_filename   = "FlowViewer_save_" . $saved_suffix . ".png";
if ($debug_viewer eq "Y") { print DEBUG "filter_source: $filter_source  sort_column: $sort_column  ascend: $ascend\n"; }

if ($filter_source eq "SV") {

        $save_file   = "$save_directory/FlowViewer_save_$saved_suffix";

        # Create a new FlowViewer save file and copy the old PNG to new one

        $new_piechart_link = "$graphs_directory/$png_filename";
        $old_piechart_link = "$save_directory/$png_filename";
        $copy_command = "cp $old_piechart_link $new_piechart_link";
        system($copy_command);

} else {

        $save_file  = "$work_directory/FlowViewer_save_$saved_suffix";

}

$piechart_link = "$graphs_short/$png_filename";
$piechart_full = "$graphs_directory/$png_filename";

$saved_sort = $save_file;

# Load the temporary file of detail lines

open(SORT,"<$save_file");
chomp (@sort_lines = <SORT>);
close SORT;

open(SORTED_SAVE,">$saved_sort");
foreach $sort_line (@sort_lines) {

	if ($sort_line eq "") { next; }

        if ($sort_line =~ /BEGIN FILTERING/) { 
		$found_parameters = 1; 
                print SORTED_SAVE "$sort_line\n";
		next; }
        if ($found_parameters) {
		print SORTED_SAVE "$sort_line\n";
                if ($sort_line =~ /END FILTERING/) { 
			$found_parameters = 0; 
			$head_line = 1;
			next;
		}
		($field,$field_value) = split(/: /,$sort_line);
                if ($field eq "device_name")         { $device_name = $field_value; }
                if ($field eq "sampling_multiplier") { $sampling_multiplier = $field_value; }
                if ($field eq "resolve_addresses")   { $resolve_addresses = $field_value; }
                if ($field eq "stat_report")         { 
			$stat_report = $field_value;
			if (($stat_report == 10) || ($stat_report == 21) || ($stat_report == 23) || ($stat_report == 26)) { $rate_report = 1; }
		}
                if ($field eq "print_report")        { $print_report = $field_value; }
                if ($field eq "unit_conversion")     { $unit_conversion = $field_value; }
		if ($field eq "flow_analysis")       { $flow_analysis = $field_value; }
                if ($field eq "IPFIX")               { $IPFIX = $field_value; }
		if ($field eq "Description")         { $report_name = $field_value; }
		next; }
        if ($head_line) {
		print SORTED_SAVE "$sort_line\n";
		if ($stat_report != 30) { ($head1,$head2,$head3,$head4,$head5,$head6,$head7,$head8,$head9) = split(/ : /,$sort_line); }
		if ($head2 eq "Flows") {
			if ($sort_column eq "Source")  { $sort_field = 1; }
			if ($sort_column eq "Flows")   { $sort_field = 2; }
			if ($sort_column eq "Octets")  { $sort_field = 3; }
			if ($sort_column eq "Packets") { $sort_field = 4; }
			if ($sort_column eq "OctFlow") { $sort_field = 5; }
			if ($sort_column eq "PktFlow") { $sort_field = 6; }
		} elsif ($head3 eq "Flows") {
			if ($sort_column eq "Source")  { $sort_field = 1; }
			if ($sort_column eq "Dest")    { $sort_field = 2; }
			if ($sort_column eq "Flows")   { $sort_field = 3; }
			if ($sort_column eq "Octets")  { $sort_field = 4; }
			if ($sort_column eq "Packets") { $sort_field = 5; }
			if ($sort_column eq "Mbps")    { $sort_field = 6; }
			if ($sort_column eq "OctFlow") { $sort_field = 7; }
			if ($sort_column eq "PktFlow") { $sort_field = 8; }
		} elsif ($stat_report == 30) {
			if ($sort_column eq "Start")   { $sort_field = 1; }
			if ($sort_column eq "End")     { $sort_field = 2; }
			if ($sort_column eq "Sif")     { $sort_field = 3; }
			if ($sort_column eq "Source")  { $sort_field = 4; }
			if ($sort_column eq "SrcP")    { $sort_field = 5; }
			if ($sort_column eq "Dif")     { $sort_field = 6; }
			if ($sort_column eq "Dest")    { $sort_field = 7; }
			if ($sort_column eq "DstP")    { $sort_field = 8; }
			if ($sort_column eq "Proto")   { $sort_field = 9; }
			if ($sort_column eq "Flags")   { $sort_field = 10; }
			if ($sort_column eq "Packets") { $sort_field = 11; }
			if ($sort_column eq "Octets")  { $sort_field = 12; }
			if (($IPFIX) && ($sort_field > 2)) { $sort_field++; } 
		}

		$is_host = 0;
        	if (($head1 =~/Host/) || ($head1 =~ /Prefix/) || ($head1 =~ /Exp/) || ($head1 =~ /Aggr/)) { $is_host = 1; }  
        	if (($head2 =~/Host/) || ($head2 =~ /Prefix/) || ($head2 =~ /Exp/) || ($head2 =~ /Aggr/)) { $is_host = 1; }  
		if ($stat_report == 30) { $is_host = 1; }

		$head_line = 0;
		next;
	}

	# Parse through the individual report lines

	if ($stat_report == 30) {
        	$sort_value = (split(/\s+/,$sort_line)) [$sort_field-1];
	} else {
        	$sort_value = (split(/ \^ /,$sort_line)) [$sort_field-1];
	}

        if (($sort_column eq "Octets") && ($unit_conversion eq "Y")) {
                $temp_value = (split(/ \^ /,$sort_line)) [$sort_field-1];
                ($temp_value,$sort_units) = split(/\s+/,$temp_value);
                if ($sort_units eq "KB") { $sort_value = int($temp_value * (2**10)); }
                if ($sort_units eq "MB") { $sort_value = int($temp_value * (2**20)); }
                if ($sort_units eq "GB") { $sort_value = int($temp_value * (2**30)); }
                if ($sort_units eq "TB") { $sort_value = int($temp_value * (2**40)); }
                if ($sort_units eq "PB") { $sort_value = int($temp_value * (2**50)); }
        }

	if ((($sort_column eq "Source") && ($is_host)) || (($sort_column eq "Dest") && ($is_host))) {

                if ((!($sort_value =~ /[a-zA-Z]/)) || ($sort_value =~ /:/)) {

                        $IPv4 = 0; $IPv6 = 0;
                        $_ = $sort_value;
                        $num_dots   = tr/\.//; if ($num_dots   > 0) { $IPv4 = 1; }
                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6 = 1; }

                        if ($IPv4) {
                                $slash = index($sort_value,"/");
                                if ($slash >= 1) { $network = substr($sort_value,0,$slash); }
				else { $network = $sort_value; }
                                ($a,$b,$c,$d) = split(/\./,$network);
                                if (length($a) == 1) { $a = "00" . $a; } if (length($a) == 2) { $a = "0" . $a; }
                                if (length($b) == 1) { $b = "00" . $b; } if (length($b) == 2) { $b = "0" . $b; }
                                if (length($c) == 1) { $c = "00" . $c; } if (length($c) == 2) { $c = "0" . $c; }
                                if (length($d) == 1) { $d = "00" . $d; } if (length($d) == 2) { $d = "0" . $d; }
                                $sort_value = $a . $b . $c . $d;
                        }

                        if ($IPv6) {

                                $double_colon     = 0;
                                $colon_count      = 0;
                                $sortable_address = "";
                                $abbreviated_segments = 7 - $num_colons;
                                $slash = index($sort_value,"/");
                                $sort_address = substr($sort_value,0,$slash);

                                for ($i=0;$i<8;$i++) {
                                        $colon_count++;
                                        if (($double_colon) && ($abbreviated_segments > 0)) {
                                                $ipv6_segment[$i] = "0000";
                                                $sortable_address .= $ipv6_segment[$i];
                                                $abbreviated_segments--;
                                                next;
                                        }

                                        $next_colon = index($sort_address,":");
                                        if ($i < 7) {
                                                $ipv6_segment[$i] = substr($sort_address,0,$next_colon);
                                        } else {
                                                $ipv6_segment[$i] = $sort_address;
                                        }
                                        if ($ipv6_segment[$i] eq "") {
                                                $double_colon = 1;
                                                $ipv6_segment[$i] = "0000";
                                        }

                                        if (length($ipv6_segment[$i]) == 1) { $ipv6_segment[$i] = "000" . $ipv6_segment[$i]; }
                                        if (length($ipv6_segment[$i]) == 2) { $ipv6_segment[$i] = "00"  . $ipv6_segment[$i]; }
                                        if (length($ipv6_segment[$i]) == 3) { $ipv6_segment[$i] = "0"   . $ipv6_segment[$i]; }

                                        $sort_address = substr($sort_address,$next_colon+1,60);
                                        $sortable_address .= $ipv6_segment[$i];
                                }
                                $sort_value = $sortable_address;
                        }
                }

                $sort_key = $sort_value;

        } else {
                $len_sort = length($sort_value);
                $sort_key = $sort_value;
                for ($i=$len_sort;$i<22;$i++) {
                        $sort_key = "0" . $sort_key;
                }
        }

        $presort_line = $sort_key ." ^^ ". $sort_line;
        push(@presort_lines,$presort_line);

        $report_lines++;
}
close(SORTED_SAVE);

@sorted_lines = sort (@presort_lines);

if (($stat_report == 8) || ($stat_report == 9) || ($stat_report == 11)) { $country_report = 1; }

$resolve_columns = 0;
if (($resolve_addresses eq "Y") && ($stat_report == 8))  { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 9))  { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 10)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 11)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 17)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 18)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 19)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 20)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 21)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 23)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 27)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 30)) { $resolve_columns = 1; }

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

if ($ascend == 0) {
        $ascend = 1;
} else {
        @sorted_temp = reverse(@sorted_lines);
        @sorted_lines = @sorted_temp;
        $ascend = 0;
}

# Create the web page with sorted content

&create_UI_top($active_dashboard);
&create_UI_service("FlowViewer_Main","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";
if ($filter_source eq "SV") {
        print " <span class=text16>$report_name</span>\n";
} else {
        print " <span class=text16>FlowViewer Report from $device_name</span>\n";
}

&create_filter_output("FlowViewer_Main",$filter_hash);

# Output the Pie Chart if generated

if (-e $piechart_full) { print " <center><img src=$piechart_link></center>\n"; }

# Output the column headers

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

if ($stat_report == 30) {

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
        print "<td align=left>$octets_link</td>\n";
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
}

# Output report lines

$report_lines--;
open(SORTED_SAVE,">>$saved_sort");
for ($m=0;$m<=$report_lines;$m++) {

	($sort_key,$original_line) = split(/ \^\^ /,$sorted_lines[$m]);

        if ($stat_report == 30) {

		if ($IPFIX) {
		        ($s_silk,$e_silk,$dur,$sif,$source,$srcp,$dif,$dest,$dstp,$proto,$flags,$packets,$octets) = split(/\s+/,$original_line);
			($s_dy,$s_tm)   = split(/T/,$s_silk);
			($yr,$mon,$day) = split(/\//,$s_dy);
			$smd            = $mon . $day;
			$start          = $smd .".". $s_tm;
			($e_dy,$e_tm)   = split(/T/,$e_silk);
			($yr,$mon,$day) = split(/\//,$e_dy);
			$emd            = $mon . $day;
			$end            = $emd .".". $e_tm;
		} else {
		        ($start,$end,$sif,$source,$srcp,$dif,$dest,$dstp,$proto,$flags,$packets,$octets) = split(/\s+/,$original_line);
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
                print "  </tr>\n";

        } else {

		if ($flow_analysis) {
			if ($head2 eq "Flows") {
				if ($country_report) {
					($x,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow,$country) = split(/ \^ /,$original_line);
				} else {
					($x,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow) = split(/ \^ /,$original_line);
				}
			} elsif (($head3 eq "Flows") && ($rate_report)) {

				($x,$y,$flows,$octets,$packets,$flow_rate,$oct_per_flow,$pkt_per_flow) = split(/ \^ /,$original_line);

			} elsif (($head3 eq "Flows") && (!$rate_report)) {
				if ($country_report) {
					($x,$y,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow,$country) = split(/ \^ /,$original_line);
				} else {
					($x,$y,$flows,$octets,$packets,$oct_per_flow,$pkt_per_flow) = split(/ \^ /,$original_line);
				}
			}
		} else {
			if ($head2 eq "Flows") {
				($x,$flows,$octets,$packets) = split(/ \^ /,$original_line);
			} elsif (($head3 eq "Flows") && ($rate_report)) {
				($x,$y,$flows,$octets,$packets,$flow_rate) = split(/ \^ /,$original_line);
			} elsif (($head3 eq "Flows") && (!$rate_report)) {
				($x,$y,$flows,$octets,$packets) = split(/ \^ /,$original_line);
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
		print "<td align=right>$flows</td>\n";
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

	print SORTED_SAVE "$original_line\n";
}
close(SORTED_SAVE);

print " <tr><td>&nbsp</td></tr>";
print " <tr><td>&nbsp</td></tr>";
print " </table>\n";
print " </div>\n";

&create_UI_service("FlowViewer_Main","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowViewer_Main");

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
