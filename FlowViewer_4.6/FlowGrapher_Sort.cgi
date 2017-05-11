#! /usr/bin/perl
#
#  Purpose:
#  FlowGrapher_Sort.cgi sorts FlowGrapher detail line output and
#  redisplays the page.
#
#  Description:
#  The script is invoked by the user clicking on a column heading of the
#  Detail Lines section of the FlowGgrapher output page. A temporary file
#  that contains a copy of the detail lines is read in and sorted. A new page
#  is output.
#
#  Input arguments (received from the form):
#  Name                 Description
#  -----------------------------------------------------------------------
#  filter_hash          Identifies which temporary files to use
#  sort_column          Identifies which column to sort on
#  ascend               Identifies how to sort (ascend v. descend)
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
#  J. Loiacono  08/07/2013      4.2     Accomodations for Linear processing
#  J. Loiacono  09/11/2013      4.2.1   Mods for Linear for FlowMonitor
#                                       Mods for international date formatting
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards and Analysis
#  J. Loiacono  01/26/2015      4.6     Timezone from system (not Configuration)
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

if ($debug_grapher eq "Y") { open (DEBUG,">>$work_directory/DEBUG_GRAPHER"); }

# Retrieve the form inputs
 
($active_dashboard,$filter_hash,$sort_column,$ascend) = split(/\^/,$ENV{'QUERY_STRING'});

($filter_source,$part2,$part3,$saved_suffix) = split(/_/,$filter_hash);
$png_filename   = "FlowGrapher_save_" . $saved_suffix . ".png";
$flowgraph_link = "$graphs_short/$png_filename";

if ($filter_source eq "SV") {

        $save_file   = "$save_directory/FlowGrapher_save_$saved_suffix";

	# Create a new FlowGrapher save file and copy the old PNG to new one

	$new_flowgraph_link = "$graphs_directory/$png_filename";
	$old_flowgraph_link = "$save_directory/$png_filename";
	$copy_command = "cp $old_flowgraph_link $new_flowgraph_link";
	system($copy_command);

	$SAVED = 1;

} else {

	$save_file  = "$work_directory/FlowGrapher_save_$saved_suffix";

}

$saved_hash   = "FlowGrapher_save_$saved_suffix"; 
$new_filter_hash  = "FA_$saved_hash";

$saved_sort = $save_file;

if ($debug_grapher eq "Y") { print DEBUG "In FlowGrapher_Sort.cgi   filter_hash: $filter_hash  sort_column: $sort_column  ascend: $ascend\n"; }

# Load the temporary file of detail lines

open(SORT,"<$save_file");
chomp (@sort_lines = <SORT>);
close SORT;

open(SORTED_SAVE,">$saved_sort");

