#! /usr/bin/perl
#
#  Purpose:
#  FlowGrapher_Analyze.cgi works on an existing FlowGrapher report to
#  re-graph the traffic subdivided either by sources or destinations.
#
#  Description:
#  The script is invoked from one of four buttons created at the bottom 
#  of a FlowGrapher report that has been created using either the "Pro-rated"
#  or flows "Initiated" graph types. The largest contributing sources
#  and destinations have been identified by the FlowGrapher run and
#  kept in the Saved file. This script will collect buckets for each 
#  source or destination as selected by the user. The script also will
#  subdivide the traffic by provided largest "peak" contributors. The
#  same filtering crieria are used.
#
#  Input arguments (received from the form):
#  Name                 Description
#  -----------------------------------------------------------------------
#  device_name          An identifying name of the device (e.g. router1)
#  flow_select          Identifies which flows to include wrt time period
#  start_date           Start date of analysis period
#  start_time           Start time of analysis period
#  end_date             End date of analysis period
#  end_time             End time of analysis period
#  source_addresses     Constrain flows examined to these source IP addresses
#  source_ports         Constrain flows examined to these source ports
#  source_ifs           Constrain flows examined to these input interfaces
#  sif_names            Constrain flows examined to these named interfaces
#  source_ases          Constrain flows examined to these source ASes
#  dest_addresses       Constrain flows examined to these dest. IP addresses
#  dest_ports           Constrain flows examined to these dest. ports
#  dest_ifs             Constrain flows examined to these output interfaces
#  dif_names            Constrain flows examined to these named interfaces
#  dest_ases            Constrain flows examined to these dest. ASes
#  tos_fields           Constrain flows examined by specified TOS field values
#  tcp_flags            Constrain flows examined by specified TCP flag values
#  exporter             Constrain flows examined by specified exporter IP address
#  nexthop_ips          Constrain flows examined to specified Next Hop IP address
#  protocols            Constrain flows examined to these protocols
#  detail_lines         Limit of detailed flow lines to print out for graphs
#  bucket_size          Amount of time for each graphing 'bucket'
#  graph_multiplier    	Multiplier of standard width for presented graph
#  resolve_addresses    Whether or not to resolve IP addresses
#  graph_type           Type of Graph bits/flows/packets
#  sampling_multiplier  Value to multiply all flow data (for sampled routers)
#  src-objects          The five largest source contributers (peak or total)
#  dst-objects          The five largest destination contributers (peak or total)
#  analyze_method       Either: PeakSrc, PeakDst, TotalSrc, TotalDst
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  07/04/2014      4.4     Original released version
#  J. Loiacono  11/02/2014      4.5     SiLK local timezone fixes
#                                       IPv6 hyper-link fixes
#  J. Loiacono  01/26/2015      4.6     Timezone from system (not Configuration)
#                                       Fixed local timezone processing for SiLK
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
use File::stat;
use GD;
use GD::Graph::linespoints;
use GD::Graph::mixed;
use GD::Graph::bars;

time_check("start");
$run_start = time;

if ($debug_grapher eq "Y") { open (DEBUG,">$work_directory/DEBUG_ANALYZE"); }
if ($debug_grapher eq "Y") { print DEBUG "In FlowGrapher_Analyze.cgi\n"; }

$query_string  = $ENV{'QUERY_STRING'};
$query_string  =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge;
($active_dashboard,$analyze_method,$filter_hash_string) = split(/\^/,$query_string);
($label,$filter_hash) = split(/=/,$filter_hash_string);
$filter_source = substr($filter_hash,0,2);
$hash_file     = substr($filter_hash,3,255);
($part1,$part2,$existing_suffix) = split(/_/,$hash_file);
$saved_file = "$work_directory/$hash_file";
$existing_output_file = "$work_directory/FlowGrapher_output_$existing_suffix";

# Tie in the 'names' file which saves IP address resolved names 
      
if (eval 'local $SIG{"__DIE__"}= sub { }; use GDBM_File;   
        tie %host_names, "GDBM_File", "$names_directory/names", GDBM_WRCREAT, 0666;' ) { 
	if ($debug_grapher eq "Y") { print DEBUG "Using GDBM\n"; } };  
if (eval 'local $SIG{"__DIE__"}= sub { }; use NDBM_File; use Fcntl;    
        tie %host_names, "GDBM_File", "$names_directory/names", GDBM_WRCREAT, 0666;' ) {
	if ($debug_grapher eq "Y") { print DEBUG "Using NDBM\n"; } };  

# Tie in the 'ports' file which saves port_id (port_num:port_type) to port_name mapping
      
if (eval 'local $SIG{"__DIE__"}= sub { }; use GDBM_File;   
        tie %port_names, "GDBM_File", "$names_directory/ports", GDBM_WRCREAT, 0666;' ) { 
	if ($debug_grapher eq "Y") { print DEBUG "Using GDBM\n"; } };  
if (eval 'local $SIG{"__DIE__"}= sub { }; use NDBM_File; use Fcntl;    
        tie %port_names, "GDBM_File", "$names_directory/ports", GDBM_WRCREAT, 0666;' ) {
	if ($debug_grapher eq "Y") { print DEBUG "Using NDBM\n"; } };  

# Set up graphing colors

GD::Graph::colour::read_rgb("FlowGrapher_Colors") or die "cannot read colors";

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
}    
$hex_colors{"standard"} = $rrd_area; 
sub dec2hex($) { return sprintf("%lx", $_[0]) } 

# Load up the FlowGrapher Saved file and start up the Analysis Saved file 

$saved_suffix = &get_suffix;
$saved_hash   = "FlowGrapher_save_$saved_suffix"; 
$new_filter_hash  = "FA_$saved_hash";
$saved_html   = "$work_directory/$saved_hash"; 

open(SAVED,"<$saved_file");
chomp (@saved_lines = <SAVED>);
close SAVED;

open(SAVE_ANALYSIS,">$saved_html");

