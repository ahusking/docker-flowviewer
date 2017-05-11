#! /usr/bin/perl
#
#  Purpose:
#  FlowViewer_Main.cgi permits a Web user to analyze Net Flow data stored
#  in flow tools format and create an HTML report.
#
#  Description:
#  The script responds to an HTML form from the user in order to collect
#  parameters that will control the analysis (e.g., router, time-period, ip
#  addresses etc.) Upon receipt of the form input the script creates a flow tools
#  filter file which controls the selection of the data via the invocation of
#  additional flow tools utilities. An HTML report is then generated.
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
#  exporter             Constrain flows examined to specified exporter IP address
#  nexthop_ips          Constrain flows examined to specified Next Hop IP address
#  protocols            Constrain flows examined to these protocols 
#  print_report         Select from these various report options
#  stat_report          Select from these various statistics options
#  cutoff_lines         Number of report lines to print out
#  cutoff_octets        Minimum number of octets for inclusion in report
#  sort_field           Sorts on (Octets, Flows, Packets) for first report 
#  resolve_addresses    Whether or not to resolve IP addresses
#  unit_conversion      Whether or not to convert octets to GB, KB, etc.
#  sampling_multiplier  Value to multiply flow data (for sampled routers)
#  pie_charts           Generate pie charts; optional 'others' category
#
#  Notes:
#  1. It is a good idea to retain the host_names GDBM file (names), even if it 
#     gets large, since it is up to 1000 times faster than using 'dig'.
#  
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  07/04/2005      1.0     Original version.
#  J. Loiacono  01/01/2006      2.0     FlowGrapher, new functions, speed
#  J. Loiacono  01/16/2006      2.1     Fixed compute of concatenation date
#  J. Loiacono  01/26/2006      2.2     New flow_select option for inclusion
#  J. Loiacono  07/04/2006      3.0     Renamed for re-organization
#                                       Single script for GDBM/NDBM (thanks Ed Ravin)
#  J. Loiacono  12/25/2006      3.1     [No Change to this module]
#  J. Loiacono  02/14/2007      3.2     [No Change to this module]
#  J. Loiacono  12/07/2007      3.3     Sampling Multiplier, Pie Charts
#                                       AS resolving (thanks Sean Cardus)
#                                       Named IFs, Unit Conv. (thanks C. Kishimoto)
#  J. Loiacono  12/15/2007      3.3.1   New $no_devices ... parameter
#  J. Loiacono  03/17/2011      3.4     Support for change of device w/o reset
#                                       Support for meaningful Save report names
#                                       Concatenation now includes 'temp' files
#                                       Dynamic Resolved column width, flows/sec
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  04/15/2013      4.1     Removed extraneuos formatting
#  J. Loiacono  09/11/2013      4.2.1   Mods for international date formatting
#  J. Loiacono  01/26/2014      4.3     Introduced Detect Scanning
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards and flow analysis
#  J. Loiacono  11/02/2014      4.5     SiLK local timezone fixes
#                                       Cleaned up checking of entered times
#                                       Extended pie-charts to some Printed Reports
#                                       Use of $site_config_file on SiLK commands
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

if ($debug_viewer eq "Y") { open (DEBUG,">$work_directory/DEBUG_VIEWER"); }
if ($debug_viewer eq "Y") { print DEBUG "In FlowViewer_Main.cgi\n"; }

# Tie in the appropriate 'names' files which saves IP address resolved names