foreach $sort_line (@sort_lines) {

        if ($sort_line =~ /BEGIN FILTERING/) { 
		$found_parameters = 1; 
		print SORTED_SAVE "$sort_line\n";
		next; }
        if ($found_parameters) {
		print SORTED_SAVE "$sort_line\n";
                if ($sort_line =~ /END FILTERING/) { $found_parameters = 0; }
		($field,$field_value) = split(/: /,$sort_line);
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
                if ($field eq "IPFIX")               { $IPFIX = $field_value;
			if (!$IPFIX && $LINEAR) {
				if ($sort_column eq "Dur")     { $sort_column = 1; }
				if ($sort_column eq "Source")  { $sort_column = 2; }
				if ($sort_column eq "Sport")   { $sort_column = 3; }
				if ($sort_column eq "Dest")    { $sort_column = 4; }
				if ($sort_column eq "Dport")   { $sort_column = 5; }
				if ($sort_column eq "Flows")   { $sort_column = 6; }
				if ($sort_column eq "Bytes")   { $sort_column = 7; }
				if ($sort_column eq "Pckts")   { $sort_column = 8; }
				if ($sort_column eq "aRate")   { $sort_column = 9; }
			} else {
				if ($sort_column eq "Start")   { $sort_column = 1; }
				if ($sort_column eq "End")     { $sort_column = 2; }
				if ($sort_column eq "Len")     { $sort_column = 3; }
				if ($sort_column eq "Source")  { $sort_column = 4; }
				if ($sort_column eq "Sport")   { $sort_column = 5; }
				if ($sort_column eq "Dest")    { $sort_column = 6; }
				if ($sort_column eq "Dport")   { $sort_column = 7; }
				if ($sort_column eq "Bytes")   { $sort_column = 8; }
				if ($sort_column eq "Mbps")    { $sort_column = 9; }
			}
		}
                if ($field eq "Description")         { $report_name = $field_value; }
		next;
        }
	if ($sort_line =~ /BEGIN ANALYSIS/) {
		$found_analysis = 1;
		print SORTED_SAVE "$sort_line\n";
		next;
	}
	if ($found_analysis) {
		$ANALYSIS = 1;
		print SORTED_SAVE "$sort_line\n";
		if ($sort_line =~ /END ANALYSIS/) { $found_analysis = 0; }
		next;
	}

	$sort_value = (split(/\s+/,$sort_line)) [$sort_column];

	if (!$IPFIX && $LINEAR) {
		$addr_col_1 = 2;
		$addr_col_2 = 4;
	} else {
		if (($date_format =~ /DMY/) && (($sort_column == 1) || ($sort_column == 2))) { $switch_date = 1; }
		$addr_col_1 = 4;
		$addr_col_2 = 6;
	}

	if (($sort_column == $addr_col_1) || ($sort_column == $addr_col_2)) {
                if ((!($sort_value =~ /[a-zA-Z]/)) || ($sort_value =~ /:/)) {

                        $IPv4 = 0; $IPv6 = 0;
                        $_ = $sort_value;
                        $num_dots   = tr/\.//; if ($num_dots   > 0) { $IPv4 = 1; }
                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6 = 1; }

                        if ($IPv4) {
                                ($a,$b,$c,$d) = split(/\./,$sort_value);
                                if (length($a) == 1) { $a = "00" . $a; } if (length($a) == 2) { $a = "0" . $a; }
                                if (length($b) == 1) { $b = "00" . $b; } if (length($b) == 2) { $b = "0" . $b; }
                                if (length($c) == 1) { $c = "00" . $c; } if (length($c) == 2) { $c = "0" . $c; }
                                if (length($d) == 1) { $d = "00" . $d; } if (length($d) == 2) { $d = "0" . $d; }
                                $sort_value = $a . $b . $c . $d;
                        }

                        if ($IPv6) {
                                ($a,$b,$c,$d,$e,$f,$g,$h) = split(/:/,$sort_value);
                                if(length($a)==1){$a="000".$a;} if(length($a)==2){$a="00".$a;} if(length($a)==3){$a="0".$a;}
                                if(length($b)==1){$b="000".$b;} if(length($b)==2){$b="00".$b;} if(length($b)==3){$b="0".$b;}
                                if(length($c)==1){$c="000".$c;} if(length($c)==2){$c="00".$c;} if(length($c)==3){$c="0".$c;}
                                if(length($d)==1){$d="000".$d;} if(length($d)==2){$d="00".$d;} if(length($d)==3){$d="0".$d;}
                                if(length($e)==1){$e="000".$e;} if(length($e)==2){$e="00".$e;} if(length($e)==3){$e="0".$e;}
                                if(length($f)==1){$f="000".$f;} if(length($f)==2){$f="00".$f;} if(length($f)==3){$f="0".$f;}
                                if(length($g)==1){$g="000".$g;} if(length($g)==2){$g="00".$g;} if(length($g)==3){$g="0".$g;}
                                if(length($h)==1){$h="000".$h;} if(length($h)==2){$h="00".$h;} if(length($h)==3){$h="0".$h;}
                                $sort_value = $a . $b . $c . $d . $e . $f . $g . $h;
                        }
                }
		$sort_key = $sort_value;

	} elsif ($switch_date == 1) {
		$sort_date  = substr($sort_value,0,2);
		$sort_month = substr($sort_value,2,2);
		$sort_time  = substr($sort_value,4,9);
		$sort_key = $sort_month . $sort_date . $sort_time;
	} else {
	        $len_sort = length($sort_value); 
	        $sort_key = $sort_value; 
	        for ($i=$len_sort;$i<22;$i++) { 
	                $sort_key = "0" . $sort_key; 
	        }
	}

	$presort_line = $sort_key ."  ". $sort_line;
	push(@presort_lines,$presort_line);

	$detail_lines++;
}
close(SORTED_SAVE);

@sorted_lines = sort (@presort_lines);

if (!$IPFIX && $LINEAR) {
	if ($ascend == 0) {
		if (($sort_column == 1) || ($sort_column == 6) || ($sort_column == 7) || ($sort_column == 8) || ($sort_column == 9)) { 
			@sorted_temp = reverse(@sorted_lines); 
			@sorted_lines = @sorted_temp;
		}
		$ascend = 1;
	} else {
		if (($sort_column != 1) && ($sort_column != 6) && ($sort_column != 7) && ($sort_column != 8) && ($sort_column != 9)) { 
			@sorted_temp = reverse(@sorted_lines); 
			@sorted_lines = @sorted_temp;
		}
		$ascend = 0;
	}
} else {
	if ($ascend == 0) {
		if (($sort_column == 8) || ($sort_column == 9) || ($sort_column == 3)) { 
			@sorted_temp = reverse(@sorted_lines); 
			@sorted_lines = @sorted_temp;
		}
		$ascend = 1;
	} else {
		if (($sort_column != 8) && ($sort_column != 9) && ($sort_column != 3)) { 
			@sorted_temp = reverse(@sorted_lines); 
			@sorted_lines = @sorted_temp;
		}
		$ascend = 0;
	}
}