foreach $saved_line (@saved_lines) {

        if ($saved_line =~ /BEGIN FILTERING/) {
                $found_parameters = 1;
                print SAVE_ANALYSIS "$saved_line\n";
                next; }
        if ($found_parameters) {
                if ($saved_line =~ /END FILTERING/) { $found_parameters = 0;}
                ($field,$field_value) = split(/: /,$saved_line);
                if ($field eq "device_name")         { $device_name = $field_value; }
                if ($field eq "start_date")          { $start_date = $field_value; }
                if ($field eq "start_time")          { $start_time = $field_value; }
                if ($field eq "end_date")            { $end_date = $field_value; }
                if ($field eq "end_time")            { $end_time = $field_value; }
                if ($field eq "protocols")           { $protocols = $field_value; }
                if ($field eq "bucket_size")         { $bucket_size = $field_value; }
                if ($field eq "graph_multiplier")    { $graph_multiplier = $field_value; }
                if ($field eq "sampling_multiplier") { $sampling_multiplier = $field_value; }
                if ($field eq "resolve_addresses")   { $resolve_addresses = $field_value; }
                if ($field eq "graph_type")          { $graph_type = $field_value; }
                if ($field eq "IPFIX")               { $IPFIX = $field_value; }
                if ($field eq "Description")         { $report_name = $field_value; }
                if ($field eq "filter_hash")         { $saved_line =~ s/FG_/FA_/; }
                print SAVE_ANALYSIS "$saved_line\n";
                next;
	}
        if ($saved_line =~ /BEGIN ANALYSIS/) {
                print SAVE_ANALYSIS "$saved_line\n";
		$in_analysis = 1;
		next;
        }
        if ($saved_line =~ /END ANALYSIS/) {
                print SAVE_ANALYSIS "$saved_line\n";
		last;
        }
	if ($in_analysis) {
                print SAVE_ANALYSIS "$saved_line\n";
		($object_label,$object_info) = split(/: /,$saved_line);
		if ($object_label eq  "total-measured_total") { 
			$total_measured_total = $object_info;
			next;
		}
		if ($object_label eq  "total-measured_peak") { 
			$total_measured_peak = $object_info;
			next;
		}
		($object_label,$object_num) = split(/_/,$object_label);
		($object_address,$object_value) = split(/ /,$object_info);
		if (($analyze_method eq "TotalSrc") || ($analyze_method eq "TotalDst")) {
			$analyzing_hosts = 1;
			if ($object_label =~ "total-src") { @src_objects[$object_num] = $object_address; @src_values[$object_num] = $object_value;}
			if ($object_label =~ "total-dst") { @dst_objects[$object_num] = $object_address; @dst_values[$object_num] = $object_value;}
		} elsif (($analyze_method eq "TotalSpt") || ($analyze_method eq "TotalDpt")) {
			if ($object_label =~ "total-spt") { @src_objects[$object_num] = $object_address; @src_values[$object_num] = $object_value;}
			if ($object_label =~ "total-dpt") { @dst_objects[$object_num] = $object_address; @dst_values[$object_num] = $object_value;}
		} elsif (($analyze_method eq "PeakSrc") || ($analyze_method eq "PeakDst")) {
			$analyzing_hosts = 1;
			if ($object_label =~  "peak-src") { @src_objects[$object_num] = $object_address; @src_values[$object_num] = $object_value;}
			if ($object_label =~  "peak-dst") { @dst_objects[$object_num] = $object_address; @dst_values[$object_num] = $object_value;}
		} elsif (($analyze_method eq "PeakSpt") || ($analyze_method eq "PeakDpt")) {
			if ($object_label =~  "peak-spt") { @src_objects[$object_num] = $object_address; @src_values[$object_num] = $object_value;}
			if ($object_label =~  "peak-dpt") { @dst_objects[$object_num] = $object_address; @dst_values[$object_num] = $object_value;}
		}
	}
}

if ($bucket_size eq "300E") {
	$bucket_size = 300;
	$use_bucket_endtime = 1;
} 

if (($analyze_method =~ /Src/) || ($analyze_method =~ /Spt/)) { @analyzed_objects = @src_objects; @analyzed_values = @src_values; }
if (($analyze_method =~ /Dst/) || ($analyze_method =~ /Dpt/)) { @analyzed_objects = @dst_objects; @analyzed_values = @dst_values; }

unshift(@analyzed_objects,"All Others");
for ($i=0;$i<$analyze_count;$i++) { $analyzed_measured += $analyzed_values[$i]; }
if ($analyze_method =~ /Peak/)  { $allothers_measured = $total_measured_peak  - $analyzed_measured; }
if ($analyze_method =~ /Total/) { $allothers_measured = $total_measured_total - $analyzed_measured; }
if ($allothers_measured < 0) { $allothers_measured = 0; }
unshift(@analyzed_values,$allothers_measured);

if ($debug_grapher eq "Y") {
	print DEBUG "graph_type: $graph_type  analyze_method: $analyze_method\n";
	for ($i=0;$i<$analyze_count;$i++) {
		print DEBUG "     src_object_$i: $src_objects[$i] $src_values[$i]\n";
	}
	for ($i=0;$i<$analyze_count;$i++) {
		print DEBUG "     dst_object_$i: $dst_objects[$i] $dst_values[$i]\n";
	}
	for ($i=0;$i<=$analyze_count;$i++) {
		print DEBUG "analyzed_object_$i: $analyzed_objects[$i] $analyzed_values[$i]\n";
	}
	print DEBUG " total_measured_peak: $total_measured_peak\n";
	print DEBUG "total_measured_total: $total_measured_total\n";
}

# Start the web page output
 
&create_UI_top($active_dashboard);
&create_UI_service("FlowGrapher_Main","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";
print " <span class=text16>FlowGrapher Analysis from $device_name</span>\n";

open(DATE,"date 2>&1|");   
while (<DATE>) {  
	($d_tz,$m_tz,$dt_tz,$t_tz,$time_zone,$y_tz) = split(/\s+/,$_);  
}        

# Establish Start-of-Year epochs, secs in months, for current, prior, and next years to speed processing of each flow

($mn,$da,$yr) = split(/\//,$start_date);
$current_year = $yr; 
$prior_year   = $current_year - 1; 
$next_year    = $current_year + 1; 
$start_mn     = $mn;
$midnight     = "00:00:00"; 

$current_year_date = "01" ."/". "01" ."/". $current_year; 
if (($IPFIX) && ($silk_compiled_localtime ne "Y")) {
	$current_year_epoch  = date_to_epoch($current_year_date,$midnight,"GMT"); 
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$current_year_dst) = gmtime($current_year_epoch);
} else {
	$current_year_epoch  = date_to_epoch($current_year_date,$midnight,"$time_zone"); 
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$current_year_dst) = localtime($current_year_epoch);
}
if ($debug_grapher eq "Y") { print DEBUG "current_year_date: $current_year_date   current_year_epoch: $current_year_epoch  current_year_dst: $current_year_dst\n"; }
  
$prior_year_date = "01" ."/". "01" ."/". $prior_year; 
if (($IPFIX) && ($silk_compiled_localtime ne "Y")) {
	$prior_year_epoch  = date_to_epoch($prior_year_date,$midnight,"GMT"); 
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$prior_year_dst) = gmtime($prior_year_epoch);
} else {
	$prior_year_epoch    = date_to_epoch($prior_year_date,$midnight,"$time_zone"); 
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$prior_year_dst) = localtime($prior_year_epoch);
}
if ($debug_grapher eq "Y") { print DEBUG "  prior_year_date: $prior_year_date     prior_year_epoch: $prior_year_epoch    prior_year_dst: $prior_year_dst\n"; }
  