if (eval 'local $SIG{"__DIE__"}= sub { }; use GDBM_File; 
	tie %host_names, "GDBM_File", "$names_directory/names",    GDBM_WRCREAT, 0666;' ) { print DEBUG "Using GDBM\n"; };
if (eval 'local $SIG{"__DIE__"}= sub { }; use NDBM_File; use Fcntl; 
	tie %host_names, "GDBM_File", "$names_directory/names",    GDBM_WRCREAT, 0666;' ) { print DEBUG "Using NDBM\n"; };

# Tie in the appropriate 'as_names' file which saves resolved AS names

if (eval 'local $SIG{"__DIE__"}= sub { }; use GDBM_File; 
	tie %as_names,   "GDBM_File", "$names_directory/as_names", GDBM_WRCREAT, 0666;' ) { print DEBUG "Using GDBM\n"; };
if (eval 'local $SIG{"__DIE__"}= sub { }; use NDBM_File; use Fcntl; 
	tie %as_names,   "GDBM_File", "$names_directory/as_names", GDBM_WRCREAT, 0666;' ) { print DEBUG "Using NDBM\n"; };

if ((eval 'local $SIG{"__DIE__"}= sub { }; use GD; use GD::Graph::pie; use GD::Text') && ($pie_charts > 0)) { 
	if ($debug_viewer eq "Y") { print DEBUG "Using GD::Graph:Pie, etc.\n"; }
}

# Set up the Pie Chart colors

GD::Graph::colour::read_rgb("FlowGrapher_Colors") or die "cannot read colors";

# Retrieve the form inputs

read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
@pairs = split(/&/, $buffer);
foreach $pair (@pairs) {
    ($name, $value) = split(/=/, $pair);
    $value =~ tr/+/ /;
    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
    $FORM{$name} = $value;
}
 
# Clean up input 
      
($fv_link,$FORM{device_name}) = split(/DDD/,$FORM{device_name});
($fv_link,$FORM{exporter})    = split(/EEE/,$FORM{exporter});

if ($debug_viewer eq "Y") { print DEBUG "FORM{device_name}: $FORM{device_name}\n"; }
if ($debug_viewer eq "Y") { print DEBUG "FORM{exporter}: $FORM{exporter}\n"; }

$FORM{source_address} =~ s/\s+//g; $FORM{source_address} =~ s/,/, /g;   
$FORM{source_port}    =~ s/\s+//g; $FORM{source_port}    =~ s/,/, /g;   
$FORM{source_if}      =~ s/\s+//g; $FORM{source_if}      =~ s/,/, /g;   
$FORM{source_as}      =~ s/\s+//g; $FORM{source_as}      =~ s/,/, /g;   
$FORM{dest_address}   =~ s/\s+//g; $FORM{dest_address}   =~ s/,/, /g;   
$FORM{dest_port}      =~ s/\s+//g; $FORM{dest_port}      =~ s/,/, /g;   
$FORM{dest_if}        =~ s/\s+//g; $FORM{dest_if}        =~ s/,/, /g;   
$FORM{dest_as}        =~ s/\s+//g; $FORM{dest_as}        =~ s/,/, /g;   
$FORM{protocols}      =~ s/\s+//g; $FORM{protocols}      =~ s/,/, /g;   
$FORM{tos_fields}     =~ s/\s+//g; $FORM{tos_fields}     =~ s/,/, /g;   
$FORM{tcp_flags}      =~ s/\s+//g; $FORM{tcp_flags}      =~ s/,/, /g;
$FORM{nexthop_ip}     =~ s/\s+//g; $FORM{nexthop_ip}     =~ s/,/, /g;
$FORM{sif_name}       =~ s/,/, /g;   
$FORM{dif_name}       =~ s/,/, /g;   

# Parameters for generating a FlowViewer report

$active_dashboard    = $FORM{'active_dashboard'};
$device_name         = $FORM{'device_name'};
$flow_select         = $FORM{'flow_select'};
$start_date          = $FORM{'start_date'};
$start_time          = $FORM{'start_time'};
$end_date            = $FORM{'end_date'};
$end_time            = $FORM{'end_time'};
$source_addresses    = $FORM{'source_address'};
$source_ports        = $FORM{'source_port'};
$source_ifs          = $FORM{'source_if'};
$sif_names           = $FORM{'sif_name'};
$source_ases         = $FORM{'source_as'};
$dest_addresses      = $FORM{'dest_address'};
$dest_ports          = $FORM{'dest_port'};
$dest_ifs            = $FORM{'dest_if'};
$dif_names           = $FORM{'dif_name'};
$dest_ases           = $FORM{'dest_as'};
$protocols           = $FORM{'protocols'};
$tcp_flags           = $FORM{'tcp_flags'};
$tos_fields          = $FORM{'tos_fields'};
$exporter            = $FORM{'exporter'};
$nexthop_ips         = $FORM{'nexthop_ip'};
$print_report        = $FORM{'print_report'};
$stat_report         = $FORM{'stat_report'};
$cutoff_lines        = $FORM{'cutoff_lines'};
$cutoff_octets       = $FORM{'cutoff_octets'};
$sort_field          = $FORM{'sort_field'};
$resolve_addresses   = $FORM{'resolve_addresses'};
$unit_conversion     = $FORM{'unit_conversion'};
$sampling_multiplier = $FORM{'sampling_multiplier'};
$pie_charts          = $FORM{'pie_charts'};
$flow_analysis       = $FORM{'flow_analysis'};
$silk_rootdir        = $FORM{'silk_rootdir'};
$silk_class          = $FORM{'silk_class'};
$silk_flowtype       = $FORM{'silk_flowtype'};
$silk_type           = $FORM{'silk_type'};
$silk_sensors        = $FORM{'silk_sensors'};
$silk_switches       = $FORM{'silk_switches'};

if ($site_config_file ne "") { $site_config_modifier = "--site-config-file=$site_config_file "; }

# Convert into US date format for internal processing

if ($date_format eq "DMY") {
        ($temp_day_s,$temp_mnth_s,$temp_yr_s) = split(/\//,$start_date);
        ($temp_day_e,$temp_mnth_e,$temp_yr_e) = split(/\//,$end_date);
} elsif ($date_format eq "DMY2") {
        ($temp_day_s,$temp_mnth_s,$temp_yr_s) = split(/\./,$start_date);
        ($temp_day_e,$temp_mnth_e,$temp_yr_e) = split(/\./,$end_date);
} elsif ($date_format eq "YMD") {
        ($temp_yr_s,$temp_mnth_s,$temp_day_s) = split(/\-/,$start_date);
        ($temp_yr_e,$temp_mnth_e,$temp_day_e) = split(/\-/,$end_date);
} else {
        ($temp_mnth_s,$temp_day_s,$temp_yr_s) = split(/\//,$start_date);
        ($temp_mnth_e,$temp_day_e,$temp_yr_e) = split(/\//,$end_date);
}
$start_date = $temp_mnth_s ."/". $temp_day_s ."/". $temp_yr_s;
$end_date   = $temp_mnth_e ."/". $temp_day_e ."/". $temp_yr_e;

if ($debug_viewer eq "Y") { print DEBUG "FORM{start_date}: $FORM{start_date}  start_date: $start_date  FORM{end_date}: $FORM{end_date}  end_date: $end_date\n"; }

# Determine if we are looking at an IPFIX device

$IPFIX = 0;
foreach $ipfix_device (@ipfix_devices) {
        if ($device_name eq $ipfix_device) { $IPFIX = 1; if ($debug_viewer eq "Y") { print DEBUG "This device is exporting IPFIX\n";} }
}

# Start up the Saved file

$saved_suffix = &get_suffix;
$saved_hash   = "FlowViewer_save_$saved_suffix";
$filter_hash  = "FV_$saved_hash";
$saved_html   = "$work_directory/$saved_hash";
&start_saved_file($saved_html);

# Start the FlowViewer Report web page output

&create_UI_top($active_dashboard);
&create_UI_service("FlowViewer_Main","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";
print " <span class=text16>FlowViewer Report from $device_name</span>\n";
&create_filter_output("FlowViewer_Main",$filter_hash);

open(DATE,"date 2>&1|");
while (<DATE>) {
	($d_tz,$m_tz,$dt_tz,$t_tz,$time_zone,$y_tz) = split(/\s+/,$_);
}
$system_time = "UTC";
if (($time_zone ne "UTC") && ($time_zone ne "GMT") && ($time_zone ne "")) { $system_time = "NON-UTC"; }
if ($debug_grapher eq "Y") { print DEBUG "System timezone: $time_zone   system_time type: $system_time\n"; }

# Check dates and times for input errors

($mn,$da,$yr) = split(/\//,$start_date);
if ( $mn=~/\D/ || $da=~/\D/ || $yr=~/\D/ ) { &print_error("Bad date format: $FORM{start_date}"); };
if ( $mn<1 || $mn>12 || $da<1 || $da>31 || $yr<1990 || $yr>2100 ) { &print_error("Bad date format: $FORM{start_date}"); }
if (length($mn) < 2) { $mn = "0" . $mn; }
if (length($da) < 2) { $da = "0" . $da; }
$start_ymd = $yr . $mn . $da;
$start_yr = $yr; $start_mn = $mn; $start_da = $da;

($hr,$mi,$sc) = split(/:/,$start_time);
if ( $hr=~/\D/ || $mi=~/\D/ || $sc=~/\D/ ) { &print_error("Bad time format: $FORM{start_time}"); };
if (length($hr)>2 || $hr>23 || length($mi)>2 || $mi>59 || length($sc)>2 || $sc>59 ) { &print_error("Bad time format: $FORM{start_time}"); }

($mn,$da,$yr) = split(/\//,$end_date);
if ( $mn=~/\D/ || $da=~/\D/ || $yr=~/\D/ ) { &print_error("Bad date format: $FORM{end_date}"); };
if ( $mn<1 || $mn>12 || $da<1 || $da>31 || $yr<1990 || $yr>2100 ) { &print_error("Bad date format: $FORM{end_date}"); }
if (length($mn) < 2) { $mn = "0" . $mn; }
if (length($da) < 2) { $da = "0" . $da; }
$end_ymd = $yr . $mn . $da;
$end_yr = $yr; $end_mn = $mn; $end_da = $da;

($hr,$mi,$sc) = split(/:/,$end_time);
if ( $hr=~/\D/ || $mi=~/\D/ || $sc=~/\D/ ) { &print_error("Bad time format: $FORM{end_time}"); };
if (length($hr)>2 || $hr>23 || length($mi)>2 || $mi>59 || length($sc)>2 || $sc>59 ) { &print_error("Bad time format: $FORM{end_time}"); }

if (($no_devices_or_exporters eq "N") && (($device_name eq "") && ($exporter eq ""))) {
        print "<br><b>Must select a device or an exporter. <p>Use the \"back\" key to save inputs</b><br>";
        exit;
}
 
if (($stat_report == 0) && ($print_report == 0)) { &print_error("Must specify a report."); }
if (($stat_report != 0) && ($print_report != 0)) { &print_error("Two reports selected. Please reset one."); }
 
if (($stat_report == 10) && ($print_report ne "0")) {
	$stat_report = 0;
}

# Retrieve current time to use as a file suffix to permit more than one user to generate reports

($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime(time);
$mnth++;
$yr += 1900;
if ((0 < $mnth) && ($mnth < 10)) { $mnth = "0" . $mnth; }
if ((0 < $date) && ($date < 10)) { $date = "0" . $date; }
if ((0 <= $hr)  && ($hr  < 10)) { $hr  = "0" . $hr; }
if ((0 <= $min) && ($min < 10)) { $min = "0" . $min; }
if ((0 <= $sec) && ($sec < 10)) { $sec = "0" . $sec; }
$prefix = $yr . $mnth . $date ."_". $hr . $min . $sec;
$suffix = $hr . $min . $sec;

if ($IPFIX) {

	# Obtain user requested start time in SiLK-storage time zone

	($temp_hr_s,$temp_min_s,$temp_sec_s) = split(/:/,$start_time);
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

	# Obtain user requested end time in SiLK-storage time zone

	($temp_hr_e,$temp_min_e,$temp_sec_e) = split(/:/,$end_time);
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

	# Determine flow-tools concatenation start and end times
	
	$start_epoch     = date_to_epoch($start_date,$start_time,"LOCAL");
	$end_epoch       = date_to_epoch($end_date,$end_time,"LOCAL");
	
	$start_flows     = &flow_date_time($start_epoch,"LOCAL");
	$end_flows       = &flow_date_time($end_epoch,"LOCAL");
		
	$cat_start_epoch = $start_epoch - $flow_file_length - 1;
	$cat_end_epoch   = $end_epoch   + $flow_capture_interval + 1;
	$cat_start       = epoch_to_date($cat_start_epoch,"LOCAL");
	$cat_end         = epoch_to_date($cat_end_epoch,"LOCAL");
	
	$concatenate_parameters = "-a -t \"$cat_start\" -T \"$cat_end\" "; 
}

$report_length = $end_epoch - $start_epoch;
if ($report_length <= 0) { &print_error("End time ($end_date $end_time) earlier than Start time ($start_date $start_time)"); } 
	
if (!$IPFIX) {

	if (($start_ymd ne $end_ymd) && ($end_epoch > $start_epoch)) {
	        for ($i=0;$i<$maximum_days;$i++) {
	                if (($cat_start_epoch + $i*86400) > $cat_end_epoch + 86400) { last; }
	                ($sec,$min,$hr,$cat_date,$cat_mnth,$cat_yr,$day,$yr_date,$DST) = localtime($cat_start_epoch + $i*86400);
	                $cat_mnth++;
	                $cat_yr += 1900;
	                if ((0 < $cat_mnth) && ($cat_mnth < 10)) { $cat_mnth = "0" . $cat_mnth; }
	                if ((0 < $cat_date) && ($cat_date < 10)) { $cat_date = "0" . $cat_date; }
	
			if ($exporter ne "") {
	                	$cat_directory = "$exporter_directory";
			} else {
	                	$cat_directory = "$flow_data_directory/$device_name";
			}
	
			if ($N == -3) { $cat_directory .= "/$cat_yr/$cat_yr\-$cat_mnth/$cat_yr\-$cat_mnth\-$cat_date"; }
			if ($N == -2) { $cat_directory .= "/$cat_yr\-$cat_mnth/$cat_yr\-$cat_mnth\-$cat_date"; }
			if ($N == -1) { $cat_directory .= "/$cat_yr\-$cat_mnth\-$cat_date"; }
			if ($N == 1)  { $cat_directory .= "/$cat_yr"; }
			if ($N == 2)  { $cat_directory .= "/$cat_yr/$cat_yr\-$cat_mnth"; }
			if ($N == 3)  { $cat_directory .= "/$cat_yr/$cat_yr\-$cat_mnth/$cat_yr\-$cat_mnth\-$cat_date"; }
	
                        if (-e $cat_directory) { $concatenate_parameters .= "$cat_directory "; }
	
			if ($N == 0)  { last; }
	        }        

	} elsif ($start_ymd eq $end_ymd) { 
	     
	        ($sec,$min,$hr,$cat_date,$cat_mnth,$cat_yr,$day,$yr_date,$DST) = localtime($cat_end_epoch); 
	        $cat_mnth++; 
	        $cat_yr += 1900; 
	        if ((0 < $cat_mnth) && ($cat_mnth < 10)) { $cat_mnth = "0" . $cat_mnth; } 
	        if ((0 < $cat_date) && ($cat_date < 10)) { $cat_date = "0" . $cat_date; } 
	
		if ($exporter ne "") {
	               	$cat_directory = "$exporter_directory";
		} else {
	               	$cat_directory = "$flow_data_directory/$device_name";
		}
	
		if ($N == -3) { $cat_directory .= "/$cat_yr/$cat_yr\-$cat_mnth/$cat_yr\-$cat_mnth\-$cat_date"; }
		if ($N == -2) { $cat_directory .= "/$cat_yr\-$cat_mnth/$cat_yr\-$cat_mnth\-$cat_date"; }
		if ($N == -1) { $cat_directory .= "/$cat_yr\-$cat_mnth\-$cat_date"; }
		if ($N == 1)  { $cat_directory .= "/$cat_yr"; }
		if ($N == 2)  { $cat_directory .= "/$cat_yr/$cat_yr\-$cat_mnth"; }
		if ($N == 3)  { $cat_directory .= "/$cat_yr/$cat_yr\-$cat_mnth/$cat_yr\-$cat_mnth\-$cat_date"; }
	
	        $concatenate_parameters .= "$cat_directory "; 
	}
	else {
	        &print_error("Start day ($start_date) is past End day ($end_date)");
	}
	
	# Create the filter to match the input specifications
	
	$filter_file = "$work_directory/FlowViewer_filter_$suffix";
	
	create_filter_file(%FORM,$filter_file);
	
	# Set up the command to concatenate the files
	 
	$flowcat_command = "$flow_bin_directory/flow-cat" . " $concatenate_parameters";
	 
	# Set up the command to filter the concatenated file
	 
	$flownfilter_command = "$flow_bin_directory/flow-nfilter -f $work_directory/FlowViewer_filter_$suffix -FFlow_Filter";
	     
	# Set up the flow-stat command if requested
	 
	if ($stat_report ne "0") {
		if ($rate_report) {
			if ($sort_field == 1) { $ft_sort_field = 3; }
			if ($sort_field == 2) { $ft_sort_field = 2; }
			if ($sort_field == 3) { $ft_sort_field = 4; }
		} else {
			if ($sort_field == 1) { $ft_sort_field = 2; }
			if ($sort_field == 2) { $ft_sort_field = 1; }
			if ($sort_field == 3) { $ft_sort_field = 3; }
		}
		if ($stat_report eq "99") {
	        	$flowstat_command = "$flow_bin_directory/flow-stat -S$ft_sort_field >$work_directory/FlowViewer_output_$suffix";
	        	$flow_run = "$flowcat_command | $flownfilter_command | $flowstat_command 2>>$work_directory/FlowViewer_output_$suffix";
		} elsif ($stat_report == 30) {
			if (($source_ifs ne "") || ($sif_names ne "")) { $in_int_list  = "-i" . $source_ifs . $sif_names; } else {  $in_int_list = ""; }
			if (($dest_ifs   ne "") || ($dif_names ne "")) { $out_int_list = "-I" . $dest_ifs   . $dif_names; } else { $out_int_list = ""; }
			$suppress_list = "$cgi_bin_directory/dscan.suppress";
			$touch_command = "touch $suppress_list.src $suppress_list.dst";
			system($touch_command);
			$flow_prefilter = "$flowcat_command | $flownfilter_command > $work_directory/FlowViewer_scanner_$suffix";
			system($flow_prefilter);
			$flow_run = "$flow_bin_directory/flow-dscan $in_int_list $out_int_list -L$suppress_list -b $dscan_parameters < $work_directory/FlowViewer_scanner_$suffix >&$work_directory/FlowViewer_output_$suffix";
		} else {
	        	$flowstat_command = "$flow_bin_directory/flow-stat -f$stat_report -S$ft_sort_field >$work_directory/FlowViewer_output_$suffix";
	        	$flow_run = "$flowcat_command | $flownfilter_command | $flowstat_command 2>>$work_directory/FlowViewer_output_$suffix";
		}
	}
	 
	# Set up the flow-print command if requested
	 
	if ($print_report ne "0") {
	        $flowprint_command = "$flow_bin_directory/flow-print -f$print_report >$work_directory/FlowViewer_output_$suffix";
	        $flow_run = "$flowcat_command | $flownfilter_command | $flowprint_command 2>>$work_directory/FlowViewer_output_$suffix";
	}
	 
	# Execute the piped flow-tools command
	 
	if ($debug_viewer eq "Y") { print DEBUG "\n$flow_run\n\n"; }
	
	system ($flow_run);

} else {

	$silk_cat_start = $start_epoch - $silk_capture_buffer_pre;
	$silk_cat_end   = $end_epoch   + $silk_capture_buffer_post;

	if ($silk_compiled_localtime eq "Y") {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($silk_cat_start);
	} else {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = gmtime($silk_cat_start);
	}
	$yr += 1900;
	$mnth++;
	if (length($mnth) < 2) { $mnth = "0" . $mnth; }
	if (length($date) < 2) { $date = "0" . $date; }
	if (length($hr)   < 2) { $hr   = "0" . $hr; }
	$silk_cat_start    = $yr ."/". $mnth ."/". $date .":". $hr;
	
	if ($silk_compiled_localtime eq "Y") {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($silk_cat_end);
	} else {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = gmtime($silk_cat_end);
	}
	$yr += 1900;
	$mnth++;
	if (length($mnth) < 2) { $mnth = "0" . $mnth; }
	if (length($date) < 2) { $date = "0" . $date; }
	if (length($hr)   < 2) { $hr   = "0" . $hr; }
	$silk_cat_end = $yr ."/". $mnth ."/". $date .":". $hr;

	# Set up SiLK selection

	$selection_switches = "";
	if ($silk_rootdir ne "")   { $selection_switches  = "--data-rootdir=$silk_rootdir "; }
	if ($silk_class ne "")     { $selection_switches .= "--class=$silk_class "; }
	if ($silk_flowtype ne "")  { $selection_switches .= "--flowtype=$silk_flowtype "; }
	if ($silk_type ne "")      { $selection_switches .= "--type=$silk_type "; }
	if ($silk_sensors ne "")   { $selection_switches .= "--sensors=$silk_sensors "; }
	if ($silk_switches ne "")  { $selection_switches .= "$silk_switches "; }

	$silk_info_out = $selection_switches;

        # Prepare rwfilter start and end time parameters

        $time_window = $silk_period_start ."-". $silk_period_end;

	if ($flow_select eq 1) { $window_type = "--active"; }
	if ($flow_select eq 2) { $window_type = "--etime"; }
	if ($flow_select eq 3) { $window_type = "--stime"; }
	if ($flow_select eq 4) { $window_type = "--stime"; }

	$selection_switches .= "--start-date=$silk_cat_start --end-date=$silk_cat_end $window_type=$time_window ";

        # Prepare source and destination IP address parameters

        create_ipfix_filter(%FORM);

        # Prepare rwfilter command

	if ($debug_viewer eq "Y") { print DEBUG "   selection_switches: $selection_switches\n"; }
	if ($debug_viewer eq "Y") { print DEBUG "partitioning_switches:$partitioning_switches\n"; }

	$rwfilter_command = "$silk_bin_directory/rwfilter $site_config_modifier $selection_switches $partitioning_switches --pass=stdout";

	if ($print_report == 1) { $rwfilter_command .= " | $silk_bin_directory/rwsort $site_config_modifier --fields=9 "; }

        # Prepare rwstats output fields (this set is similar to flow-tools)

	$column_separator = " ";

	if ($stat_report == 99) { $report_title = "Summary"; }
	if ($stat_report == 5)  { $field_sequence = "4"; }
	if ($stat_report == 6)  { $field_sequence = "3"; }
	if ($stat_report == 7)  { $field_sequence = "3,4"; }
	if ($stat_report == 8)  { $field_sequence = "2"; }
	if ($stat_report == 9)  { $field_sequence = "1"; }
	if ($stat_report == 10) { $field_sequence = "1,2"; }
	if ($stat_report == 11) { $report_title = "Source or Destination IP";  $heading_1 = "Host"; }
	if ($stat_report == 12) { $field_sequence = "5"; }
	if ($stat_report == 17) { $field_sequence = "13"; }
	if ($stat_report == 18) { $field_sequence = "14"; }
	if ($stat_report == 19) { &print_error("The Source AS Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($stat_report == 20) { &print_error("The Destination AS Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($stat_report == 21) { &print_error("The Source/Destination AS Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($stat_report == 22) { &print_error("The IP ToS Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($stat_report == 23) { $field_sequence = "13,14"; }
	if ($stat_report == 24) { &print_error("The Statistics Source Prefix Report is not available for IPFIX data. Please use the Source Prefix Aggregation Printed Report."); }
	if ($stat_report == 25) { &print_error("The Statistics Destination Prefix Report is not available for IPFIX data. Please use the Destination Prefix Aggregation Printed Report."); }
	if ($stat_report == 26) { &print_error("The Statistics Source/Destination Prefix Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($stat_report == 27) { &print_error("The Exporter IP Report is not available for IPFIX data."); }
	if ($stat_report == 30) { $report_title = "Detect Scanning"; }

	if ($print_report == 1)  { $field_sequence = "22,24,23,13,1,14,2,5,3,4,6,7,8"; }
	if ($print_report == 4)  { &print_error("The AS Numbers Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($print_report == 5)  { $field_sequence = "22,24,23,13,1,3,14,2,4,15,5,6,7,8"; }
	if ($print_report == 9)  { &print_error("The 1 Line with Tags Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($print_report == 10) { &print_error("The AS Aggregation Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($print_report == 11) { &print_error("The Protocol Port Aggregation Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($print_report == 12) { $field_sequence = "1"; }
	if ($print_report == 13) { $field_sequence = "2"; }
	if ($print_report == 14) { &print_error("The Prefix Aggregation report is not available for IPFIX data. The capability is not currently supported by SiLK."); }
	if ($print_report == 15) { $field_sequence = "1"; }
	if ($print_report == 16) { $field_sequence = "2"; }
	if ($print_report == 17) { $field_sequence = "1,2"; }
	if ($print_report == 24) { &print_error("The Full Catalyst Report is not available for IPFIX data. The capability is not currently supported by SiLK."); }

	if ($sort_field == 1) { $rwstat_values = "Bytes,Packets,Records"; }
	if ($sort_field == 2) { $rwstat_values = "Records,Bytes,Packets"; }
	if ($sort_field == 3) { $rwstat_values = "Packets,Bytes,Records"; }

	time_check("start SiLK");

	if ($stat_report == 11) {

		$half_cutoff_lines  = int(0.5 * $cutoff_lines);

		$field_sequence = "1";
        	$rwstats_command = "$silk_bin_directory/rwstats $site_config_modifier --fields=$field_sequence --values=$rwstat_values --no-titles --no-percents --delimited=\"  \" ";
		if ($cutoff_octets > 0) { 
			$rwstats_command .= "--threshold=$cutoff_octets";
		} else {
			$rwstats_command .= "--count=$half_cutoff_lines";
		}
        	$silk_command = "$rwfilter_command | $rwstats_command > $work_directory/FlowViewer_output_$suffix";
		if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

		$field_sequence = "2";
        	$rwstats_command = "$silk_bin_directory/rwstats $site_config_modifier --fields=$field_sequence --values=$rwstat_values --no-titles --no-percents --delimited=\"  \" ";
		if ($cutoff_octets > 0) { 
			$rwstats_command .= "--threshold=$cutoff_octets";
		} else {
			$rwstats_command .= "--count=$half_cutoff_lines";
		}
        	$silk_command = "$rwfilter_command | $rwstats_command >> $work_directory/FlowViewer_output_$suffix";
		if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

		$temp_sort_file = "$work_directory/FlowViewer_output_$suffix";
		open(TEMPSORT,"<$temp_sort_file");
		chomp (@temp_sort_lines = <TEMPSORT>);
		close TEMPSORT;
		foreach $temp_sort_line (@temp_sort_lines) {
			($ip_addr,$octs,$pkts,$flws) = split(/\s+/,$temp_sort_line);
			$num_zeroes = 20 - length($octs);
			for ($i=0;$i<$num_zeroes;$i++) { $octs = "0" . $octs; }
			$new_sort_line = $octs ." ". $ip_addr ." ". $pkts ." ". $flws;
			push(@new_sort_lines,$new_sort_line);
		}

		@pre_sorted_lines = sort (@new_sort_lines);
		@newly_sorted_lines = reverse(@pre_sorted_lines);
		open(TEMPSORT,">$temp_sort_file");
		foreach $temp_sort_line (@newly_sorted_lines) {
			($octs,$ip_addr,$pkts,$flws) = split(/\s+/,$temp_sort_line);
			for ($i=0;$i<20;$i++) { if (substr($octs,0,1) eq "0") { $octs = substr($octs,1,20); } }
			$sorted_output_line = $ip_addr ." ". $octs ." ". $pkts ." ". $flws;
			print TEMPSORT "$sorted_output_line\n";
		}
		close TEMPSORT;

	} elsif ($stat_report == 30) {

		$prefiltered_file = "$work_directory/FlowViewer_scanner_$suffix";
		($left_part,$right_part) = split(/--pass=/,$rwfilter_command);
		$rwfilter_command = $left_part . "--pass=$prefiltered_file";
        	if ($debug_viewer eq "Y") { print DEBUG "rwfilter_command: $rwfilter_command\n"; }
        	system ($rwfilter_command);
		$rwsort_command = "$silk_bin_directory/rwsort $site_config_modifier --fields=sip,proto,dip $prefiltered_file"; 
		$rwscan_command = "$silk_bin_directory/rwscan $site_config_modifier --scan-model=$scan_model --trw-internal-set=$trw_internal_set --model-fields"; 
        	$silk_command = "$rwsort_command | $rwscan_command > $work_directory/FlowViewer_output_$suffix";
        	if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

	} elsif ($stat_report == 99) {

		$field_sequence = "5";
        	$rwstats_command = "$silk_bin_directory/rwstats $site_config_modifier --fields=$field_sequence --values=$rwstat_values --count=1000 --no-titles --no-percents --delimited=\"  \" ";
        	$silk_command = "$rwfilter_command | $rwstats_command > $work_directory/FlowViewer_summary_$suffix";
		if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

		open (SUMMARY,"<$work_directory/FlowViewer_summary_$suffix");
		while (<SUMMARY>) {
			if (substr($_,0,1) eq "#") { next; }
			($x,$flows,$octets,$packets) = split(/\s+/,$_);
			$sum_field_sequence .= "$x,";
		}

		chop $sum_field_sequence;
        	$rwstats_command = "$silk_bin_directory/rwstats $site_config_modifier --detail-proto-stats=$sum_field_sequence";
        	$silk_command = "$rwfilter_command | $rwstats_command > $work_directory/FlowViewer_output_$suffix";
        	if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

	} elsif (($print_report == 1) || ($print_report == 5)) {

		$sort_field = 5;
        	$rwcut_command = "$silk_bin_directory/rwcut $site_config_modifier --fields=$field_sequence --column-separator=\"  \"";
		if ($cutoff_lines > 0) { $rwcut_command .= "--num-recs=$cutoff_lines"; }
        	$silk_command = "$rwfilter_command | $rwcut_command > $work_directory/FlowViewer_output_$suffix";
        	if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

	} elsif (($print_report >= 12) && ($print_report <= 17)) {

		if ($print_report == 12) { $rwnetmask_command = "$silk_bin_directory/rwnetmask $site_config_modifier --sip-prefix-length  $sip_prefix_length"; }
		if ($print_report == 13) { $rwnetmask_command = "$silk_bin_directory/rwnetmask $site_config_modifier --dip-prefix-length  $dip_prefix_length"; }
		if ($print_report == 15) { $rwnetmask_command = "$silk_bin_directory/rwnetmask $site_config_modifier --6sip-prefix-length $sip_prefix_length --ipv6-policy=only"; }
		if ($print_report == 16) { $rwnetmask_command = "$silk_bin_directory/rwnetmask $site_config_modifier --6dip-prefix-length $dip_prefix_length --ipv6-policy=only"; }
		if ($print_report == 17) { $rwnetmask_command = "$silk_bin_directory/rwnetmask $site_config_modifier --6sip-prefix-length $sip_prefix_length --6dip-prefix-length $dip_prefix_length --ipv6-policy=only"; }

        	$rwstats_command = "$silk_bin_directory/rwstats $site_config_modifier --fields=$field_sequence --values=$rwstat_values --no-titles --no-percents --delimited=\"  \" ";
		if ($cutoff_octets > 0) { 
			$rwstats_command .= "--threshold=$cutoff_octets";
		} else {
			$rwstats_command .= "--count=$cutoff_lines";
		}
        	$silk_command = "$rwfilter_command | $rwnetmask_command | $rwstats_command > $work_directory/FlowViewer_output_$suffix";
        	if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

	} else {

        	$rwstats_command = "$silk_bin_directory/rwstats $site_config_modifier --fields=$field_sequence --values=$rwstat_values --no-titles --no-percents --delimited=\"  \" ";
		if ($cutoff_octets > 0) { 
			$rwstats_command .= "--threshold=$cutoff_octets";
		} else {
			$rwstats_command .= "--count=$cutoff_lines";
		}
        	$silk_command = "$rwfilter_command | $rwstats_command > $work_directory/FlowViewer_output_$suffix";
        	if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);
	}
	time_check("end SiLK");
}

$heading_1 = ""; $heading_2 = "";

if ($stat_report == 99) { $report_title = "Summary"; }
if ($stat_report == 5)  { $report_title = "UDP/TCP Destination Port";  $heading_1 = "Dst Port"; }
if ($stat_report == 6)  { $report_title = "UDP/TCP Source Port";       $heading_1 = "Src Port"; }
if ($stat_report == 7)  { $report_title = "UDP/TCP Port";              $heading_1 = "Port"; }
if (($stat_report == 7) && ($IPFIX)) {                                 $heading_1 = "Src Port"; $heading_2 = "Dst Port";}
if ($stat_report == 8)  { $report_title = "Destination IP";            $heading_1 = "Dst Host"; }
if ($stat_report == 9)  { $report_title = "Source IP";                 $heading_1 = "Src Host"; }
if ($stat_report == 10) { $report_title = "Source/Destination IP";     $heading_1 = "Src Host"; $heading_2 = "Dst Host"; $rate_report = 1;}
if ($stat_report == 11) { $report_title = "Source or Destination IP";  $heading_1 = "Host"; }
if ($stat_report == 12) { $report_title = "IP Protocol";               $heading_1 = "Protocol"; }
if ($stat_report == 17) { $report_title = "Input Interface";           $heading_1 = "In I/F"; }
if ($stat_report == 18) { $report_title = "Output Interface";          $heading_1 = "Out I/F"; }
if ($stat_report == 19) { $report_title = "Source AS";                 $heading_1 = "Src AS"; }
if ($stat_report == 20) { $report_title = "Destination AS";            $heading_1 = "Dst AS"; }
if ($stat_report == 21) { $report_title = "Source/Destination AS";     $heading_1 = "Src AS"; $heading_2 = "Dst AS"; $rate_report = 1;}
if ($stat_report == 22) { $report_title = "IP ToS";                    $heading_1 = "ToS"; }
if ($stat_report == 23) { $report_title = "Input/Output Interface";    $heading_1 = "In I/F"; $heading_2 = "Out I/F"; $rate_report = 1;}
if ($stat_report == 24) { $report_title = "Source Prefix";             $heading_1 = "Src Prefix"; }
if ($stat_report == 25) { $report_title = "Destination Prefix";        $heading_1 = "Dst Prefix"; }
if ($stat_report == 26) { $report_title = "Source/Destination Prefix"; $heading_1 = "Src Prefix"; $heading_2 = "Dst Prefix"; $rate_report = 1;}
if ($stat_report == 27) { $report_title = "Exporter IP";               $heading_1 = "Exporter"; }
if ($stat_report == 30) { $report_title = "Detect Scanning";           $heading_1 = "Detect Scanning"; }

$resolve_columns = 0;
if (($resolve_addresses eq "Y") && ($stat_report == 8))  { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 9))  { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 10)) { $resolve_columns = 2; }
if (($resolve_addresses eq "Y") && ($stat_report == 11)) { $resolve_columns = 1; }
if (($resolve_addresses eq "Y") && ($stat_report == 17)) { $resolve_columns = 5; } 
if (($resolve_addresses eq "Y") && ($stat_report == 18)) { $resolve_columns = 5; } 
if (($resolve_addresses eq "Y") && ($stat_report == 19)) { $resolve_columns = 3; } 
if (($resolve_addresses eq "Y") && ($stat_report == 20)) { $resolve_columns = 3; } 
if (($resolve_addresses eq "Y") && ($stat_report == 21)) { $resolve_columns = 4; }
if (($resolve_addresses eq "Y") && ($stat_report == 23)) { $resolve_columns = 6; }
if (($resolve_addresses eq "Y") && ($stat_report == 27)) { $resolve_columns = 7; }

if ($print_report == 1)  { $report_title = "Flow Times"; }
if ($print_report == 4)  { $report_title = "AS Numbers"; }
if ($print_report == 5)  { $report_title = "132 Columns"; }
if ($print_report == 9)  { $report_title = "1 Line with Tags"; }
if ($print_report == 10) { $report_title = "AS Aggregation"; }
if ($print_report == 11) { $report_title = "Protocol Port Aggregation"; }
if ($print_report == 12) { $report_title = "Source Prefix Aggregation";      if ($IPFIX) { $heading_1 = "Source Prefix"; }}
if ($print_report == 13) { $report_title = "Destination Prefix Aggregation"; if ($IPFIX) { $heading_1 = "Dest Prefix"; }}
if ($print_report == 14) { $report_title = "Prefix Aggregation"; $heading_1 = "Source Aggregate"; $heading_2 = "Dest Aggregate"; }
if ($print_report == 15) { $report_title = "Source Prefix Aggregation v6";      $heading_1 = "Source Prefix"; }
if ($print_report == 16) { $report_title = "Destination Prefix Aggregation v6"; $heading_1 = "Dest Prefix"; }
if ($print_report == 17) { $report_title = "Prefix Aggregation v6"; $heading_1 = "Source Aggregate"; $heading_2 = "Dest Aggregate"; }
if ($print_report == 24) { $report_title = "Full (Catalyst)"; }
if(($print_report >  0) && (!$IPFIX)) { $sort_field = 4; }

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

# Output report input filtering criteria 
     
$start_flows_out = $start_flows ." $time_zone";
$end_flows_out   = $end_flows ." $time_zone";
if ($sort_field == 1) { $sort_field_out = "Octets"; }
if ($sort_field == 2) { $sort_field_out = "Flows"; }
if ($sort_field == 3) { $sort_field_out = "Packets"; }
if ($sort_field == 4) { $sort_field_out = "N/A"; }
if ($sort_field == 5) { $sort_field_out = "sTime"; }

# Generate a pie-chart if the user is interested

$piechart_link = "no piechart";
if (($pie_charts > 0) && ((($stat_report > 0 ) && ($stat_report < 30)) || (($print_report > 10) && ($print_report <18)))) {
	
	$array_elements = $number_slices - 1;

	open (OUTPUT,"<$work_directory/FlowViewer_output_$suffix");
	while (<OUTPUT>) {

		if (substr($_,0,1) eq "#") { next; }

		$line_count++;

		if (($rate_report) || (($stat_report == 7) && ($IPFIX)) || ($print_report == 14) || ($print_report == 17)) { 
			if ($IPFIX) { 
				if ($sort_field == 1) { ($x,$y,$octets,$packets,$flows) = split(/\s+/,$_); }
				if ($sort_field == 2) { ($x,$y,$flows,$octets,$packets) = split(/\s+/,$_); }
				if ($sort_field == 3) { ($x,$y,$packets,$octets,$flows) = split(/\s+/,$_); }
			} else { 
				($x,$y,$flows,$octets,$packets) = split(/\s+/,$_);
			}
		} else {
			if ($IPFIX) { 
				if ($sort_field == 1) { ($x,$octets,$packets,$flows) = split(/\s+/,$_); }
				if ($sort_field == 2) { ($x,$flows,$octets,$packets) = split(/\s+/,$_); }
				if ($sort_field == 3) { ($x,$packets,$octets,$flows) = split(/\s+/,$_); }
			} else { 
				($x,$flows,$octets,$packets)    = split(/\s+/,$_);
			}
		}

                $IPv4_y = 0; $IPv6_y = 0;
                if ($y =~ m/^\s*-*\d+/) {
                        $_ = $y;
                        $num_dots   = tr/\.//; if ($num_dots   > 0) { $IPv4_y = 1; }
                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6_y = 1; }
                }

		if (($stat_report != 0) && ($octets < $cutoff_octets)) { last; }

		if ($top_count < $array_elements) {
			if ($sort_field == 1) { $top_ten_values[$top_count] = $octets; }
			if ($sort_field == 2) { $top_ten_values[$top_count] = $flows; }
			if ($sort_field == 3) { $top_ten_values[$top_count] = $packets; }
			$x_out = $x;
			$y_out = $y;
			if ($resolve_columns == 0) {
		                $IPv6_x = 0;
		                if ($x_out =~ m/^\s*-*\d+/) {
		                        $_ = $x_out;
		                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6_x = 1; }
		                }
				if ($IPv6_x) {
					$last_colon = rindex($x_out,":") - 1;
					$last_colon = rindex($x_out,":",$last_colon);
					$x_out = "..." . substr($x_out,$last_colon,18);
				} else {
					if ($x_out =~ /[a-zA-Z]/) { ($x_out) = split(/\./,$x_out); }
				}
			}
			if (($resolve_columns == 1) || ($resolve_columns == 2)) {
				$x_out = dig($x);
		                $IPv6_x = 0;
		                if ($x_out =~ m/^\s*-*\d+/) {
		                        $_ = $x_out;
		                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6_x = 1; }
		                }
				if ($IPv6_x) {
					$last_colon = rindex($x_out,":") - 1;
					$last_colon = rindex($x_out,":",$last_colon);
					$x_out = "..." . substr($x_out,$last_colon,18);
				} else {
					if ($x_out =~ /[a-zA-Z]/) { ($x_out) = split(/\./,$x_out); }
				}
			}
			if ($resolve_columns == 3) {
				$x_out = dig_as($x);
			}
			if (($resolve_columns == 5) && ($interface_names)) {
				$x_out = dig_if($x);
			}
			if ($resolve_columns == 7) {
				$x_out = dig_ex($x);
		                $IPv6_x = 0;
		                if ($x_out =~ m/^\s*-*\d+/) {
		                        $_ = $x_out;
		                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6_x = 1; }
		                }
				if ($IPv6_x) {
					$last_colon = rindex($x_out,":") - 1;
					$last_colon = rindex($x_out,":",$last_colon);
					$x_out = "..." . substr($x_out,$last_colon,18);
				} else {
					if ($x_out =~ /[a-zA-Z]/) { ($x_out) = split(/\./,$x_out); }
				}
			}
			$top_ten_labels[$top_count] = $x_out;
			if ($y ne "") { 
				if ($resolve_columns == 0) {
			                $IPv6_y = 0;
			                if ($y_out =~ m/^\s*-*\d+/) {
			                        $_ = $y_out;
			                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6_y = 1; }
			                }
					if ($IPv6_y) {
						$last_colon = rindex($y_out,":") - 1;
						$last_colon = rindex($y_out,":",$last_colon);
						$y_out = "..." . substr($y_out,$last_colon,18);
					} else {
						if ($y_out =~ /[a-zA-Z]/) { ($y_out) = split(/\./,$y_out); }
					}
				}
				if (($resolve_columns == 1) || ($resolve_columns == 2)) { 
					$y_out = dig($y);
			                $IPv6_y = 0;
			                if ($y_out =~ m/^\s*-*\d+/) {
			                        $_ = $y_out;
			                        $num_colons = tr/\://; if ($num_colons > 0) { $IPv6_y = 1; }
			                }
					if ($IPv6_y) {
						$last_colon = rindex($y_out,":") - 1;
						$last_colon = rindex($y_out,":",$last_colon);
						$y_out = "..." . substr($y_out,$last_colon,18);
					} else {
						if ($y_out =~ /[a-zA-Z]/) { ($y_out) = split(/\./,$y_out); }
					}
				}
				if ($resolve_columns == 4) { 
					$y_out = dig_as($y);
				}
				if (($resolve_columns == 6) && ($interface_names)) { 
					$y_out = dig_if($y);
				}
				$top_ten_labels[$top_count] .= " - ". $y_out; 
			}
			$top_count++;
		} elsif ($pie_charts == 1) {
			if ($sort_field == 1) { $top_ten_values[$top_count] += $octets; }
			if ($sort_field == 2) { $top_ten_values[$top_count] += $flows; }
			if ($sort_field == 3) { $top_ten_values[$top_count] += $packets; }
			$top_ten_labels[$array_elements] = "Other";
		}

		if (($line_count-3) > $cutoff_lines) { last; }
	}

	if ($line_count eq "") {

		print " </div>\n";
		&create_UI_service("FlowViewer_Main","service_bottom",$active_dashboard,$filter_hash);
		&finish_the_page("FlowViewer_Main");
 
		$rm_command = "rm $work_directory/FlowViewer_filter_$suffix";
		if ($debug_files ne "Y") { system($rm_command); }
		$rm_command = "rm $work_directory/FlowViewer_output_$suffix";
		if ($debug_files ne "Y") { system($rm_command); }

		exit;

	} else { $line_count = 0; }

	$graph = new GD::Graph::pie(325,175);
	
	$graph->set(
	    transparent     => 1,
	    axislabelclr    => 'black',
	    dclrs           => $pie_colors,
	    '3d'            => 1,
	    pie_height      => 10,
	    start_angle     => 90,
	    suppress_angle  => 20
	)
	or warn $graph->error;
	
	$graph->set_label_font(GD::Font->Small);
	$graph->set_value_font(GD::Font->Small);

	@plot = ([@top_ten_labels],[@top_ten_values]);
	$image = $graph->plot(\@plot) or die $graph->error;
	
	$png_filename = "FlowViewer_save_" . $saved_suffix . ".png";
	$piechart_link = "$graphs_short/$png_filename";

	open(PNG,">$graphs_directory/$png_filename"); 
	binmode PNG; 
	print PNG $image->png;

	print "<center><img src=$piechart_link></center>\n";
	print HTML "<center><img src=$piechart_link></center>\n";

	close (OUTPUT);
}

# Parse through the intermediate, flow tools (or now SiLK) generated, 'FlowViewer_output' file

$print_header  = 1;
$first_scanner = 1;

$sort_file = "$work_directory/FlowViewer_save_" . $saved_suffix;
open (SORTED_SAVE, ">$sort_file");
&start_saved_file($sort_file);
open (SORTED_SAVE, ">>$sort_file");

if ((($print_report > 0) && ($print_report < 12)) || ($stat_report == 99)) { 
	print " <pre><font face=\"Courier New\">\n"; 
	print " <table>\n";
	print SORTED_SAVE " <pre><font face=\"Courier New\">\n"; 
	print SORTED_SAVE " <table>\n";
}

if ($IPFIX && ($silk_compiled_localtime ne "Y") && ($system_time eq "NON-UTC")) { $format_local_time = 1; }

open (OUTPUT,"<$work_directory/FlowViewer_output_$suffix");
while (<OUTPUT>) {

	chop;
	if (substr($_,0,1) eq "#") { next; }
	if (substr($_,0,5) eq "flow-") { 
		if ($stat_report == 30) {
			if (!$start_table) { 

				$report_suffix = &get_suffix;
				$report_filename = "FlowViewer_save_$report_suffix";
				$filter_hash = "SC_$report_filename";
				$main_hash = $filter_hash;
				$report_file = "$work_directory/$report_filename";
				open (SCAN_SAVE, ">$report_file");
				&start_saved_file($report_file);
				close (SCAN_SAVE);
				open (SCAN_SAVE, ">>$report_file");

				print " <table>\n";
				print " <tr><td>&nbsp</td></tr>\n";
				print " <tr><td align=left>The following hosts were discovered to be scanners</td></tr>\n";
				print " <tr><td>&nbsp</td></tr>\n";
				print " </table>\n";
				print " <table>\n";
				print " <tr>\n";
				print "<td>IP Address</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>Host Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>CC</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>AS Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>Flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>Avg Fl Time</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>Avg Pkt Size</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>Pkts/Flow</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "<td>Flows/Sec</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print "</tr>\n";
				print " <tr><td>&nbsp</td></tr>\n";

				print SCAN_SAVE " <table>\n";
				print SCAN_SAVE " <tr><td>&nbsp</td></tr>\n";
				print SCAN_SAVE " <tr><td align=left>The following hosts were discovered to be scanners</td></tr>\n";
				print SCAN_SAVE " <tr><td>&nbsp</td></tr>\n";
				print SCAN_SAVE " </table>\n";
				print SCAN_SAVE " <table>\n";
				print SCAN_SAVE " <tr>\n";
				print SCAN_SAVE "<td>IP Address</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>Host Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>CC</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>AS Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>Flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>Avg Fl Time</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>Avg Pkt Size</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>Pkts/Flow</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "<td>Flows/Sec</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
				print SCAN_SAVE "</tr>\n";
				print SCAN_SAVE " <tr><td>&nbsp</td></tr>\n";
				$start_table = 1;
			}
			if (substr($_,0,16) eq "flow-dscan: host") {

				($left_part,$right_part) = split(/ ts=/);
				($left_part,$ip_address) = split(/=/,$left_part);

				$scan_suffix = &get_suffix;
				$scan_filename = "FlowViewer_save_$scan_suffix";
				$scan_hash  = "SC_$scan_filename";
				$scan_file = "$work_directory/$scan_filename";
				$stats_file = "$work_directory/FlowViewer_scan_stats";
				$filter_hash = $scan_hash;
				$source_addresses = $ip_address;
				open (SORTED_SAVE, ">$scan_file");
				&start_saved_file($scan_file);
				close (SORTED_SAVE);
				$filter_hash = $main_hash;

				$ip_name  = dig($ip_address);
				($as_number,$as_country,$as_name) = dig_as_full($ip_address);

				$filter_file = "$work_directory/FlowViewer_filter_scanner";
				$FORM{source_address} = $ip_address;
				$FORM{cutoff_lines} = 2000;
				create_filter_file(%FORM,$filter_file);
				$flownfilter_command = "$flow_bin_directory/flow-nfilter -f $work_directory/FlowViewer_filter_scanner -FFlow_Filter";
				$flowprint_command = "$flow_bin_directory/flow-print -f5 >>$scan_file";
				$flow_run = "$flownfilter_command <$work_directory/FlowViewer_scanner_$suffix | $flowprint_command";
				system($flow_run);

				$flowstat_command = "$flow_bin_directory/flow-stat -f0 >$stats_file";
				$flow_run = "$flownfilter_command <$work_directory/FlowViewer_scanner_$suffix | $flowstat_command";
				system($flow_run);
				open(STATS,"<$stats_file");
                		while (<STATS>) {
					if ((substr($_,0,1) eq "#") || (substr($_,0,1) eq " ")) { next; }
					($field_name,$field_value) = split(/: /);
					if (/Total Flows/)         { $total_flows   = $field_value; }
					if (/Average flow time/)   { 
						$avg_flow_time = $field_value;
						$avg_flow_time *= 0.001;
						if ($avg_flow_time < 0.001) { $avg_flow_time = "0.000"; }
						$avg_flow_time = substr($avg_flow_time,0,5);
					}
					if (/Average packet size/) { $avg_pkt_size  = $field_value; }
					if (/Average packets per/) { $avg_pkt_flow  = $field_value; }
					if (/Average flows \/ se/) { $avg_flow_sec  = $field_value; }
				}
				$rm_command = "rm $stats_file";
				system($rm_command);

				$cgi_link = "$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=$scan_hash";
				print "<tr><td align=left><a href=$cgi_link>$ip_address</a></td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td>$ip_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td>$as_country</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td>$as_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td align=right>$total_flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td align=right>$avg_flow_time</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td align=right>$avg_pkt_size</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td align=right>$avg_pkt_flow</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "<td align=right>$avg_flow_sec</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print "</tr>\n";

				print SCAN_SAVE "<tr><td align=left><a>$ip_address</a></td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td>$ip_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td>$as_country</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td>$as_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td align=right>$total_flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td align=right>$avg_flow_time</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td align=right>$avg_pkt_size</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td align=right>$avg_pkt_flow</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "<td align=right>$avg_flow_sec</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
				print SCAN_SAVE "</tr>\n";
				next;
			}

		} else {
			if (!$start_table) { 
				print " <table>\n";
				print " <tr><td>&nbsp</td></tr>\n";
				print " <tr><td align=left>Error: Examine presense of flow data for time period specified, etc.</td></tr>\n";
				print " <tr><td>&nbsp</td></tr>\n";
				$start_table = 1;
			}
			print " <tr><td align=left>$_</td></tr>\n";
			next;
		}
	}

	if (($IPFIX) && ($stat_report == 30)) {

		if (!$start_table) { 

			$report_suffix = &get_suffix;
			$report_filename = "FlowViewer_save_$report_suffix";
			$filter_hash = "SC_$report_filename";
			$main_hash = $filter_hash;
			$report_file = "$work_directory/$report_filename";
			open (SCAN_SAVE, ">$report_file");
			&start_saved_file($report_file);
			close (SCAN_SAVE);
			open (SCAN_SAVE, ">>$report_file");

			print " <table>\n";
			print " <tr><td>&nbsp</td></tr>\n";
			print " <tr><td align=left>The following hosts were discovered to be scanners</td></tr>\n";
			print " <tr><td>&nbsp</td></tr>\n";
			print " </table>\n";
			print " <table>\n";
			print " <tr>\n";
			print " <td>IP Address</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>Host Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>CC</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>AS Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>Start Time</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>End Time</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>Flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>Packets</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " <td>Octets</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print " </tr>\n";
			print " <tr><td>&nbsp</td></tr>\n";

			print SCAN_SAVE " <table>\n";
			print SCAN_SAVE " <tr><td>&nbsp</td></tr>\n";
			print SCAN_SAVE " <tr><td align=left>The following hosts were discovered to be scanners</td></tr>\n";
			print SCAN_SAVE " <tr><td>&nbsp</td></tr>\n";
			print SCAN_SAVE " </table>\n";
			print SCAN_SAVE " <table>\n";
			print SCAN_SAVE " <tr>\n";
			print SCAN_SAVE " <td>IP Address</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>Host Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>CC</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>AS Name</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>Start Time</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>End Time</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>Flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>Packets</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " <td>Octets</td><td>&nbsp&nbsp&nbsp&nbsp</td>\n";
			print SCAN_SAVE " </tr>\n";
			print SCAN_SAVE " <tr><td>&nbsp</td></tr>\n";
			$start_table = 1;
		}

		($sip,$proto,$stime,$etime,$flows,$packets,$octets) = split(/\|/,$_);

		$sip     =~ s/^\s+//;
		$proto   =~ s/^\s+//;
		$stime   =~ s/^\s+//;
		$etime   =~ s/^\s+//;
		$flows   =~ s/^\s+//;
		$packets =~ s/^\s+//;
		$octets  =~ s/^\s+//;

		if ($sip eq "sip") { next; }

		if ($flow_analysis) {
			$oct_per_flow = int($octets / $flows);
			$pkt_per_flow = int($packets / $flows);
		}

		$FORM{source_address} = $sip;
        	create_ipfix_filter(%FORM);

		$scan_suffix = &get_suffix;
		$scan_filename = "FlowViewer_save_$scan_suffix";
		$scan_hash  = "SC_$scan_filename";
		$scan_file = "$work_directory/$scan_filename";
		$stats_file = "$work_directory/FlowViewer_scan_stats";
		$filter_hash = $scan_hash;
		$source_addresses = $sip;
		$cutoff_lines = 1000;
		open (SORTED_SAVE, ">$scan_file");
		&start_saved_file($scan_file);
		close (SORTED_SAVE);
		$filter_hash = $main_hash;

		$rwfilter_command = "$silk_bin_directory/rwfilter $site_config_modifier $partitioning_switches --pass=stdout $prefiltered_file";
                $field_sequence = "22,23,10,13,1,3,14,2,4,5,8,6,7";
                $rwcut_command  = "$silk_bin_directory/rwcut $site_config_modifier --fields=$field_sequence --delimited=\"  \" ";
        	$silk_command = "$rwfilter_command | $rwcut_command >> $scan_file";
        	if ($debug_viewer eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
        	system ($silk_command);

		$sip_name = dig($sip);
		($as_number,$as_country,$as_name) = dig_as_full($sip);

		$cgi_link = "$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=$scan_hash";
		print "<tr><td align=left><a href=$cgi_link>$sip</a></td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td>$sip_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td>$as_country</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td>$as_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td align=right>$stime</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td align=right>$etime</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td align=right>$flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td align=right>$packets</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "<td align=right>$octets</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print "</tr>\n";

		print SCAN_SAVE "<tr><td align=left><a>$sip</a></td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td>$sip_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td>$as_country</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td>$as_name</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td align=right>$stime</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td align=right>$etime</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td align=right>$flows</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td align=right>$packets</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "<td align=right>$octets</td><td>&nbsp&nbsp&nbsp&nbsp</td>";
		print SCAN_SAVE "</tr>\n";
		next;
	}

	if ((($print_report > 0) && (!$IPFIX)) || (($print_report > 0) && ($print_report < 12)) || ($stat_report == 99) || ($stat_report == 30)) {

		$line_count++;
		if ((($line_count-1) > $cutoff_lines) && ($stat_report != 99)) { last; }

		if (($print_report == 5) && (/DstP    P/)) { s/DstP    P/DstP  P  /; }

		if (($stat_report == 99) && (!$IPFIX) && ($sampling_multiplier > 1)) {

			$line = $_;
                	($field_name,$field_value) = split(/:/,$line); 
	                if (($line =~ /Total Flows/)   || ($line =~ /Total Octets/) ||  
	                    ($line =~ /Total Packets/) || ($line =~ /Total Time/)   || 
	                    ($line =~ /Average flows \/ second \(flow\)/) || 
	                    ($line =~ /Average flows \/ second \(real\)/) || 
	                    ($line =~ /Average Kbits \/ second \(flow\)/) || 
	                    ($line =~ /Average Kbits \/ second \(real\)/)) {  
                        	$field_value *= $sampling_multiplier; 
                        	$field_value .= "*";  
                        	$line = $field_name .": $field_value";    
			}
			print " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			print SORTED_SAVE " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			next;

		} elsif ($stat_report == 30) {

			if (substr(0,16) eq "flow-dscan: host") {
				$line = $_;
				print SORTED_SAVE "$line\n";
			}
			next;

		} elsif (($print_report == 1) && ($date_format =~ /DMY/)) {

			# Converting output for data formatting

			$line = $_;

			if ($IPFIX) {

				if ($line_count > 1) { &convert_to_local; }

			} else {

				if ((substr($line,0,1) eq " ") && (substr($line,1,1) =~ /[0-9]/)) {
	
					$line_mnth = substr($line,1,2);
					$line_date = substr($line,3,2);
					$temp_mnth = $line_mnth;
					substr($line,1,2) = $line_date;
					substr($line,3,2) = $temp_mnth;
					$line_mnth = substr($line,20,2);
					$line_date = substr($line,22,2);
					$temp_mnth = $line_mnth;
					substr($line,20,2) = $line_date;
					substr($line,22,2) = $temp_mnth;
				}	
			}

			print " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			print SORTED_SAVE " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			next;

		} elsif (($print_report == 5) && ($date_format =~ /DMY/)) {

			# Converting output for data formatting

			$line = $_;

			if ($IPFIX) {

				if ($line_count > 1) { &convert_to_local; }

			} else {

				if (substr($line,0,1) =~ /[0-9]/) {
	
					$line_mnth = substr($line,0,2);
					$line_date = substr($line,2,2);
					$temp_mnth = $line_mnth;
					substr($line,0,2) = $line_date;
					substr($line,2,2) = $temp_mnth;
					$line_mnth = substr($line,18,2);
					$line_date = substr($line,20,2);
					$temp_mnth = $line_mnth;
					substr($line,18,2) = $line_date;
					substr($line,20,2) = $temp_mnth;
				}	
			}

			print " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			print SORTED_SAVE " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			next;
		}

		if ((($print_report == 1) || ($print_report == 5)) && ($format_local_time)) { 

			$line = $_;
			if ($line_count > 1) { &convert_to_local; }
			print " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";
			print SORTED_SAVE " <tr><td align=left><font face=\"Courier New\">$line</font></td></tr>\n";

		} else {

			print " <tr><td align=left><font face=\"Courier New\">$_</font></td></tr>\n";
			print SORTED_SAVE " <tr><td align=left><font face=\"Courier New\">$_</font></td></tr>\n";

		}

		next;
	}

	if (($stat_report == 8) || ($stat_report == 9) || ($stat_report == 11)) { $country_report = 1; }

	# Print out the header

	if ($print_header) {

	        # Create column headers with sort links

		$source_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Source^$ascend>$heading_1</a>";
		$dest_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Dest^$ascend>$heading_2</a>";
		$country_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Country^$ascend>Country</a>";
		$octfl_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^OctFlow^$ascend>Octs/Flow</a>";
		$pktfl_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^PktFlow^$ascend>Pkts/Flow</a>";
		
		if ($sampling_multiplier > 0) {
			$flows_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Flows^$ascend>Flows*</a>";
			$octets_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Octets^$ascend>Octets*</a>";
			$packets_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Packets^$ascend>Packets*</a>";
			$mbps_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Mbps^$ascend>Avg. Rate*</a>";
		} else {
			$flows_link   = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Flows^$ascend>Flows</a>";
			$octets_link  = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Octets^$ascend>Octets</a>";
			$packets_link = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Packets^$ascend>Packets</a>";
			$mbps_link    = "<a href=$cgi_bin_short/FlowViewer_Sort.cgi?$active_dashboard^$filter_hash^Mbps^$ascend>Avg. Rate</a>";
		}
		
		print "<br>\n";
		print "<center>\n";
		print "<table>\n";
		print "<tr>\n";
		print "<td align=left>$source_link</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		if ($heading_2 ne "") { 
			print "<td align=left>$dest_link</td>\n";
			print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		}
		print "<td align=right>$flows_link</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$octets_link</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$packets_link</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		if ($rate_report) { print "<td align=right>$mbps_link</td>\n"; }
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
		print "</tr>\n";
		print "<tr><td>&nbsp&nbsp</td></tr>\n";

		print "</b>";

		$header_line = "$heading_1 : ";
		if ($heading_2 ne "") { $header_line .= "$heading_2 : "; }
		$header_line .= "Flows : Octets : Packets";
		if ($rate_report) { $header_line .= " : Avg. Rate"; }
		if ($flow_analysis) { 
			$header_line .= " : Octs/Flow : Pkts/Flow";
			if ($country_report) { $header_line .= " : Country"; }
		}
        	print SORTED_SAVE "$header_line\n";

		$print_header = 0;
	}

	# Print out the individual lines

	$line_count++;

	if (($rate_report) || (($stat_report == 7) && ($IPFIX)) || ($print_report == 14) || ($print_report == 17)) { 
		if ($IPFIX) { 
			if ($sort_field == 1) { ($x,$y,$octets,$packets,$flows) = split(/\s+/,$_); }
			if ($sort_field == 2) { ($x,$y,$flows,$octets,$packets) = split(/\s+/,$_); }
			if ($sort_field == 3) { ($x,$y,$packets,$octets,$flows) = split(/\s+/,$_); }
		} else { 
			($x,$y,$flows,$octets,$packets) = split(/\s+/,$_);
		}
	} else {
		if ($IPFIX) { 
			if ($sort_field == 1) { ($x,$octets,$packets,$flows) = split(/\s+/,$_); }
			if ($sort_field == 2) { ($x,$flows,$octets,$packets) = split(/\s+/,$_); }
			if ($sort_field == 3) { ($x,$packets,$octets,$flows) = split(/\s+/,$_); }
		} else { 
			($x,$flows,$octets,$packets)    = split(/\s+/,$_);
		}
	}

        if ($rate_report) {
		$flow_rate = int($octets*8/$report_length);
		if ($sampling_multiplier > 1) { $flow_rate *= $sampling_multiplier; }
		$flow_rate = format_number($flow_rate);
	}

	# Multiply by sampling multiplier if set

	if ($sampling_multiplier > 1) { 
		$flows     *= $sampling_multiplier; 
		$octets    *= $sampling_multiplier; 
		$packets   *= $sampling_multiplier; 
	}

	if ($flow_analysis) {
		$oct_per_flow = int($octets / $flows);
		$pkt_per_flow = int($packets / $flows);
		if ($country_report) { ($as_number,$as_country,$as_name) = dig_as_full($x); }
	}

	if (($stat_report != 0) && ($octets < $cutoff_octets)) { last; }

        # Unit conversion if requested

        if ($unit_conversion eq "Y") { 
             $octets = convert_octets2string($octets); 
        }

	if ($resolve_columns == 1) {
                 $x = dig($x);
        } elsif ($resolve_columns == 2) {
                 $x = dig($x);
                 $y = dig($y);
        } elsif ($resolve_columns == 3) {
                 $x = dig_as($x);
        } elsif ($resolve_columns == 4) {
                 $x = dig_as($x);
                 $y = dig_as($y);
        } elsif (($resolve_columns == 5) && ($interface_names)) {
                 $x = dig_if($x);
        } elsif (($resolve_columns == 6) && ($interface_names)) {
                 $x = dig_if($x);
                 $y = dig_if($y);
        } elsif ($resolve_columns == 7) {
                 $x = dig_ex($x);
	}
 
	if (($print_report == 12) || ($print_report == 15)) { $x = $x . "/". $sip_prefix_length; }
	if (($print_report == 13) || ($print_report == 16)) { $x = $x . "/". $dip_prefix_length; }
	if (($print_report == 14) || ($print_report == 17)) { $x = $x . "/". $sip_prefix_length; $y = $y . "/". $dip_prefix_length; }

        # Build the line

        if ($heading_2 ne "" ) {
		$line = $x ." ^ ". $y ." ^ ". $flows ." ^ ". $octets ." ^ ". $packets;
        	if ($rate_report) { $line = $line ." ^ ". $flow_rate; }
		if ($flow_analysis) { $line .= " ^ ". $oct_per_flow ." ^ ". $pkt_per_flow; }
	} elsif (($heading_1 ne "") && ($heading_2 eq "")) {
		$line = $x ." ^ ". $flows ." ^ ". $octets ." ^ ". $packets;
		if ($flow_analysis)  { $line .= " ^ ". $oct_per_flow ." ^ ". $pkt_per_flow; }
		if ($country_report) { $line .= " ^ ". $as_country; }
        } elsif ($print_report eq "0") {
		$line = sprintf("%-12s %-19s %-19s %-19s", $x, $y, $octets, $flows);
		if ($flow_analysis) { $line = sprintf("%-12s %-19s %-19s %-19s %-19s %-19s %-19s", $x, $y, $octets, $flows, $oct_per_flow, $pkt_per_flow, $as_country); }
	} else {
		$line = $_;
	}
	
        if ($line ne "") { print SORTED_SAVE "$line\n"; }

	print "<tr>\n";
	print "<td align=left>$x</td>\n";
	print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	if ($heading_2 ne "") { 
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
			print "<td align=right>$as_country</td>\n";
		}
	}
	print "</tr>\n";

	if (($stat_report > 0) && ($stat_report != 99)) { if (($line_count+1) > $cutoff_lines) { last; } }
}
close(SORTED_SAVE);

print " <tr><td>&nbsp</td></tr>";
print " <tr><td>&nbsp</td></tr>";
print " </table>\n";
print " </div>\n";

&create_UI_service("FlowViewer_Main","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowViewer_Main");
 
# Remove intermediate files

$rm_command = "rm $work_directory/FlowViewer_filter_$suffix";
if ($debug_files ne "Y") { system($rm_command); }
$rm_command = "rm $work_directory/FlowViewer_output_$suffix";
if ($debug_files ne "Y") { system($rm_command); }
$rm_command = "rm $work_directory/FlowViewer_scanner_$scan_suffix";
if ($debug_files ne "Y") { system($rm_command); }

# Subroutines

sub print_error {

	my ($error_text) = @_;
	print "  <br>";
	print "  $error_text\n";  
	print " </div>\n";
	&create_UI_service("FlowViewer_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowViewer_Main");
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
        return $host_name;
}

sub dig_as {

        my ($host_address) = @_;
        $as_name = $host_address;

        if (defined($as_names{$host_address})) {
                $as_name = $as_names{$host_address};
        } else {
                open(DIG_AS,"dig +short AS$host_address.asn.cymru.com TXT 2>&1|");
                $answer_record = 0;
                while (<DIG_AS>) {
                        chomp;
                        if (/[0-9]+ | [A-Z]+ |.*/) {
                                s/"//g;
                                ($as_number, $as_country, $as_rir, $as_date, $as_name) = split(/ \| /, $_);
                                @as_info = split(/\s/, $as_name);
                                $as_name = shift(@as_info);
                        }
                }
                if ($as_name eq "") { $as_name = $host_address; }
                $as_names{$host_address} = $as_name;
        }
        return $as_name;
}

sub dig_as_full {

	my ($host_address) = @_;

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

sub dig_ex {

	my ($exporter_number) = @_;
	$exporter_name = $exporter_number;

	foreach $exporter (@exporters) {
		($exporter_ip,$exp_name) = split(/:/,$exporter);
		if ($exporter_number eq $exporter_ip) { $exporter_name = $exp_name; }
	}
	return $exporter_name;
}

sub convert_to_local {

	# SiLK rwcut time format: 2014/10/31T16:00:58.978     5.800 2014/10/31T16:01:04.778

	if ($line_count == 2) {
		$s_time_index = index($line,"T",0);
		$e_time_index = index($line,"T",24);
	}
		
	for $endpoint ("start","end") {

		if ($endpoint eq "start") { $start_pos = $s_time_index; }
		if ($endpoint eq "end")   { $start_pos = $e_time_index; }

		$temp_year = substr($line,$start_pos-10,4);
		$temp_mnth = substr($line,$start_pos-5,2);
		$temp_date = substr($line,$start_pos-2,2);
		$temp_hour = substr($line,$start_pos+1,2);
		$temp_min  = substr($line,$start_pos+4,2);
		$temp_sec  = substr($line,$start_pos+7,2);
		$temp_msec = substr($line,$start_pos+10,3);
	
		$endpoint_epoch_gm = timegm($temp_sec,$temp_min,$temp_hour,$temp_date,$temp_mnth-1,$temp_year-1900);
		($temp_sec,$temp_min,$temp_hour,$temp_date,$temp_mnth,$temp_year,$day,$yr_date,$DST) = localtime($endpoint_epoch_gm);
		$temp_year += 1900;
		$temp_mnth++;
		if (length($temp_mnth) < 2) { $temp_mnth = "0" . $temp_mnth; }
		if (length($temp_date) < 2) { $temp_date = "0" . $temp_date; }
		if (length($temp_hour) < 2) { $temp_hour = "0" . $temp_hour; }
		if (length($temp_min)  < 2) { $temp_min  = "0" . $temp_min;  }
		if (length($temp_sec)  < 2) { $temp_sec  = "0" . $temp_sec;  }
	
		if ($date_format =~ /DMY/) {
			$endpoint_date = $temp_date ."/". $temp_mnth ."/". $temp_year;
			$endpoint_time = $temp_hour .":". $temp_min  .":". $temp_sec .".". $temp_msec;
		} elsif ($date_format =~ /MDY/) {
			$endpoint_date = $temp_mnth ."/". $temp_date ."/". $temp_year;
			$endpoint_time = $temp_hour .":". $temp_min  .":". $temp_sec .".". $temp_msec;
		} else {
			$endpoint_date = $temp_year ."/". $temp_mnth ."/". $temp_date;
			$endpoint_time = $temp_hour .":". $temp_min  .":". $temp_sec .".". $temp_msec;
		}

		$endpoint_date_time = $endpoint_date ."T". $endpoint_time;

		substr($line,$start_pos-10,23) = $endpoint_date_time;
	}
}