&create_UI_top($active_dashboard);
&create_UI_service("FlowGrapher_Main","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";

if ($filter_source eq "SV") { 
	print " <span class=text16>$report_name</span>\n";
} else {
	print " <span class=text16>FlowGrapher Report from $device_name</span>\n";
}
     
open(DATE,"date 2>&1|");
while (<DATE>) {
	($d_tz,$m_tz,$dt_tz,$t_tz,$time_zone,$y_tz) = split(/\s+/,$_);
}

&create_filter_output("FlowGrapher_Main",$filter_hash);

print " <br>\n";
print " <center><img src=$flowgraph_link></center>\n";

if (!$IPFIX && $LINEAR) {

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
	
	$dns_column_widths    = $dns_column_width . "s";
	$dns_column_widthss   = $dns_column_width .".". $dns_column_width ."s";
	
	open(SORTED_SAVE,">>$saved_sort");
	for ($m=0;$m<=$detail_lines;$m++) {
	
		if ($sorted_lines[$m] eq "") { next; }
	
		($sort_field,$indx,$dur,$sip,$sp,$dip,$dp,$flows,$bytes,$pckts,$agg_rate) = split(/\s+/,$sorted_lines[$m]);
	
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

                # Print to Save/Sort file

                printf SORTED_SAVE "%-12s  %10.3f  %-$dns_column_widthss  %-6s   %-$dns_column_widthss  %-6s  %8s %15s %11s  %8.3f\n",$indx,$dur,$sip,$sp,$dip,$dp,$flows,$bytes,$pckts,$agg_rate;
        }

} else {

	# Adjust column headers for selected output type
	
	if ($graph_type =~ /pps/) {
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
	
	# Create column headers with sort links
	
	$start_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Start^$ascend>Start</a>";
	$end_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^End^$ascend>End</a>";
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
	
	$dns_column_widths    = $dns_column_width . "s";
	$dns_column_widthss   = $dns_column_width .".". $dns_column_width ."s";
	
	open(SORTED_SAVE,">>$saved_sort");
	for ($m=0;$m<=$detail_lines;$m++) {
	
		if ($sorted_lines[$m] eq "") { next; }
	
		($sort_field,$s_epoch,$s_tm,$e_tm,$len,$sip,$sp,$dip,$dp,$tb,$mbps) = split(/\s+/,$sorted_lines[$m]);
	
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
	
		printf SORTED_SAVE "%-12s %-9s %-9s %7.1f  %-$dns_column_widthss  %-6s   %-$dns_column_widthss  %-6s  %14s  %8.3f\n",$s_epoch,$s_tm,$e_tm,$len,$sip,$sp,$dip,$dp,$tb,$mbps;
	}
}
close(SORTED_SAVE);

print " <tr><td>&nbsp</td></tr>";
print " <tr><td>&nbsp</td></tr>";
print " </table>\n";
print " </div>\n";

if ($ANALYSIS && !$SAVED) {
	print " <div id=service_bottom>\n";
	print "  <span class=analyze_lead></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_filter^$filter_hash\">\n";
	print "  <button class=links type=submit>Save Filter</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer_b></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^PeakSrc^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>SIP Peak</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^TotalSrc^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>SIP Tot</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^PeakSpt^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>SPT Peak</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^TotalSpt^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>SPT Tot</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer_b></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
	print "  <button class=active type=submit>FlowGrapher</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer_b></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^PeakDst^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>DIP Peak</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^TotalDst^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>DIP Tot</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^PeakDpt^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>DPT Peak</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowGrapher_Analyze.cgi?$active_dashboard^TotalDpt^filter_hash=$filter_hash\">\n";
	print "  <button class=analyze type=submit>DPT Tot</button>\n";
	print "  </form>\n";
	print "  <span class=analyze_spacer_b></span>\n";
	print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_report^$new_filter_hash\">\n";
	print "  <button class=links type=submit>Save Report</button>\n";
	print "  </form>\n";
	print " </div>\n";
} else {
	&create_UI_service("FlowGrapher_Main","service_bottom",$active_dashboard,$filter_hash);
}

&finish_the_page("FlowGrapher_Main");