$next_year_date = "01" ."/". "01" ."/". $next_year; 
if (($IPFIX) && ($silk_compiled_localtime ne "Y")) {
	$next_year_epoch  = date_to_epoch($next_year_date,$midnight,"GMT"); 
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$next_year_dst) = gmtime($next_year_epoch);
} else {
	$next_year_epoch     = date_to_epoch($next_year_date,$midnight,"$time_zone");
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$next_year_dst) = localtime($next_year_epoch);
}
if ($debug_grapher eq "Y") { print DEBUG "   next_year_date: $next_year_date      next_year_epoch: $next_year_epoch     next_year_dst: $next_year_dst\n"; }

#   ... adjust Start-of-Year epochs, if Daylight Savings is in effect (does not impact GMT)

if (($IPFIX) && ($silk_compiled_localtime ne "Y")) {
	$start_epoch = date_to_epoch($start_date,$start_time,"GMT");
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$start_epoch_dst)  = gmtime($start_epoch);
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$current_year_dst) = gmtime($current_year_epoch);
} else {
	$start_epoch = date_to_epoch($start_date,$start_time,"LOCAL");
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$start_epoch_dst)  = localtime($start_epoch);
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$current_year_dst) = localtime($current_year_epoch);
}

if ($debug_grapher eq "Y") { print DEBUG "Current Year: $current_year_date  Epoch: $current_year_epoch  DST: $current_year_dst\n"; }
if ($debug_grapher eq "Y") { print DEBUG "  Start Date:  $FORM{start_date}  Epoch: $start_epoch  DST: $start_epoch_dst\n"; }

if ($start_epoch_dst > $current_year_dst) {
        $current_year_epoch -= $time_zone_dst_offset;
        $prior_year_epoch   -= $time_zone_dst_offset;
        $next_year_epoch    -= $time_zone_dst_offset;
} elsif ($start_epoch_dst < $current_year_dst) {
        $current_year_epoch += $time_zone_dst_offset;
        $prior_year_epoch   += $time_zone_dst_offset;
        $next_year_epoch    += $time_zone_dst_offset;
}

$secs_to_month[2]  = 31 * 86400;    
$secs_to_month[3]  = 28 * 86400 + $secs_to_month[2];    
$secs_to_month[4]  = 31 * 86400 + $secs_to_month[3];    
$secs_to_month[5]  = 30 * 86400 + $secs_to_month[4];    
$secs_to_month[6]  = 31 * 86400 + $secs_to_month[5];    
$secs_to_month[7]  = 30 * 86400 + $secs_to_month[6];    
$secs_to_month[8]  = 31 * 86400 + $secs_to_month[7];    
$secs_to_month[9]  = 31 * 86400 + $secs_to_month[8];    
$secs_to_month[10] = 30 * 86400 + $secs_to_month[9];    
$secs_to_month[11] = 31 * 86400 + $secs_to_month[10];  
$secs_to_month[12] = 30 * 86400 + $secs_to_month[11];

if (($no_devices_or_exporters eq "N") && (($device_name eq "") && ($exporter eq ""))) {
        print "<br><br><b>Must select a device or an exporter. <p>Use the \"back\" key to save inputs</b><br>";
        exit; 
}

# Retrieve current time to use as a file suffix to permit more than one user to generate reports
 
($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime(time);
$mnth++;
$yr += 1900;
if ((0 < $mnth) && ($mnth < 10)) { $mnth = "0" . $mnth; }
if ((0 < $date) && ($date < 10)) { $date = "0" . $date; }
if ((0 <= $hr)  && ($hr   < 10)) { $hr  = "0"  . $hr; }
if ((0 <= $min) && ($min  < 10)) { $min = "0"  . $min; }
if ((0 <= $sec) && ($sec  < 10)) { $sec = "0"  . $sec; }
$suffix = $hr . $min . $sec;
 
# Determine the flow files concatenation start and end time

if ($IPFIX) {

	# Obtain user requested time period start time in SiLK-storage time zone

	($temp_mnth_s,$temp_day_s,$temp_yr_s) = split(/\//,$start_date);
	($temp_hr_s,$temp_min_s,$temp_sec_s)  = split(/:/,$start_time);
	$start_epoch = timelocal($temp_sec_s,$temp_min_s,$temp_hr_s,$temp_day_s,$temp_mnth_s-1,$temp_yr_s-1900);
	if ($silk_compiled_localtime eq "Y") {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($start_epoch);
	} else {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = gmtime($start_epoch);
	}
	$yr += 1900; $mnth++;
	if (length($mnth) < 2) { $mnth = "0" . $mnth; }
	if (length($date) < 2) { $date = "0" . $date; }
	if (length($hr)   < 2) { $hr   = "0" . $hr; }
	if (length($min)  < 2) { $min  = "0" . $min; }
	if (length($sec)  < 2) { $sec  = "0" . $sec; }
	$silk_period_start = $yr ."/". $mnth ."/". $date .":". $hr .":". $min .":". $sec;

	# Obtain user requested time period end time in SiLK-storage time zone

	($temp_mnth_e,$temp_day_e,$temp_yr_e) = split(/\//,$end_date);
	($temp_hr_e,$temp_min_e,$temp_sec_e)  = split(/:/,$end_time);
	$end_epoch = timelocal($temp_sec_e,$temp_min_e,$temp_hr_e,$temp_day_e,$temp_mnth_e-1,$temp_yr_e-1900);
	if ($silk_compiled_localtime eq "Y") {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($end_epoch);
	} else {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = gmtime($end_epoch);
	}
	$yr += 1900; $mnth++;
	if (length($mnth) < 2) { $mnth = "0" . $mnth; }
	if (length($date) < 2) { $date = "0" . $date; }
	if (length($hr)   < 2) { $hr   = "0" . $hr; }
	if (length($min)  < 2) { $min  = "0" . $min; }
	if (length($sec)  < 2) { $sec  = "0" . $sec; }
	$silk_period_end = $yr ."/". $mnth ."/". $date .":". $hr .":". $min .":". $sec;
		
} else {

	$start_epoch = date_to_epoch($start_date,$start_time,$time_zone);
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$start_epoch_dst) = localtime($start_epoch);
	if ($debug_grapher eq "Y") { print DEBUG "       start_date: $FORM{start_date}           start_epoch: $start_epoch   start_epoch_dst: $start_epoch_dst\n"; }
	$start_flows = &flow_date_time($start_epoch,"LOCAL");
	
	$end_epoch = date_to_epoch($end_date,$end_time,$time_zone);
	($dst_sc,$dst_mi,$dst_hr,$dst_da,$dst_mn,$dst_yr,$dst_dy,$dst_yd,$end_epoch_dst) = localtime($end_epoch);
	if ($debug_grapher eq "Y") { print DEBUG "         end_date: $FORM{end_date}             end_epoch: $end_epoch     end_epoch_dst: $end_epoch_dst\n"; }
	$end_flows = &flow_date_time($end_epoch,"LOCAL");
}

$end_peak_period = $start_epoch + ($analyze_peak_width * $bucket_size);

$report_length   = $end_epoch - $start_epoch;
if ($report_length <= 0) { &print_error("End time ($FORM{end_date} $end_time) earlier than Start time ($FORM{start_date} $start_time)"); }

$total_buckets = int($report_length / $bucket_size) - 1;
if ($total_buckets < 8) { &print_error("Graphing Period ($report_length secs) must be at least 9 times the Sample Time ($bucket_size secs)"); }
 
# Collect data into buckets to form the plot for the graph

time_check("start Examine_flows");
open (FLOWS,"<$existing_output_file");
while (<FLOWS>) {
	
        $first_char = substr($_,0,1);
        if (!($first_char =~ /[0-9]/)) { next; }

        if ($IPFIX) {
                $silk_record = $_;
                $silk_record =~ s/\s+//g;
                ($s_time,$e_time,$dur,$sif,$sip,$sp,$dif,$dip,$dp,$p,$fl,$pkt,$oct) = split(/\|/,$silk_record);
		if ($graph_type =~ "fpsi") { $dur = 1.0; }
        } else {
                ($s_time,$e_time,$sif,$sip,$sp,$dif,$dip,$dp,$p,$fl,$pkt,$oct) = split(/\s+/,$_);
        }

        $obs++;
        $flows = 1;

        # Find flow start epoch (this method avoids using timelocal which is comparatively slow)

        if ($IPFIX) {
                $md = substr($s_time,5,2) . substr($s_time,8,2);
                $s_tm = substr($s_time,11,8);
                $s_ms = substr($s_time,20,3);
        } else {
                ($md,$s_tm,$s_ms) = split(/\./,$s_time);
        }

	$smd              = $md;
        $mn               = substr($md,0,2);
        $da               = substr($md,2,2);
        ($hr,$mi,$sc)     = split(/:/,$s_tm);

        $ssc_ms           = $sc + (0.001 * $s_ms);
        $s_mdhms          = $md . $s_tm;

        if ($s_mdhms eq $s_last_mdhms) {
                $s_epoch = $s_last_epoch;
        } else {

                $yr_secs = 0;
                $hr_secs = ($mi * 60) + $sc;
                $da_secs = ($hr * 3600) + $hr_secs;
                $mn_secs = (($da - 1) * 86400) + $da_secs;
                $yr_secs = $secs_to_month[$mn] + $mn_secs;
                if ((($yr % 4) == 0) && ($mn gt "02")) { $yr_secs += 86400; }

                $base_epoch = $current_year_epoch;
                if (($start_mn eq "11") || ($start_mn eq "12")) {
                        if (($mn eq "01") || ($mn eq "02")) {
                                $base_epoch = $next_year_epoch;
                        }
                } elsif (($start_mn eq "01") || ($start_mn eq "02")) {
                        if (($mn eq "11") || ($mn eq "12")) {
                                $base_epoch = $prior_year_epoch;
                        }
                }

                $s_epoch = $base_epoch + $yr_secs;
                $s_last_mdhms = $s_mdhms;
                $s_last_epoch = $s_epoch;
        }

        $s_epoch_ms = $s_epoch + (0.001 * $s_ms);
        $start_delta = $s_epoch_ms - $start_epoch;

	if ($graph_type =~ /fpsi/) {
		if ($s_epoch_ms < $start_epoch) { next; }
		if ($s_epoch_ms > $end_epoch)   { next; }
	}

        # Find flow end epoch

        if ($IPFIX) {
                $emd = substr($e_time,5,2) . substr($e_time,8,2);
                $e_tm = substr($e_time,11,8);
                $e_ms = substr($e_time,20,3);
                $e_epoch_ms = $s_epoch_ms + $dur;
                $e_epoch = int($e_epoch_ms);
        } else {
                ($md,$e_tm,$e_ms) = split(/\./,$e_time);
		$emd              = $md;
                $mn               = substr($md,0,2);
                $da               = substr($md,2,2);
                ($hr,$mi,$sc)     = split(/:/,$e_tm);
                $esc_ms           = $sc + (0.001 * $e_ms);
                $e_mdhms          = $md . $e_tm;

                if ($e_mdhms eq $e_last_mdhms) {
                        $e_epoch = $e_last_epoch;
                } else {

                        $yr_secs = 0;
                        $hr_secs = ($mi * 60) + $sc;
                        $da_secs = ($hr * 3600) + $hr_secs;
                        $mn_secs = (($da - 1) * 86400) + $da_secs;
                        $yr_secs = $secs_to_month[$mn] + $mn_secs;
                        if ((($yr % 4) == 0) && ($mn gt "02")) { $yr_secs += 86400; }

                        $base_epoch = $current_year_epoch;
                        if (($start_mn eq "11") || ($start_mn eq "12")) {
                                if (($mn eq "01") || ($mn eq "02")) {
                                        $base_epoch = $next_year_epoch;
                                }
                        } elsif (($start_mn eq "01") || ($start_mn eq "02")) {
                                if (($mn eq "11") || ($mn eq "12")) {
                                        $base_epoch = $prior_year_epoch;
                                }
                        }

                        $e_epoch = $base_epoch + $yr_secs;
                        $e_last_mdhms = $e_mdhms;
                        $e_last_epoch = $e_epoch;
                        $e_epoch_ms = $e_epoch + (0.001 * $e_ms);
                }
        }

        $e_epoch_ms  = $e_epoch + (0.001 * $e_ms);
        $end_delta   = $e_epoch_ms - $start_epoch;

        $flow_length_ms = $e_epoch_ms - $s_epoch_ms;
	if ($graph_type =~ /fpsi/) {
		$e_epoch_ms = $s_epoch_ms + 1.000;
        	$end_delta  = $start_delta;
	}

        if ($e_epoch_ms <= $start_epoch) { next; }
        if ($s_epoch_ms >= $end_epoch)   { next; }

        # OK, we have a flow that occurs within the time-frame

        $obs_included++;

        if ($flow_length_ms <= 0) { $flow_length_ms = 0.001; }
        $flow_length = $flow_length_ms;

        if ($graph_type =~ /pps/) {
                $flow_bits = $pkt;
        } elsif ($graph_type =~ /fpsa/) {
                $flow_bits = $flow_length;
        } elsif ($graph_type =~ /fpsi/) {
                $flow_bits = 1;
        } else {
                $flow_bits = $oct * 8;
        }

        if ($sampling_multiplier > 1) { $flow_bits *= $sampling_multiplier; }

	# Set the analyze object

	if ($analyze_method =~ /Src/) { $current_object = $sip; }
	if ($analyze_method =~ /Dst/) { $current_object = $dip; }
	if ($analyze_method =~ /Spt/) { $current_object = $sp; }
	if ($analyze_method =~ /Dpt/) { $current_object = $dp; }

        # Determine first, last, and total number of buckets spanned by flow

        if ($start_delta <= 0) {
                $secs_in_first_bucket = 0;
                $first_bucket = 0;
        } else {
                $first_bucket = int($start_delta / $bucket_size);
                $secs_in_first_bucket = $bucket_size - ((($start_delta/$bucket_size) - $first_bucket) * $bucket_size);
        }

        if ($end_delta > $report_length) {
                $last_bucket = int($report_length / $bucket_size) - 1;
                $secs_in_last_bucket = 0;
        } else {
                $last_bucket = int($end_delta / $bucket_size);
                $secs_in_last_bucket = (($end_delta/$bucket_size) - $last_bucket) * $bucket_size;
        }

        if ($first_bucket > $last_bucket) { $first_bucket = $last_bucket; }
        $num_buckets = $last_bucket - $first_bucket + 1;

        # Determine bucket amount and accumulate into buckets, start with bits/second

	$per_second_amount = $flow_bits / $flow_length;

        if ($num_buckets == 1) {
                if (($first_bucket == 0) && ($start_delta < 0)) {
			for ($j=1;$j<=$analyze_count;$j++) {
				if ($current_object eq $analyzed_objects[$j]) {
                       			$buckets[$j][$first_bucket] += $secs_in_last_bucket * $per_second_amount;
					$analyzed_object = 1;
				}
			}
			if (!$analyzed_object) { $buckets[0][$first_bucket] += $secs_in_last_bucket * $per_second_amount; }
                } elsif (($first_bucket eq $total_buckets) && ($end_delta > $report_length)) {
			for ($j=1;$j<=$analyze_count;$j++) {
				if ($current_object eq $analyzed_objects[$j]) {
                       			$buckets[$j][$first_bucket] += $secs_in_first_bucket * $per_second_amount;
					$analyzed_object = 1;
				}
			}
			if (!$analyzed_object) { $buckets[0][$first_bucket] += $secs_in_first_bucket * $per_second_amount; }
                } else {
			for ($j=1;$j<=$analyze_count;$j++) {
				if ($current_object eq $analyzed_objects[$j]) {
					$buckets[$j][$first_bucket] += $flow_bits;
					$analyzed_object = 1;
				}
			}
			if (!$analyzed_object) { $buckets[0][$first_bucket] += $flow_bits; }
                }
        } else {
                for ($i=$first_bucket;$i<=$last_bucket;$i++) {

                        # Pro-rate for first bucket
                        if ($i == $first_bucket) {
                               	if ($start_delta < 0) {
                                       	$bucket_amount = $bucket_size * $per_second_amount;
                               	} else {
                                       	$bucket_amount = $secs_in_first_bucket * $per_second_amount;
                               	}
                        }

                        # Pro-rate for last bucket
                        elsif ($i == $last_bucket) {
                               	if ($end_delta > $report_length) {
                                       	$bucket_amount = $bucket_size * $per_second_amount;
                               	} else {
                                       	$bucket_amount = $secs_in_last_bucket * $per_second_amount;
                               	}
                        }

                        # All other buckets ...
                        else {
                               	$bucket_amount = $bucket_size * $per_second_amount;
                        }

                        # Accumulate into the buckets
			for ($j=1;$j<=$analyze_count;$j++) {
				if ($current_object eq $analyzed_objects[$j]) {
					$buckets[$j][$i] += $bucket_amount;
					$analyzed_object = 1;
				}
			}
			if (!$analyzed_object) { $buckets[0][$i] += $bucket_amount; }
                }
        }
	$analyzed_object = 0;
}

if ($debug_grapher eq "Y") { 
	print DEBUG "looked at: $obs flows\n";
	print DEBUG "passed   : $obs_included flows\n";
}

time_check("done_Examine_flows");
close FLOWS;
 
# Determine the statistics and graphing times
 
$total_graph_times = $report_length / $bucket_size;
$skip_graph_times  = $total_graph_times / 8;
 
for ($i=0;$i<$total_graph_times;$i++) {

	for ($j=0;$j<=$analyze_count;$j++) {
        	$buckets[$j][$i] = $buckets[$j][$i] / $bucket_size;
		if ($buckets[$j][$i] eq "") { $buckets[$j][$i] = 0; }
		if ($j == 0) { push (@bucket_0,$buckets[$j][$i]); }
		if ($j == 1) { push (@bucket_1,$buckets[$j][$i]); }
		if ($j == 2) { push (@bucket_2,$buckets[$j][$i]); }
		if ($j == 3) { push (@bucket_3,$buckets[$j][$i]); }
		if ($j == 4) { push (@bucket_4,$buckets[$j][$i]); }
		if ($j == 5) { push (@bucket_5,$buckets[$j][$i]); }
		if ($j == 6) { push (@bucket_6,$buckets[$j][$i]); }
		if ($j == 7) { push (@bucket_7,$buckets[$j][$i]); }
		if ($j == 8) { push (@bucket_8,$buckets[$j][$i]); }
		if ($j == 9) { push (@bucket_9,$buckets[$j][$i]); }
		if ($j == 10){ push (@bucket_10,$buckets[$j][$i]); }
	}

        $graph_labels[$i] = "";
        if (($i % $skip_graph_times) == 0) {
                $bucket_time = $start_epoch + (($i) * $bucket_size);
                $bucket_time_d = epoch_to_date($bucket_time,$time_zone);
                ($bucket_date,$bucket_hms) = split(/ /,$bucket_time_d);
                $graph_labels[$i] = $bucket_hms;
                if (($i != 0) && (!$found_first)) {
                        $x_tick_offset = $i;
                        $x_label_skip = $i;
                        $found_first = 1;
                }
        }
}

if ($use_bucket_endtime) {
	unshift(@bucket_0,0);
	unshift(@bucket_1,0);
	unshift(@bucket_2,0);
	unshift(@bucket_3,0);
	unshift(@bucket_4,0);
	unshift(@bucket_5,0);
	unshift(@bucket_6,0);
	unshift(@bucket_7,0);
	unshift(@bucket_8,0);
	unshift(@bucket_9,0);
	unshift(@bucket_10,0);
	$bucket_size = "300E";
}

$bucket_time = $end_epoch; 
$bucket_time_d = epoch_to_date($bucket_time,$time_zone); 
($bucket_date,$bucket_hms) = split(/ /,$bucket_time_d); 
$graph_labels[$total_graph_times] = $bucket_hms;
push (@graph_labels," ");
 
# Create the plot ...

if ($analyze_count == 3) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3]); }
if ($analyze_count == 4) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4]); }
if ($analyze_count == 5) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4],[@bucket_5]); }
if ($analyze_count == 6) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4],[@bucket_5],[@bucket_6]); }
if ($analyze_count == 7) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4],[@bucket_5],[@bucket_6],[@bucket_7]); }
if ($analyze_count == 8) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4],[@bucket_5],[@bucket_6],[@bucket_7],[@bucket_8]); }
if ($analyze_count == 9) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4],[@bucket_5],[@bucket_6],[@bucket_7],[@bucket_8],[@bucket_9]); }
if ($analyze_count == 10) {
@plot = ([@graph_labels],[@bucket_0],[@bucket_1],[@bucket_2],[@bucket_3],[@bucket_4],[@bucket_5],[@bucket_6],[@bucket_7],[@bucket_8],[@bucket_9],[@bucket_10]); }
 
# Create the graph ...
 
$horizontal  = "Time: $time_zone";

if ($graph_type =~ /bps/) { $vertical = "Bits/Second"; }
if ($graph_type =~ /pps/) { $vertical = "Packets/Second"; }
if ($graph_type =~ /fps/) { $vertical = "Flows/Second"; }

if ($analyze_method eq "PeakSrc")  { $description = "Analysis by Source - Peak"; $accentclr = "";}
if ($analyze_method eq "PeakDst")  { $description = "Analysis by Destination - Peak"; $accentclr = "";}
if ($analyze_method eq "TotalSrc") { $description = "Analysis by Source - Total"; }
if ($analyze_method eq "TotalDst") { $description = "Analysis by Destination - Total"; }
if ($analyze_method eq "PeakSpt")  { $description = "Analysis by Source Port - Peak"; $accentclr = "";}
if ($analyze_method eq "PeakDpt")  { $description = "Analysis by Destination Port - Peak"; $accentclr = "";}
if ($analyze_method eq "TotalSpt") { $description = "Analysis by Source Port - Total"; }
if ($analyze_method eq "TotalDpt") { $description = "Analysis by Destination Port - Total"; }

$accentclr = "gray60";
$x_ticks     = 1;
$long_ticks  = 1;
 
$graph_width *= $graph_multiplier;
$analyze_height = $graph_height + $analyze_extension;
$graph = GD::Graph::area->new($graph_width,$analyze_height);

$graph->set(
        boxclr               => "$boxclr",
        bgclr                => "$bgclr",
        transparent          => "$transparent",
	accentclr	     => "$accentclr",
        borderclrs           => "$borderclrs",
        fgclr                => "$fgclr",
        labelclr             => "$labelclr",
        axislabelclr         => "$axislabelclr",
        legendclr            => "$legendclr",
        valuesclr            => "$valuesclr",
        textclr              => "$textclr",
        dclrs                => $analyze_colors,
        types                => ['area'],
	cumulate             => "1",
        line_width           => "1",
        t_margin             => "$t_margin",
        b_margin             => "$b_margin",
        l_margin             => "$l_margin",
        r_margin             => "$r_margin",
        x_ticks              => "$x_ticks",
        long_ticks           => "$long_ticks",
        x_label_skip         => "$x_label_skip",
        x_tick_offset        => "$x_tick_offset",
        y_label              => "$vertical",
        x_label              => "$horizontal",
        x_label_position     => "0.5",
        y_number_format      => \&y_format,
        skip_undef           => "$skip_undef",
        title                => "$description",
        legend_marker_width  => "24",
        legend_marker_height => "4",
	lg_cols		     => "3"
        ) or warn $graph->error;
 
$title_font = "('arial', 16)";
$title_font = "('arial', 16)";
$graph->set_legend(@analyzed_objects);
$graph->set_x_axis_font($x_axis_font);
$graph->set_title_font(gdSmallFont);
 
# Create the image and write it to the correct directory

$image = $graph->plot(\@plot) or die print $graph->error;
$png_filename  = "FlowGrapher_save_" . $saved_suffix . ".png";
$flowgraph_link = "$graphs_short/$png_filename";
open(PNG,">$graphs_directory/$png_filename");
binmode PNG;
print PNG $image->png;
close PNG;
 
time_check("create_graph");

# Create the FlowGrapher Content

&create_filter_output("FlowGrapher_Main",$filter_hash);

print " <br>\n";
print " <center><img src=$flowgraph_link></center>\n";

@analyzed_colors = @$analyze_colors;
for ($j=0;$j<=$analyze_count;$j++) {
	$output_value = $analyzed_values[$j];
	$output_value = $output_value .":". $hex_colors{$analyzed_colors[$j]};
	$output_values{$analyzed_objects[$j]} = $output_value;
}
if ($analyze_method =~ /Total/) {
	@sorted_objects = sort { $output_values{$a} <=> $output_values{$b} } keys %output_values;
} else {
	@sorted_objects = sort { $output_values{$b} <=> $output_values{$a} } keys %output_values;
}

if ($analyzing_hosts) {
	$object_header_id = "Host IP";
	$object_header_name = "Host Name";
} else {
	$object_header_id = "Port";
	$object_header_name = "Port Name";
}

if (($analyze_method =~ /Src/) || ($analyze_method =~ /Spt/)) { $object_action = "sent"; }
if (($analyze_method =~ /Dst/) || ($analyze_method =~ /Dpt/)) { $object_action = "received"; }
if ($analyze_method =~ /Peak/)  { $number_type = "Peak"; }
if ($analyze_method =~ /Total/) { $number_type = "Total"; }

if ($graph_type =~ "bps")  { $object_data = "bytes"; }
if ($graph_type =~ "pps")  { $object_data = "packets"; }
if ($graph_type =~ "fpsi") { $object_data = "flows"; }
if (($graph_type =~ "fpsa") && ($analyze_method =~ /Peak/))  { $object_data = "flows"; }
if (($graph_type =~ "fpsa") && ($analyze_method =~ /Total/)) { $object_data = "flow seconds"; }
if ($analyze_method =~ /Peak/)  { $output_total = $total_measured_peak; }
if ($analyze_method =~ /Total/) { $output_total = $total_measured_total; }

print "<table>\n";
print "<tr>\n";
print "<td><b>&nbsp&nbsp$object_header_id&nbsp&nbsp&nbsp&nbsp</b></td>\n";
print "<td><b>&nbsp&nbsp$object_header_name&nbsp&nbsp&nbsp&nbsp</b></td>\n";
if ($analyzing_hosts) {
	print "<td><b>&nbsp&nbspCountry&nbsp&nbsp&nbsp&nbsp</b></td>\n";
	print "<td><b>&nbsp&nbspAutonomous System&nbsp&nbsp&nbsp&nbsp</b></td>\n";
}
print "<td align=center><b>&nbsp&nbspAction&nbsp&nbsp&nbsp&nbsp</b></td>\n";
print "<td align=center><b>&nbsp&nbspNumber ($number_type)&nbsp&nbsp</b></td>\n";
print "<td align=center><b>&nbsp&nbspType&nbsp&nbsp&nbsp&nbsp</b></td>\n";
if (!($analyze_method =~ /Peak/)) { print "<td align=center><b>&nbsp&nbspPct&nbsp&nbsp&nbsp&nbsp</b></td>\n"; }
print "<tr><td>&nbsp</td></tr>\n";
foreach $output_object (@sorted_objects) {
	if (($output_object =~ "All Other") || ($output_object eq "")) { next; }
	$exclude_objects .= $output_object ."|";
	$output_object_name = $output_object;
	if (($output_object =~ /\./) || ($output_object =~ /:/)) { 
		$output_object_name = dig($output_object);
		($as_number,$as_country,$as_name) = dig_as_full($output_object);
		if ($as_name ne "") {
			$output_as_country = "$as_country";
			$output_as_name = "$as_name";
		} else {
			$output_as_country = " ";
			$output_as_name = "None Found";
		}
	} else {
		$port_type = "tcp"; if ($protocols == 17) { $port_type = "udp"; }
		$port_id = "$output_object:$port_type";
		$port_name = $port_names{$port_id};
		if ($port_name ne "") { $output_object_name = $port_names{$port_id}; }
		else { $output_object_name = "Not Mapped"; }
	}
	($output_amount,$output_color) = split(/:/,$output_values{$output_object});
	$output_pct = int((100 * ($output_amount / $output_total)) + 0.5);
	if ($graph_type =~ /bps/) { $output_amount = int($output_amount / 8); }
	$formatted_value = format_number($output_amount);
	$fg_analyze_link = "$cgi_bin_short/FlowGrapher_Main.cgi?$active_dashboard^$analyze_method^$output_object^$new_filter_hash";
	print "<td style=background-color:#$output_color><a href=$fg_analyze_link>&nbsp&nbsp$output_object&nbsp&nbsp&nbsp&nbsp</a></td>\n";
	print "<td style=background-color:#$output_color>&nbsp&nbsp$output_object_name&nbsp&nbsp&nbsp&nbsp</td>\n";
	if ($analyzing_hosts) {
		print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$output_as_country&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td style=background-color:#$output_color>&nbsp&nbsp$output_as_name&nbsp&nbsp&nbsp&nbsp</td>\n";
	}
	print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_action&nbsp&nbsp</td>\n";
	print "<td align=right style=background-color:#$output_color>&nbsp&nbsp$formatted_value&nbsp&nbsp</td>\n";
	print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_data&nbsp&nbsp</td>\n";
	if (!($analyze_method =~ /Peak/)) { print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$output_pct&nbsp&nbsp</td>\n"; }
	print "</tr>\n";
	$last_value = $formatted_value;
}
$output_object  = "All Others";
if ($analyzing_hosts) {
	$analyze_object = "AllOtherHosts" ."|". $exclude_objects;
} else {
	$analyze_object = "AllOtherPorts" ."|". $exclude_objects;
}
chop $analyze_object;
$output_object_name = "All Others";
($output_amount,$output_color) = split(/:/,$output_values{$output_object});
$output_pct = int((100 * ($output_amount / $output_total)) + 0.5);
if ($graph_type =~ /bps/) { $output_amount = int($output_amount / 8); }
$formatted_value = format_number($output_amount);
if ($analyze_method =~ /Peak/) { $formatted_value = "< " . $last_value; }
print "<tr><td>&nbsp</td></tr>\n";
$fg_analyze_link = "$cgi_bin_short/FlowGrapher_Main.cgi?$active_dashboard^$analyze_method^$analyze_object^$new_filter_hash";
print "<td style=background-color:#$output_color><a href=$fg_analyze_link>&nbsp&nbsp$output_object&nbsp&nbsp&nbsp&nbsp</a></td>\n";
print "<td style=background-color:#$output_color>&nbsp&nbsp$output_object_name&nbsp&nbsp&nbsp&nbsp</td>\n";
if ($analyzing_hosts) {
	print "<td style=background-color:#$output_color>&nbsp&nbsp   &nbsp&nbsp&nbsp&nbsp</td>\n";
	print "<td style=background-color:#$output_color>&nbsp&nbsp   &nbsp&nbsp&nbsp&nbsp</td>\n";
}
print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_action&nbsp&nbsp</td>\n";
print "<td align=right style=background-color:#$output_color>&nbsp&nbsp$formatted_value&nbsp&nbsp</td>\n";
print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_data&nbsp&nbsp</td>\n";
if (!($analyze_method =~ /Peak/)) { print "<td align=center style=background-color:#$output_color>&nbsp&nbsp$output_pct&nbsp&nbsp</td>\n"; }
print "</table>\n";
print "</div>\n";

# Print to Save file

print SAVE_ANALYSIS "<table>\n";
print SAVE_ANALYSIS "<tr>\n";
print SAVE_ANALYSIS "<td><b>&nbsp&nbsp$object_header_id&nbsp&nbsp&nbsp&nbsp</b></td>\n";
print SAVE_ANALYSIS "<td><b>&nbsp&nbsp$object_header_name&nbsp&nbsp&nbsp&nbsp</b></td>\n";
if ($analyzing_hosts) {
	print SAVE_ANALYSIS "<td><b>&nbsp&nbspCountry&nbsp&nbsp&nbsp&nbsp</b></td>\n";
	print SAVE_ANALYSIS "<td><b>&nbsp&nbspAutonomous System&nbsp&nbsp&nbsp&nbsp</b></td>\n";
}
print SAVE_ANALYSIS "<td align=center><b>&nbsp&nbspAction&nbsp&nbsp&nbsp&nbsp</b></td>\n";
print SAVE_ANALYSIS "<td align=center><b>&nbsp&nbspNumber ($number_type)&nbsp&nbsp</b></td>\n";
print SAVE_ANALYSIS "<td align=center><b>&nbsp&nbspType&nbsp&nbsp&nbsp&nbsp</b></td>\n";
if (!($analyze_method =~ /Peak/)) { print SAVE_ANALYSIS "<td align=center><b>&nbsp&nbspPct&nbsp&nbsp&nbsp&nbsp</b></td>\n"; }
print SAVE_ANALYSIS "<tr><td>&nbsp</td></tr>\n";
foreach $output_object (@sorted_objects) {
	if (($output_object =~ "All Other") || ($output_object eq "")) { next; }
	$exclude_objects .= $output_object ."|";
	$output_object_name = $output_object;
	if (($output_object =~ /\./) || ($output_object =~ /:/)) { 
		$output_object_name = dig($output_object);
		($as_number,$as_country,$as_name) = dig_as_full($output_object);
		if ($as_name ne "") {
			$output_as_country = "$as_country";
			$output_as_name = "$as_name";
		} else {
			$output_as_country = " ";
			$output_as_name = "None Found";
		}
	} else {
		$port_type = "tcp"; if ($protocols == 17) { $port_type = "udp"; }
		$port_id = "$output_object:$port_type";
		$port_name = $port_names{$port_id};
		if ($port_name ne "") { $output_object_name = $port_names{$port_id}; }
		else { $output_object_name = "Not Mapped"; }
	}
	($output_amount,$output_color) = split(/:/,$output_values{$output_object});
	$output_pct = int((100 * ($output_amount / $output_total)) + 0.5);
	if ($graph_type =~ /bps/) { $output_amount = int($output_amount / 8); }
	$formatted_value = format_number($output_amount);
	print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp$output_object&nbsp&nbsp&nbsp&nbsp</td>\n";
	print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp$output_object_name&nbsp&nbsp&nbsp&nbsp</td>\n";
	if ($analyzing_hosts) {
		print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$output_as_country&nbsp&nbsp&nbsp&nbsp</td>\n";
		print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp$output_as_name&nbsp&nbsp&nbsp&nbsp</td>\n";
	}
	print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_action&nbsp&nbsp</td>\n";
	print SAVE_ANALYSIS "<td align=right style=background-color:#$output_color>&nbsp&nbsp$formatted_value&nbsp&nbsp</td>\n";
	print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_data&nbsp&nbsp</td>\n";
	if (!($analyze_method =~ /Peak/)) { print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$output_pct&nbsp&nbsp</td>\n"; }
	print SAVE_ANALYSIS "</tr>\n";
	$last_value = $formatted_value;
}
$output_object  = "All Others";
if ($analyzing_hosts) {
	$analyze_object = "AllOtherHosts" ."|". $exclude_objects;
} else {
	$analyze_object = "AllOtherPorts" ."|". $exclude_objects;
}
chop $analyze_object;
$output_object_name = "All Others";
($output_amount,$output_color) = split(/:/,$output_values{$output_object});
$output_pct = int((100 * ($output_amount / $output_total)) + 0.5);
if ($graph_type =~ /bps/) { $output_amount = int($output_amount / 8); }
$formatted_value = format_number($output_amount);
if ($analyze_method =~ /Peak/) { $formatted_value = "< " . $last_value; }
print SAVE_ANALYSIS "<tr><td>&nbsp</td></tr>\n";
print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp$output_object&nbsp&nbsp&nbsp&nbsp</td>\n";
print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp$output_object_name&nbsp&nbsp&nbsp&nbsp</td>\n";
if ($analyzing_hosts) {
	print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp   &nbsp&nbsp&nbsp&nbsp</td>\n";
	print SAVE_ANALYSIS "<td style=background-color:#$output_color>&nbsp&nbsp   &nbsp&nbsp&nbsp&nbsp</td>\n";
}
print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_action&nbsp&nbsp</td>\n";
print SAVE_ANALYSIS "<td align=right style=background-color:#$output_color>&nbsp&nbsp$formatted_value&nbsp&nbsp</td>\n";
print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$object_data&nbsp&nbsp</td>\n";
if (!($analyze_method =~ /Peak/)) { print SAVE_ANALYSIS "<td align=center style=background-color:#$output_color>&nbsp&nbsp$output_pct&nbsp&nbsp</td>\n"; }
print SAVE_ANALYSIS "</table>\n";

close(SAVE_ANALYSIS);

print " <div id=service_bottom>\n";
print "  <span class=analyze_lead></span>\n";
print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_filter^$new_filter_hash\">\n";
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

&finish_the_page("FlowGrapher_Main");

# Remove temporary files

$rm_command = "/bin/rm $work_directory/FG_details_cfg_$suffix";
if ($debug_files ne "Y") { system($rm_command); }
$rm_command = "/bin/rm $work_directory/FG_buckets_cfg_$suffix";
if ($debug_files ne "Y") { system($rm_command); }
 
$run_end = time;
$run_time = $run_end - $run_start;
time_check("done");
if ($debug_grapher eq "Y") { print DEBUG "run took: $run_time seconds\n"; }

sub by_number { $a <=> $b; }

sub print_error {
	my ($error_text) = @_;
	print "<br><br><h4>        $error_text  </h4><br>";
	exit;
}

sub dig { 
        my ($host_address) = @_; 
     
        $host_name = $host_address; 
        if (defined($host_names{$host_address})) { 
                $host_name = $host_names{$host_address}; 
                $length_name = length($host_name); 
                if ($length_name > $dns_column_width) {  
                        $left_start = $length_name - $dns_column_width; 
                        $host_name = substr($host_name,$left_start,$dns_column_width); 
                }        
        } else {   
                open(DIG,"$dig $host_address 2>&1|"); 
                $answer_record = 0; 
                while (<DIG>) { 
                        chop;    
                        if (/ANSWER SECTION/) { 
                                $answer_record = 1; 
                                next;    
                        }        
                        if ($answer_record) { 
                                ($in_addr,$rec_timeout,$rec_direction,$rec_type,$host_name) = split(/\s+/,$_); 
                                $last_period = rindex($host_name,"\."); 
                                $host_name = substr($host_name,0,$last_period); 
                                $length_name = length($host_name); 
                                if ($length_name > $dns_column_width) {  
                                        $left_start = $length_name - $dns_column_width; 
                                        $host_name = substr($host_name,$left_start,$dns_column_width); 
                                }        
                                if (/CNAME/) { $host_name = $host_address; } 
                                last;    
                        }        
                }        
     
		if (length($host_name) < 1) { $host_name = $host_address; }
		$host_names{$host_address} = $host_name; 
        }        
	close DIG;
        return $host_name; 
}  

sub dig_as_full {

	my ($host_address) = @_;

	$as_number  = "";

	($a,$b,$c,$d) = split(/\./,$host_address);
	$reverse_address = $d .".". $c .".". $b .".". $a;

	open(DIG_AS,"dig +short $reverse_address.origin.asn.cymru.com TXT 2>&1|");
	while (<DIG_AS>) {
		chomp;
		if (/[0-9]+ | [A-Z]+ |.*/) {
			s/"//g;
			($as_number, $ip_range, $as_country, $as_rir, $as_date) = split(/ \| /, $_);
		}
	}
	close (DIG_AS);
	
	if ($as_number =~ / /) { ($as_number,$right_part) = split(/ /,$as_number); }
	$as_country = ""; $as_rir = ""; $as_date = ""; $as_name = "";

	open(DIG_AS,"dig +short AS$as_number.asn.cymru.com TXT 2>&1|");
	while (<DIG_AS>) {
		chomp;
		if (/[0-9]+ | [A-Z]+ |.*/) {
			s/"//g;
			($as_number, $as_country, $as_rir, $as_date, $as_name) = split(/ \| /, $_);
		}
	}
	close (DIG_AS);

	$as_name = substr($as_name,0,$asn_width);
	return ($as_number,$as_country,$as_name);
}
