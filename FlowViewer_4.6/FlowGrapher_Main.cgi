#! /usr/bin/perl
#
#  Purpose:
#  FlowGrapher_Main.cgi permits a Web user to analyze Net Flow data stored in
#  flow tools format and create a graph and partial listing of flows.
#
#  Description:
#  The script responds to an HTML form from the user in order to collect
#  parameters that will control the analysis (e.g., router, time-period, ip
#  addresses etc.) Upon receipt of the form input the script creates a flow tools
#  filter file which controls the selection of the data via the invocation of
#  additional flow tools utilities. A graph is then created using the GD graphics
#  package.
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
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  01/01/2006      2.0     Original released version
#  J. Loiacono  01/16/2006      2.1     Fixed compute of concatenation date,
#                                       end-of-year problem
#  J. Loiacono  01/26/2006      2.2     New flow_select to determine inclusion,
#                                       adjusted processing for flow_select
#  J. Loiacono  04/15/2006      2.3     Minimized use of timelocal for epoch to
#                                       speed things up ten-fold
#  J. Loiacono  05/31/2006      2.3.1   Fixed last bucket problem; caused spikes
#					(thanks Mark Foster)
#  J. Loiacono  07/04/2006      3.0     Changed name for reorganization
#                                       Resolve address option (thanks Mark Foster)
#                                       Single script for GDBM/NDBM (thanks Ed Ravin)
#  J. Loiacono  12/25/2006      3.1     Changes for MIN/MAX, more than 30 days
#  J. Loiacono  02/22/2007      3.2     [No Change to this module]
#  J. Loiacono  04/01/2007      3.2     Fixes to bucket alignment (removed rounding) 
#                                       (thanks Dario La Guardia)
#  J. Loiacono  05/01/2007      3.2     Fixed FlowGrapher first, last buckets
#  J. Loiacono  12/07/2007      3.3     Sampling Multiplier, Column Sorting
#                                       Graph Types (Eric Lautenschlaeger)
#  J. Loiacono  12/15/2007      3.3.1   New $no_devices ... parameter
#  J. Loiacono  01/26/2008      3.3.1   E. Lautenschlaeger fix for exporter names
#  J. Loiacono  02/02/2008      3.3.1   Fixed end-of-month processing, Dport sorting
#  J. Loiacono  12/31/2008      3.3.1   Fixed FlowGrapher sort for very first invocation
#  J. Loiacono  03/17/2011      3.4     Support for change of device w/o resetting form values
#                                       Dynamic Resolve col widths, flows/sec, nonzero stats
#                                       Sped up the conversion of flow-tools times to epoch
#                                       Fixed 'flows' graphing; was 'flags' :-(
#                                       Fixed a sorting problem
#  J. Loiacono  05/21/2011      3.4     Fixed speeded-up FlowGrapher for non-GMT hosts
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  04/15/2013      4.1     Removed extraneuos formatting
#  J. Loiacono  04/15/2013      4.2     Introduced Linear processing for flow-tools runs
#  J. Loiacono  09/11/2013      4.2.1   Used prefiltered files to speed SiLK processing
#					Adjusted Flows processing to keep consistent w/ FT
#                                       Mods for international date formatting
#  J. Loiacono  01/26/2014      4.3     Use of "-" to list smallest flows
#  J. Loiacono  07/04/2014      4.4     Multiple Dashboards and largest src/dst for Analysis
#  J. Loiacono  11/02/2014      4.5     SiLK local timezone fixes
#                                       IPv6 hyper-link fixes
#                                       Use of $site_config_file on SiLK commands
#  J. Loiacono  01/26/2015      4.6     Timezone from system (not Configuration)
#                                       Fixed local timezone processing for SiLK
#                                       Fixed detail lines for 'smallest' (use "-")
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

if ($debug_grapher eq "Y") { open (DEBUG,">$work_directory/DEBUG_GRAPHER"); }
if ($debug_grapher eq "Y") { print DEBUG "In FlowGrapher_Main.cgi\n"; }

# Tie in the 'names' file which saves IP address resolved names 
      
if (eval 'local $SIG{"__DIE__"}= sub { }; use GDBM_File;   
        tie %host_names, "GDBM_File", "$names_directory/names", GDBM_WRCREAT, 0666;' ) { 
	if ($debug_grapher eq "Y") { print DEBUG "Using GDBM\n"; } };  
if (eval 'local $SIG{"__DIE__"}= sub { }; use NDBM_File; use Fcntl;    
        tie %host_names, "GDBM_File", "$names_directory/names", GDBM_WRCREAT, 0666;' ) {
	if ($debug_grapher eq "Y") { print DEBUG "Using NDBM\n"; } };  

# Set up graphing colors

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
      
# Adjust to switch in device or exporter
       
($fg_link,$FORM{device_name}) = split(/DDD/,$FORM{device_name});
($fg_link,$FORM{exporter})    = split(/EEE/,$FORM{exporter});

# Respond to Analysis focusing if requested

if (($ENV{'QUERY_STRING'}) ne "") {
        ($active_dashboard,$analyze_method,$analyze_object,$analyze_hash) = split(/\^/,$ENV{'QUERY_STRING'});
        $filter_filename = substr($analyze_hash,3,255);
        $filter_source_file = "$work_directory/$filter_filename";
        open(FILTER,"<$filter_source_file");
        while (<FILTER>) {
                chop;
		if (/END FILTERING/) { last; }
                ($field,$field_value) = split(/: /);
		if (substr($field,-1,1) eq ":") { chop $field; }
		if ($field eq "active_dashboard") { $field = "active_dashboard"; }
		if ($field eq "source_addresses") { $field = "source_address"; }
		if ($field eq "source_ports")     { $field = "source_port"; }
		if ($field eq "source_ifs")       { $field = "source_if"; }
		if ($field eq "sif_names")        { $field = "sif_name"; }
		if ($field eq "source_ases")      { $field = "source_as"; }
		if ($field eq "dest_addresses")   { $field = "dest_address"; }
		if ($field eq "dest_ports")       { $field = "dest_port"; }
		if ($field eq "dest_ifs")         { $field = "dest_if"; }
		if ($field eq "dif_names")        { $field = "dif_name"; }
		if ($field eq "dest_ases")        { $field = "dest_as"; }
		if ($field eq "nexthop_ips")      { $field = "nexthop_ip"; }
                $FORM{$field} = $field_value;
	}

	$FORM{'active_dashboard'} = $active_dashboard;

        if ($debug_grapher eq "Y") { print DEBUG "QUERY_STRING analyze_method: $analyze_method  analyze_object: $analyze_object  analyze_hash: $analyze_hash\n"; }
 
        if (($analyze_method =~ /Src/) || ($analyze_method =~ /Spt/)) {
		($o[0],$o[1],$o[2],$o[3],$o[4],$o[5],$o[6],$o[7],$o[8],$o[9],$o[10]) = split(/\|/,$analyze_object);
		for ($i=1;$i<=10;$i++) {
			if ($o[$i] ne "") { $exclude_objects .= "-". $o[$i] .","; }
		}
		chop $exclude_objects;
		if ($analyze_object =~ "AllOtherHosts") {
			if ($FORM{'source_address'} =~ /-/) {
                		$FORM{'source_address'} .= ",". $exclude_objects;
			} else {
                		$FORM{'source_address'}  = $exclude_objects;
			}
		} elsif ($analyze_object =~ "AllOtherPorts") {
			if ($FORM{'source_port'} =~ /-/) {
                		$FORM{'source_port'} .= ",". $exclude_objects;
			} else {
                		$FORM{'source_port'}  = $exclude_objects;
			}
		} else {
			if (($analyze_object =~ /\./) || ($analyze_object =~ /:/)) {
                		$FORM{'source_address'} = $analyze_object;
			} else {
                		$FORM{'source_port'} = $analyze_object;
			}
		}
        } elsif (($analyze_method =~ /Dst/) || ($analyze_method =~ /Dpt/)) {
		($o[0],$o[1],$o[2],$o[3],$o[4],$o[5],$o[6],$o[7],$o[8],$o[9],$o[10]) = split(/\|/,$analyze_object);
		for ($i=1;$i<=10;$i++) {
			if ($o[$i] ne "") { $exclude_objects .= "-". $o[$i] .","; }
		}
		chop $exclude_objects;
		if ($analyze_object =~ "AllOtherHosts") {
			if ($FORM{'dest_address'} =~ /-/) {
                		$FORM{'dest_address'} .= ",". $exclude_objects;
			} else {
                		$FORM{'dest_address'}  = $exclude_objects;
			}
		} elsif ($analyze_object =~ "AllOtherPorts") {
			if ($FORM{'dest_port'} =~ /-/) {
                		$FORM{'dest_port'} .= ",". $exclude_objects;
			} else {
                		$FORM{'dest_port'}  = $exclude_objects;
			}
		} else {
			if (($analyze_object =~ /\./) || ($analyze_object =~ /:/)) {
                		$FORM{'dest_address'} = $analyze_object;
			} else {
                		$FORM{'dest_port'} = $analyze_object;
			}
		}
	}
}

if ($debug_grapher eq "Y") { print DEBUG "FORM{device_name}: $FORM{device_name}\n"; }
if ($debug_grapher eq "Y") { print DEBUG "FORM{exporter}: $FORM{exporter}\n"; }

# Clean up inputs

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

# Parameters for generating a FlowGrapher graph 
      
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
$detail_lines        = $FORM{'detail_lines'}; 
$bucket_size         = $FORM{'bucket_size'}; 
$graph_multiplier    = $FORM{'graph_multiplier'}; 
$resolve_addresses   = $FORM{'resolve_addresses'};
$stats_method        = $FORM{'stats_method'};
$graph_type          = $FORM{'graph_type'};
$sampling_multiplier = $FORM{'sampling_multiplier'};
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

if ($debug_grapher eq "Y") { print DEBUG "FORM{start_date}: $FORM{start_date}  start_date: $start_date  FORM{end_date}: $FORM{end_date}  end_date: $end_date\n"; }
if ($debug_grapher eq "Y") { print DEBUG "FORM{start_time}: $FORM{start_time}  start_time: $start_time  FORM{end_time}: $FORM{end_time}  end_time: $end_time\n"; }

if ($device_name ne "") { $save_file = "$device_name"; } 
if ($exporter ne "")    { $save_file = "$exporter"; }

# Determine if we are looking at an IPFIX device

$IPFIX = 0;
foreach $ipfix_device (@ipfix_devices) {
	if ($device_name eq $ipfix_device) { $IPFIX = 1; if ($debug_viewer eq "Y") { print DEBUG "This device is exporting IPFIX\n";} }
}

# Start up the Saved file 

$suffix      = &get_suffix;
$saved_hash  = "FlowGrapher_save_$suffix"; 
$filter_hash = "FG_$saved_hash";
$saved_html  = "$work_directory/$saved_hash"; 
&start_saved_file($saved_html);

# Start the web page output
 
&create_UI_top($active_dashboard);
&create_UI_service("FlowGrapher_Main","service_top",$active_dashboard,$filter_hash);
print " <div id=content_wide>\n";
print " <span class=text16>FlowGrapher Report from $device_name</span>\n";

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
if ( $mn<1 || $mn>12 || $da<1 || $da>31 || $yr<1990 || $yr>2100 ) { &print_error("Bad date format: $FORM(start_date}"); }
$start_yr = $yr;
$start_mn = $mn; if (length($start_mn) < 2) { $start_mn = "0" . $start_mn; }
$start_da = $da; if (length($start_da) < 2) { $start_da = "0" . $start_da; }
$start_md = $start_mn . $start_da;

($hr,$mi,$sc) = split(/:/,$start_time);
if ( $hr=~/\D/ || $mi=~/\D/ || $sc=~/\D/ ) { &print_error("Bad time format: $start_time"); };
if (length($hr)>2 || $hr>23 || length($mi)>2 || $mi>59 || length($sc)>2 || $sc>59 ) { &print_error("Bad time format: $start_time"); }

($mn,$da,$yr) = split(/\//,$end_date);
if ( $mn=~/\D/ || $da=~/\D/ || $yr=~/\D/ ) { &print_error("Bad date format: $end_date"); };
if ( $mn<1 || $mn>12 || $da<1 || $da>31 || $yr<1990 || $yr>2100 ) { &print_error("Bad date format: $end_date"); }

($hr,$mi,$sc) = split(/:/,$end_time);
if ( $hr=~/\D/ || $mi=~/\D/ || $sc=~/\D/ ) { &print_error("Bad time format: $end_time"); };
if (length($hr)>2 || $hr>23 || length($mi)>2 || $mi>59 || length($sc)>2 || $sc>59 ) { &print_error("Bad time format: $end_time"); }
 
# Establish Start-of-Year epochs, secs in months, for current, prior, and next years to speed processing of each flow

$current_year = "$start_yr"; 
$prior_year   = $current_year - 1; 
$next_year    = $current_year + 1; 
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
if ($debug_grapher eq "Y") { print DEBUG "  Start Date: $FORM{start_date}  $FORM{start_time}  Epoch: $start_epoch  DST: $start_epoch_dst\n"; }

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
$prefix = $yr . $mnth . $date ."_". $hr . $min . $sec;
 
if ($bucket_size eq "300E") {
	$bucket_size = 300;
	$use_bucket_endtime = 1;
} 

# Determine the flow files concatenation start and end time

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
 
if (!$IPFIX) {

	# Build up flow-tools file concatenation parameters

	$cat_start_epoch = $start_epoch - $flow_file_length - 1;
	$cat_end_epoch   = $end_epoch   + $flow_capture_interval;

	$cat_start = epoch_to_date($cat_start_epoch,$time_zone);
	$cat_end   = epoch_to_date($cat_end_epoch,$time_zone);
	
	($cat_start_date,$cat_start_time)     = split(/ /,$cat_start);
	($start_month,$start_day,$start_year) = split(/\//,$cat_start_date);
	$start_ymd = $start_year . $start_month . $start_day; 
	($cat_end_date,$cat_end_time)         = split(/ /,$cat_end);
	($end_month,$end_day,$end_yr)         = split(/\//,$cat_end_date);
	$end_ymd = $end_yr . $end_month . $end_day; 
	
	$cat_end_midnight = date_to_epoch($cat_end_date,$midnight,$time_zone) + 86400;

	$concatenate_parameters = "-a -t \"$cat_start\" -T \"$cat_end\" ";
 
	if (($start_ymd ne $end_ymd) && ($end_epoch > $start_epoch)) {
	        for ($i=0;$i<$maximum_days;$i++) {
	                if (($cat_start_epoch + $i*86400) > $cat_end_midnight) { last; }
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
	}
	elsif ($start_ymd eq $end_ymd) {
	 
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
	 
	        if (-e $cat_directory) { $concatenate_parameters .= "$cat_directory "; }
	}
	else {
	        &print_error("Start day ($FORM{start_date}) is past End day ($FORM{end_date})");
	}
	
	# Set up the commands to concatenate and filter the files 
	 
	$filter_file = "$work_directory/FlowGrapher_filter_$suffix";
	open (FILTER,">$filter_file");
	create_filter_file(%FORM,$filter_file);
	$flowcat_command = "$flow_bin_directory/flow-cat" . " $concatenate_parameters";
	$flownfilter_command = "$flow_bin_directory/flow-nfilter -f $work_directory/FlowGrapher_filter_$suffix -FFlow_Filter"; 
	
	# Determine whether we will use the linear method (i.e., flow-report) or examine each flow individually (Flows Active, or for Analysis)

	if (($graph_type eq "bps") || ($graph_type eq "pps") || ($graph_type eq "fpsi")) { $LINEAR = 1; }

	if ($LINEAR) {

		$detail_lines_abs = abs($detail_lines);

		# Start the Linear method (i.e., not Prorated)

		time_check("start run_Linear");
		$flowbuckets_cat_command = "$flowcat_command | $flownfilter_command > $work_directory/FG_buckets_cat_$suffix"; 
		if ($debug_grapher eq "Y") { print DEBUG "$flowbuckets_cat_command\n"; }
		system($flowbuckets_cat_command);

		# Generate graph buckets using flow-report

		$buckets_cfg = "$work_directory/FG_buckets_cfg_$suffix";
		open (BUCKETS_CFG,">$buckets_cfg");
		print BUCKETS_CFG "stat-report buckets\n";
		print BUCKETS_CFG "  type linear-interpolated-flows-octets-packets\n";
		print BUCKETS_CFG "  output\n";
		print BUCKETS_CFG "    format ascii\n";
		print BUCKETS_CFG "    options +header,+totals\n";
		print BUCKETS_CFG "\n";
		print BUCKETS_CFG "stat-definition LINEAR\n";
		print BUCKETS_CFG "  report buckets\n";
		close(BUCKETS_CFG);
	     
		time_check("start buckets_Linear");
		$flowbuckets_command  = "$flow_bin_directory/flow-report -s$buckets_cfg -SLINEAR < $work_directory/FG_buckets_cat_$suffix > $work_directory/FlowGrapher_buckets_$suffix";
		if ($debug_grapher eq "Y") { print DEBUG "$flowbuckets_command\n"; }
		system($flowbuckets_command);

		# Generate detail lines using flow-report

		$details_cfg = "$work_directory/FG_details_cfg_$suffix";
		open (DETAILS_CFG,">$details_cfg");
		print DETAILS_CFG "include-filter $filter_file\n";
		print DETAILS_CFG "\n";
		print DETAILS_CFG "stat-report details\n";
		print DETAILS_CFG "  type ip-source/destination-address/ip-source/destination-port\n";
		print DETAILS_CFG "  output\n";
		print DETAILS_CFG "    format ascii\n";
		print DETAILS_CFG "    fields +key1,+key2,+key3,+key4,+flows,+octets,+packets,+duration,+index,+first,+last,+other\n";
		if    (($detail_lines > 0) && ($graph_type =~ /bps/)) { print DETAILS_CFG "    sort +octets\n"; }
		elsif (($detail_lines < 0) && ($graph_type =~ /bps/)) { print DETAILS_CFG "    sort -octets\n"; }
		if    (($detail_lines > 0) && ($graph_type =~ /fps/)) { print DETAILS_CFG "    sort +flows\n"; }
		elsif (($detail_lines < 0) && ($graph_type =~ /fps/)) { print DETAILS_CFG "    sort -flows\n"; }
		if    (($detail_lines > 0) && ($graph_type =~ /pps/)) { print DETAILS_CFG "    sort +packets\n"; }
		elsif (($detail_lines < 0) && ($graph_type =~ /pps/)) { print DETAILS_CFG "    sort -packets\n"; }
		print DETAILS_CFG "    records $detail_lines_abs\n";
		print DETAILS_CFG "\n";
		print DETAILS_CFG "stat-definition DETAILS\n";
		print DETAILS_CFG "  filter Flow_Filter\n";
		print DETAILS_CFG "  report details\n";
		close(DETAILS_CFG);

		time_check("start details_Linear");
		$flowdetails_command  = "$flow_bin_directory/flow-report -s$details_cfg -SDETAILS < $work_directory/FG_buckets_cat_$suffix > $work_directory/FlowGrapher_details_$suffix";
		if ($debug_grapher eq "Y") { print DEBUG "$flowdetails_command\n"; }
		system($flowdetails_command);
		time_check("end run_Linear");

	} else {

		# Examine each flow individually, run the flow-print command
	     
		time_check("start run_Prorated");
		$flow_print_option = 5;
		$flowprint_command = "$flow_bin_directory/flow-print -f$flow_print_option >$work_directory/FlowGrapher_output_$suffix";
		$flow_run = "$flowcat_command | $flownfilter_command | $flowprint_command"; 
		system ($flow_run); 
		time_check("end run_Prorated");
		if ($debug_grapher eq "Y") { print DEBUG "$flow_run\n"; }
	}

} else { 

	if (($graph_type eq "bps") || ($graph_type eq "pps") || ($graph_type eq "fpsi")) { $LINEAR = 1; }

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
	if ($silk_rootdir ne "")  { $selection_switches  = "--data-rootdir=$silk_rootdir "; }
	if ($silk_class ne "")    { $selection_switches .= "--class=$silk_class "; }
	if ($silk_flowtype ne "") { $selection_switches .= "--flowtype=$silk_flowtype "; }
	if ($silk_type ne "")     { $selection_switches .= "--type=$silk_type "; }
	if ($silk_sensors ne "")  { $selection_switches .= "--sensors=$silk_sensors "; }
	if ($silk_switches ne "") { $selection_switches .= "$silk_switches "; }

	$silk_info_out = $selection_switches;

        # Prepare rwfilter start and end time parameters

        $time_window = $silk_period_start ."-". $silk_period_end;

	if ($flow_select eq 1) { $window_type = "--active"; }
	if ($flow_select eq 2) { $window_type = "--etime"; }
	if ($flow_select eq 3) { $window_type = "--stime"; }
	if ($flow_select eq 4) { $window_type = "--stime"; }

	$selection_switches .= "--start-date=$silk_cat_start --end-date=$silk_cat_end $window_type=$time_window ";

	create_ipfix_filter(%FORM);

	# Use SiLK rwfilter to create the filtered file

	if ($debug_grapher eq "Y") { print DEBUG "   selection_switches: $selection_switches\n"; }
	if ($debug_grapher eq "Y") { print DEBUG "partitioning_switches:$partitioning_switches\n"; }

	$prefiltered_file = "$work_directory/FlowGrapher_filtered_$suffix";
	$rwfilter_command = "$silk_bin_directory/rwfilter $site_config_modifier $selection_switches $partitioning_switches --pass=$prefiltered_file";
	time_check("start filter_SiLK");
	system($rwfilter_command);

	if ($debug_grapher eq "Y") { print DEBUG "rwfilter_command: $rwfilter_command\n"; }

	# Use SiLK linear method (rwcount) unless setting up for Analysis (rwcut)

	if ($LINEAR) {

		if (($graph_type eq "bps") || ($graph_type eq "pps")) {
			$rwcount_command = "$silk_bin_directory/rwcount $site_config_modifier --bin-size=$bucket_size --start-time=$silk_period_start --epoch-slots $prefiltered_file";
			$silk_command    = "$rwcount_command > $work_directory/FlowGrapher_output_$suffix";
		} elsif ($graph_type eq "fpsi") {
			$rwcount_command = "$silk_bin_directory/rwcount $site_config_modifier --bin-size=$bucket_size --start-time=$silk_period_start --epoch-slots --load-scheme=$silk_init_loadscheme $prefiltered_file";
			$silk_command    = "$rwcount_command > $work_directory/FlowGrapher_output_$suffix";
		} else {
			$rwcount_command = "$silk_bin_directory/rwcount $site_config_modifier --bin-size=$bucket_size --start-time=$silk_period_start --epoch-slots --load-scheme=$silk_active_loadscheme $prefiltered_file";
			$silk_command    = "$rwcount_command > $work_directory/FlowGrapher_output_$suffix";
		}

	} else {

	        $field_sequence = "22,23,10,13,1,3,14,2,4,5,8,6,7";
	        $rwcut_command  = "$silk_bin_directory/rwcut $site_config_modifier --fields=$field_sequence $prefiltered_file";
	        $silk_command   = "$rwcut_command > $work_directory/FlowGrapher_output_$suffix";
	}

	time_check("start rwcount_SiLK");
	if ($debug_grapher eq "Y") { print DEBUG "silk_command: $silk_command\n"; }
	system ($silk_command); 
}

# Collect data into buckets to form the plot for the graph

if ($IPFIX && $LINEAR) {

	time_check("start report_SiLK");
	$bucket_num = 0;

	open (BUCKETS,"<$work_directory/FlowGrapher_output_$suffix");
	while (<BUCKETS>) {

		$silk_record = $_;
		$silk_record =~ s/\s+//g;
		($bucket_start,$num_recs,$num_bytes,$num_pkts) = split(/\|/,$silk_record);

		if (($bucket_start < $start_epoch) || ($bucket_start >= $end_epoch)) { next; }

	        if ($graph_type eq "pps") {
	        	$value = $num_pkts;
	        } elsif ($graph_type =~ /fps/) {
	                $value = $num_recs;
	        } else {
	                $value = $num_bytes * 8;
	        }
 
        	if ($sampling_multiplier > 1) { $value *= $sampling_multiplier; }

		$buckets[$bucket_num] = $value;
		$bucket_num++;
	}
	close BUCKETS;
	$rm_command = "rm $work_directory/FlowGrapher_output_$suffix";
	system($rm_command);

        # Prepare rwsort and rwcut commands

	if ($graph_type eq "pps") {
		if ($detail_lines > 0) {
			$rwsort_command = "$silk_bin_directory/rwsort $site_config_modifier --fields=6 --reverse $prefiltered_file";
		} else {
			$rwsort_command = "$silk_bin_directory/rwsort $site_config_modifier --fields=6 $prefiltered_file";
		}
	} else {
		if ($detail_lines > 0) {
			$rwsort_command = "$silk_bin_directory/rwsort $site_config_modifier --fields=7 --reverse $prefiltered_file";
		} else {
			$rwsort_command = "$silk_bin_directory/rwsort $site_config_modifier --fields=7 $prefiltered_file";
		}
	}

	$detail_lines_abs = abs($detail_lines);
        $field_sequence = "22,23,10,13,1,3,14,2,4,5,8,6,7";
        $rwcut_command = "$silk_bin_directory/rwcut $site_config_modifier --fields=$field_sequence --num-recs=$detail_lines_abs";

        $silk_command = "$rwsort_command | $rwcut_command > $work_directory/FlowGrapher_output_$suffix";
	time_check("start rwcut_SiLK");
	system ($silk_command); 

	# Prepare Detail lines for SiLK runs

	time_check("start records_SiLK");
	open (FLOWS,"<$work_directory/FlowGrapher_output_$suffix");
	while (<FLOWS>) {

		if (/Time/) { next; }

		$silk_record = $_;
		$silk_record =~ s/\s+//g;
        	($s_time,$e_time,$dur,$sif,$sip,$sp,$dif,$dip,$dp,$p,$fl,$pkt,$oct) = split(/\|/,$silk_record);

	        if ($graph_type eq "pps") {
	        	$value = $pkt;
	        } else {
	                $value = $oct * 8;
	        }
 
        	if ($sampling_multiplier > 1) { $value *= $sampling_multiplier; }

		$len_value = length($value);
		$detail_line_key = $value;
		for ($i=$len_value;$i<22;$i++) {
			$detail_line_key = "0" . $detail_line_key;
		}

		($s_dy,$s_tm)   = split(/T/,$s_time);
		($yr,$mon,$day) = split(/\//,$s_dy);
		$smd            = $mon . $day;
		$s_dy           = $mon ."/". $day ."/". $yr;
		($s_tm,$s_ms)   = split(/\./,$s_tm);
		$s_epoch        = date_to_epoch($s_dy,$s_tm,"LOCAL");

		($e_dy,$e_tm) = split(/T/,$e_time);
		($yr,$mon,$day) = split(/\//,$e_dy);
		$emd            = $mon . $day;
		($e_tm,$e_ms) = split(/\./,$e_tm);

		$smdtm = $smd .":". $s_tm;	
		$emdtm = $emd .":". $e_tm;	
        	$big_flow = $detail_line_key ."&". $s_epoch .";". $smdtm .";". $emdtm .";". $sip .";". $sp .";". $dip .";". $dp ."&". $value ."&". $dur;
		push(@biggest_flows,$big_flow);
	}

} elsif (!$IPFIX && $LINEAR) {

	time_check("start buckets_Linear");
	open (BUCKETS,"<$work_directory/FlowGrapher_buckets_$suffix");
	while (<BUCKETS>) {
	
	        if (substr($_,0,6) eq "# recn") { $start_data = 1; next; } if (!$start_data) { next; }
		($unix_secs,$fl,$oct,$pkt) = split(/,/);

		if (($unix_secs < $start_epoch) || ($unix_secs > $end_epoch)) { next; }
	        if ($sampling_multiplier > 1) {
	                $oct    *= $sampling_multiplier;
	                $fl     *= $sampling_multiplier;
	                $pkt    *= $sampling_multiplier;
	        }
	
	        if ($graph_type eq "pps") {
	                $flow_bits = $pkt;
	        } elsif ($graph_type =~ /fps/) {
	                $flow_bits = $fl;
	        } else {
	                $flow_bits = $oct * 8;
	        }
	
		$bucket_second = $unix_secs - $start_epoch;
		$bucket_index = int($bucket_second / $bucket_size);
		$buckets[$bucket_index] += $flow_bits;
	}
	close BUCKETS;

} else {

	# Determine if user wants to prepare for Analysis

	if (($graph_type eq "bpsa") || ($graph_type eq "ppsa") || ($graph_type eq "fpsia") || ($graph_type eq "fpsaa")) { $ANALYSIS = 1; }

	time_check("start records_Examine");
	open (FLOWS,"<$work_directory/FlowGrapher_output_$suffix");
	while (<FLOWS>) {
	
	        $first_char = substr($_,0,1);
	        if (!($first_char =~ /[0-9]/)) { next; }
	
	        if ($IPFIX) {
	                $silk_record = $_;
	                $silk_record =~ s/\s+//g;
	                ($s_time,$e_time,$dur,$sif,$sip,$sp,$dif,$dip,$dp,$p,$fl,$pkt,$oct) = split(/\|/,$silk_record);
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
	
		if ($ANALYSIS) {

			if (($obs_included % $analyze_peak_width) == 0) {

				$enough_obs = 1;

				# Update Host (IP Address) Analysis leaders

				@src_count_keys = sort { $src_peak_count{$b} <=> $src_peak_count{$a} } keys %src_peak_count;
				foreach $peak_host (@src_count_keys) {
					if ($src_peak_count{$peak_host} > $current_src_low) {
						if ($src_peak_count{$peak_host} > $src_peak_hosts{$peak_host}) {
							$src_peak_hosts{$peak_host} = $src_peak_count{$peak_host};
						}
					} else {
						last;
					}
				}
				%src_peak_count = ();

				$host_count = 0;
				@src_host_keys = sort { $src_peak_hosts{$b} <=> $src_peak_hosts{$a} } keys %src_peak_hosts;
				foreach $peak_host (@src_host_keys) {
					$host_count++;
					if ($host_count < $analyze_count) {
						next;
					} elsif ($host_count == $analyze_count) {
						$current_src_low = $src_peak_hosts{$peak_host};
						next;
					}
					delete $src_peak_hosts{$peak_host};
				}
					
				@dst_count_keys = sort { $dst_peak_count{$b} <=> $dst_peak_count{$a} } keys %dst_peak_count;
				foreach $peak_host (@dst_count_keys) {
					if ($dst_peak_count{$peak_host} > $current_dst_low) {
						if ($dst_peak_count{$peak_host} > $dst_peak_hosts{$peak_host}) {
							$dst_peak_hosts{$peak_host} = $dst_peak_count{$peak_host};
						}
					} else {
						last;
					}
				}
				%dst_peak_count = ();

				$host_count = 0;
				@dst_host_keys = sort { $dst_peak_hosts{$b} <=> $dst_peak_hosts{$a} } keys %dst_peak_hosts;
				foreach $peak_host (@dst_host_keys) {
					$host_count++;
					if ($host_count < $analyze_count) {
						next;
					} elsif ($host_count == $analyze_count) {
						$current_dst_low = $dst_peak_hosts{$peak_host};
						next;
					}
					delete $dst_peak_hosts{$peak_host};
				}
	
				# Update Port Analysis leaders

				@spt_count_keys = sort { $spt_peak_count{$b} <=> $spt_peak_count{$a} } keys %spt_peak_count;
				foreach $peak_port (@spt_count_keys) {
					if ($spt_peak_count{$peak_port} > $current_spt_low) {
						if ($spt_peak_count{$peak_port} > $spt_peak_ports{$peak_port}) {
							$src_peak_ports{$peak_port} = $spt_peak_count{$peak_port};
						}
					} else {
						last;
					}
				}
				%spt_peak_count = ();

				$port_count = 0;
				@src_port_keys = sort { $src_peak_ports{$b} <=> $src_peak_ports{$a} } keys %src_peak_ports;
				foreach $peak_port (@src_port_keys) {
					$port_count++;
					if ($port_count < $analyze_count) {
						next;
					} elsif ($port_count == $analyze_count) {
						$current_spt_low = $src_peak_ports{$peak_port};
						next;
					}
					delete $src_peak_ports{$peak_port};
				}
					
				@dpt_count_keys = sort { $dpt_peak_count{$b} <=> $dpt_peak_count{$a} } keys %dpt_peak_count;
				foreach $peak_port (@dpt_count_keys) {
					if ($dpt_peak_count{$peak_port} > $current_dpt_low) {
						if ($dpt_peak_count{$peak_port} > $dst_peak_ports{$peak_port}) {
							$dst_peak_ports{$peak_port} = $dpt_peak_count{$peak_port};
						}
					} else {
						last;
					}
				}
				%dpt_peak_count = ();

				$port_count = 0;
				@dst_port_keys = sort { $dst_peak_ports{$b} <=> $dst_peak_ports{$a} } keys %dst_peak_ports;
				foreach $peak_port (@dst_port_keys) {
					$port_count++;
					if ($port_count < $analyze_count) {
						next;
					} elsif ($port_count == $analyze_count) {
						$current_dpt_low = $dst_peak_ports{$peak_port};
						next;
					}
					delete $dst_peak_ports{$peak_port};
				}
	
				$end_peak_period += ($analyze_peak_width * $bucket_size);
			}
		}

	        if ($flow_length_ms <= 0) { $flow_length_ms = 0.001; }
	        $flow_length = $flow_length_ms;
	
	        if ($graph_type =~ /pps/) {
	                $flow_bits = $pkt;
	        } elsif ($graph_type =~ /fpsa/) {
			if ($flow_length < 1) { $flow_length = 1; }
	                $flow_bits = $flow_length;
	        } elsif ($graph_type =~ /fpsi/) {
	                $flow_bits = 1;
	        } else {
	                $flow_bits = $oct * 8;
	        }
	
	        if ($sampling_multiplier > 1) { $flow_bits *= $sampling_multiplier; }

	        # Determine first, last, and total number of buckets spanned by flow
	
	        if ($start_delta <= 0) {
			$secs_in_first_bucket = 0;
	                $first_bucket = 0; }
	        else {
	                $first_bucket = int($start_delta / $bucket_size);
	                $secs_in_first_bucket = $bucket_size - ((($start_delta/$bucket_size) - $first_bucket) * $bucket_size);
	        }
	
	        if ($end_delta > $report_length) {
			$secs_in_last_bucket = 0;
	                $last_bucket = int($report_length / $bucket_size) - 1; }
	        else {
	                $last_bucket = int($end_delta / $bucket_size);
	                $secs_in_last_bucket = (($end_delta/$bucket_size) - $last_bucket) * $bucket_size;
	        }
	
	        if ($first_bucket > $last_bucket) { $first_bucket = $last_bucket; }
	        $num_buckets = $last_bucket - $first_bucket + 1;
	
	        # Determine bucket amount and accumulate into buckets, start with bits/second
	
	        $per_second_amount = $flow_bits / $flow_length;
	
	        if ($num_buckets == 1) {
                        if (($first_bucket == 0) && ($start_delta < 0)) {
				$buckets[$first_bucket] += $secs_in_last_bucket * $per_second_amount;
				$analysis_amount = $secs_in_last_bucket * $per_second_amount;
                        } elsif (($first_bucket eq $total_buckets) && ($end_delta > $report_length)) {
				$buckets[$first_bucket] += $secs_in_first_bucket * $per_second_amount;
				$analysis_amount = $secs_in_first_bucket * $per_second_amount;
                        } else {
				$buckets[$first_bucket] += $flow_bits;
				$analysis_amount = $flow_bits;
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
                                $buckets[$i] += $bucket_amount;
				$analysis_amount += $bucket_amount;
	                }
	        }
	
		if ($ANALYSIS) {
			$src_total_hosts{$sip} += $analysis_amount;
			$dst_total_hosts{$dip} += $analysis_amount;
			$src_total_ports{$sp}  += $analysis_amount;
			$dst_total_ports{$dp}  += $analysis_amount;
			$total_measured_total  += $analysis_amount;
			if ($graph_type =~ /fps/) {
				$src_peak_count{$sip}  += 1;
				$dst_peak_count{$dip}  += 1;
				$spt_peak_count{$sp}   += 1;
				$dpt_peak_count{$dp}   += 1;
				$total_measured_peak   += 1;
			} else {
				$src_peak_count{$sip}  += $analysis_amount;
				$dst_peak_count{$dip}  += $analysis_amount;
				$spt_peak_count{$sp}   += $analysis_amount;
				$dpt_peak_count{$dp}   += $analysis_amount;
				$total_measured_peak   += $analysis_amount;
			}
			$analysis_amount = 0;
		}

	        # Collect data for detail lines if turned on (detail lines > 0)
	
	        if ($detail_lines > 0) {
	
			# For Flows, for collecting the largest $detail_lines flows, return to bytes

			if ($graph_type =~ /fps/) {
				$flow_bits = $oct;
				if ($sampling_multiplier > 1) { $flow_bits *= $sampling_multiplier; }
			}

	                if ($num_bigs < $detail_lines) {
	
	                        $num_bigs++;
	                        if ($num_bigs == 1) { $smallest_flow = $flow_bits; }
	
	                        $len_flow_bits = length($flow_bits);
	                        $detail_line_key = $flow_bits;
	                        for ($i=$len_flow_bits;$i<22;$i++) {
	                                $detail_line_key = "0" . $detail_line_key;
	                        }
	
				$smdtm = $smd .":". $s_tm;	
				$emdtm = $emd .":". $e_tm;	
	                        $big_flow = $detail_line_key ."&". $s_epoch .";". $smdtm .";". $emdtm .";". $sip .";". $sp .";". $dip .";". $dp ."&". $flow_bits ."&". $flow_length_ms;
	                        push(@biggest_flows,$big_flow);
	
	                        if ($flow_bits < $smallest_flow) { $smallest_flow = $flow_bits; } }
	
	                elsif ($flow_bits > $smallest_flow) {
	
	                        $len_flow_bits = length($flow_bits);
	                        $detail_line_key = $flow_bits;
	                        for ($i=$len_flow_bits;$i<22;$i++) {
	                                $detail_line_key = "0" . $detail_line_key;
	                        }
	
				$smdtm = $smd .":". $s_tm;	
				$emdtm = $emd .":". $e_tm;	
	                        $big_flow = $detail_line_key ."&". $s_epoch .";". $smdtm .";". $emdtm .";". $sip .";". $sp .";". $dip .";". $dp ."&". $flow_bits ."&". $flow_length_ms;
	
	                        shift(@biggest_flows);
	                        push(@biggest_flows,$big_flow);
	                        @biggest_flows = sort(@biggest_flows);
	                        $smallest_flow = substr($biggest_flows[0],0,22);
	                }

	        } elsif ($detail_lines < 0) {

			# For Flows, for collecting the smallest $detail_lines flows, return to bytes

			if ($graph_type =~ /fps/) {
				$flow_bits = $oct;
				if ($sampling_multiplier > 1) { $flow_bits *= $sampling_multiplier; }
			}

	                if ($num_smalls > $detail_lines) {
	
	                        $num_smalls--;
	                        if ($num_smalls == -1) { $biggest_flow = $flow_bits; }
	
	                        $len_flow_bits = length($flow_bits);
	                        $detail_line_key = $flow_bits;
	                        for ($i=$len_flow_bits;$i<22;$i++) {
	                                $detail_line_key = "0" . $detail_line_key;
	                        }
	
				$smdtm = $smd .":". $s_tm;	
				$emdtm = $emd .":". $e_tm;	
	                        $big_flow = $detail_line_key ."&". $s_epoch .";". $smdtm .";". $emdtm .";". $sip .";". $sp .";". $dip .";". $dp ."&". $flow_bits ."&". $flow_length_ms;
	                        push(@biggest_flows,$big_flow);
	
	                        if ($flow_bits > $biggest_flow) { $biggest_flow = $flow_bits; } }
	
	                elsif ($flow_bits < $biggest_flow) {
	
	                        $len_flow_bits = length($flow_bits);
	                        $detail_line_key = $flow_bits;
	                        for ($i=$len_flow_bits;$i<22;$i++) {
	                                $detail_line_key = "0" . $detail_line_key;
	                        }
	
				$smdtm = $smd .":". $s_tm;	
				$emdtm = $emd .":". $e_tm;	
	                        $big_flow = $detail_line_key ."&". $s_epoch .";". $smdtm .";". $emdtm .";". $sip .";". $sp .";". $dip .";". $dp ."&". $flow_bits ."&". $flow_length_ms;
	
	                        push(@biggest_flows,$big_flow);
	                        @biggest_flows = sort(@biggest_flows);
	                        $biggest_flow = pop(@biggest_flows);
	                }
		}
	}

	if (!$enough_obs) {

		@src_count_keys = sort { $src_peak_count{$b} <=> $src_peak_count{$a} } keys %src_peak_count;
		$host_count = 0;
		foreach $peak_host (@src_count_keys) { 
			$host_count++;
			$src_peak_hosts{$peak_host} = $src_peak_count{$peak_host};
			if ($host_count == $analyze_count) { last; }
		}

		@dst_count_keys = sort { $dst_peak_count{$b} <=> $dst_peak_count{$a} } keys %dst_peak_count;
		$host_count = 0;
		foreach $peak_host (@dst_count_keys) { 
			$host_count++;
			$dst_peak_hosts{$peak_host} = $dst_peak_count{$peak_host};
			if ($host_count == $analyze_count) { last; }
		}

		@spt_count_keys = sort { $spt_peak_count{$b} <=> $spt_peak_count{$a} } keys %spt_peak_count;
		$port_count = 0;
		foreach $peak_port (@spt_count_keys) { 
			$port_count++;
			$src_peak_ports{$peak_port} = $spt_peak_count{$peak_port};
			if ($port_count == $analyze_count) { last; }
		}

		@dpt_count_keys = sort { $dpt_peak_count{$b} <=> $dpt_peak_count{$a} } keys %dpt_peak_count;
		$port_count = 0;
		foreach $peak_port (@dpt_count_keys) { 
			$port_count++;
			$dst_peak_ports{$peak_port} = $dpt_peak_count{$peak_port};
			if ($port_count == $analyze_count) { last; }
		}
	}
}

if ($debug_grapher eq "Y") {
	print DEBUG "looked at: $obs flows\n";
	print DEBUG "   passed: $obs_included flows\n";
}

time_check("done_FLOWS");
close FLOWS;
 
# Determine the statistics and graphing times
 
$total_graph_times = $report_length / $bucket_size;
$skip_graph_times  = $total_graph_times / 8;
$stats_pct         = 100.0;
$stats_min         = 1000000000000;
 
for ($i=0;$i<$total_graph_times;$i++) {

	if ($buckets[$i] eq "") { $buckets[$i] = 0; }

        $buckets[$i] = $buckets[$i] / $bucket_size;

	if ($stats_method eq "Nonzeroes") {
		if ($buckets[$i] > 0) {
			$nonzero_buckets++;
			$nonzero_total += $buckets[$i];
			$stats_avg = int ($nonzero_total / $nonzero_buckets);
			if ($buckets[$i] > $stats_max) { $stats_max = int($buckets[$i]); }
			if ($buckets[$i] < $stats_min) { $stats_min = int($buckets[$i]); if ($stats_min == 0) { $stats_min = 1; } }
		}
	} else {
		$stats_total += $buckets[$i];
		$stats_avg = int ($stats_total / ($i+1));
		if ($buckets[$i] > $stats_max) { $stats_max = int($buckets[$i]); }
		if ($buckets[$i] < $stats_min) { $stats_min = int($buckets[$i]); }
	}

        $graph_labels[$i] = "";
        if (($i % $skip_graph_times) == 0) {
                $bucket_time = $start_epoch + ($i * $bucket_size);
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
$total_measured_total = int ($total_measured_total + 0.5);
$total_measured_peak  = int ($total_measured_peak  + 0.5);

if ($use_bucket_endtime) {
	unshift(@buckets,0);
	$bucket_size = "300E";
	$FORM{'bucket_size'} = "300E";
}

$bucket_time = $end_epoch; 
$bucket_time_d = epoch_to_date($bucket_time,$time_zone);
($bucket_date,$bucket_hms) = split(/ /,$bucket_time_d); 
$graph_labels[$total_graph_times] = $bucket_hms;
push (@graph_labels," ");
 
# Create the plot ...
 
@plot = ([@graph_labels],[@buckets]);
 
# Create the graph ...
 
$horizontal  = "Time: $time_zone";

if ($graph_type =~ /bps/) { $vertical = "Bits/Second"; }
if ($graph_type =~ /pps/) { $vertical = "Packets/Second"; }
if ($graph_type =~ /fps/) { $vertical = "Flows/Second"; }

if ($device_name) {
	$legend      = "Flow data from $device_name";
	$description = "Flow data from $device_name";
} elsif ($exporter) {
	foreach (@exporters) {
		($exporter_ip, $exporter_name) = split(/:/,$_);
		if ($exporter_ip eq $exporter) {
		        $legend      = "Flow data from $exporter_name";
		        $description = "Flow data from $exporter_name";
		        last;
		}
	}
}
$x_ticks     = 1;
$long_ticks  = 1;
 
$graph_width *= $graph_multiplier;
$graph = GD::Graph::mixed->new($graph_width,$graph_height);

$graph->set(
        boxclr               => "$boxclr",
        bgclr                => "$bgclr",
        transparent          => "$transparent",
        borderclrs           => "$borderclrs",
        fgclr                => "$fgclr",
        labelclr             => "$labelclr",
        axislabelclr         => "$axislabelclr",
        legendclr            => "$legendclr",
        valuesclr            => "$valuesclr",
        textclr              => "$textclr",
        dclrs                => ['pale orange','pale brown','dark red','pale blue','pale yellow'],
        types                => ['area','lines'],
        line_width           => "2",
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
        legend_placement     => "BL",
        legend_marker_width  => "24",
        legend_marker_height => "4"
        ) or warn $graph->error;
 
$graph->set_legend($legend);
$graph->set_x_axis_font($x_axis_font);
 
# Create the image and write it to the correct directory

$image = $graph->plot(\@plot) or die $graph->error;

@sorted_buckets = sort by_number (@buckets);

if ($stats_method eq "Nonzeroes") {
	$index_95 = int (0.95 * $nonzero_buckets);
	$stats_pct = int ($sorted_buckets[($total_graph_times-($nonzero_buckets-$index_95))]);
} else {
	$index_95 = int (0.95 * $total_graph_times);
	$stats_pct = int ($sorted_buckets[$index_95]);
}

if ($stats_max eq "") { $stats_pct = ""; $stats_min = ""; $stats_avg = ""; }

$stats_max = format_number($stats_max);
$stats_pct = format_number($stats_pct);
$stats_avg = format_number($stats_avg);
$stats_min = format_number($stats_min);

$stats_max_out = "Maximum  : $stats_max"; 
$stats_pct_out = "95th Pct.: $stats_pct"; 
$stats_avg_out = "Average  : $stats_avg"; 
$stats_min_out = "Minimum  : $stats_min"; 

if ($stats_method eq "Nonzeroes") { $stats_method_out = "[Non-zero values only]"; }
if ($stats_method eq "All")       { $stats_method_out = "[Zero and Non-zero values]"; }

$font_color = $image->colorAllocate(0,0,0); 
$image->string(gdSmallFont,$horz_max,$vert_max,$stats_max_out,$font_color);
$image->string(gdSmallFont,$horz_pct,$vert_pct,$stats_pct_out,$font_color);
$image->string(gdSmallFont,$horz_avg,$vert_avg,$stats_avg_out,$font_color);
$image->string(gdSmallFont,$horz_min,$vert_min,$stats_min_out,$font_color);
$image->string(gdTinyFont,$horz_mth,$vert_pct,$stats_method_out,$font_color);

$png_filename  = "FlowGrapher_save_" . $suffix . ".png";
$flowgraph_link = "$graphs_short/$png_filename";

time_check("create_graph");

open(PNG,">$graphs_directory/$png_filename");
binmode PNG;
print PNG $image->png;
close PNG;
 
# Create the FlowGrapher Content

&create_filter_output("FlowGrapher_Main",$filter_hash);

print " <br>\n";
print " <center><img src=$flowgraph_link></center>\n";

# Print out details if they have been requested

if ($ANALYSIS) {
	time_check("prior sorts");
	@src_total_keys = sort { $src_total_hosts{$b} <=> $src_total_hosts{$a} } keys %src_total_hosts;
	@dst_total_keys = sort { $dst_total_hosts{$b} <=> $dst_total_hosts{$a} } keys %dst_total_hosts;
	@src_peak_keys  = sort { $src_peak_hosts{$a}  <=> $src_peak_hosts{$b}  } keys %src_peak_hosts;
	@dst_peak_keys  = sort { $dst_peak_hosts{$a}  <=> $dst_peak_hosts{$b}  } keys %dst_peak_hosts;

	@spt_total_keys = sort { $src_total_ports{$b} <=> $src_total_ports{$a} } keys %src_total_ports;
	@dpt_total_keys = sort { $dst_total_ports{$b} <=> $dst_total_ports{$a} } keys %dst_total_ports;
	@spt_peak_keys  = sort { $src_peak_ports{$a}  <=> $src_peak_ports{$b}  } keys %src_peak_ports;
	@dpt_peak_keys  = sort { $dst_peak_ports{$a}  <=> $dst_peak_ports{$b}  } keys %dst_peak_ports;
	time_check("after sorts");
}

if (($detail_lines != 0) && !$IPFIX && $LINEAR) {

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
 
        $dns_column_widths    = $dns_column_width . "s";
        $dns_column_widthss   = $dns_column_width .".". $dns_column_width ."s";

	# Copy Detail Lines to temporary file, for potential user requested sort or eventual saving

	$sort_file = "$work_directory/FlowGrapher_save_" . $suffix;
        open (SORT, ">$sort_file");    
	&start_saved_file($sort_file);
        open (SORT, ">>$sort_file");    

	if ($ANALYSIS) {
		print SORT "<BEGIN ANALYSIS HOSTS -->\n";
		$host_count = 0;
		foreach $sip (@src_total_keys) {
			$sip_total = int($src_total_hosts{$sip} + 0.5);
			printf SORT "total-src_$host_count: $sip $sip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$host_count = 0;
		foreach $dip (@dst_total_keys) {
			$dip_total = int($dst_total_hosts{$dip} + 0.5);
			printf SORT "total-dst_$host_count: $dip $dip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$host_count = 0;
		foreach $sip (@src_peak_keys) {
			$sip_total = int($src_peak_hosts{$sip} + 0.5);
			printf SORT "peak-src_$host_count: $sip $sip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$host_count = 0;
		foreach $dip (@dst_peak_keys) {
			$dip_total = int($dst_peak_hosts{$dip} + 0.5);
			printf SORT "peak-dst_$host_count: $dip $dip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $sport (@spt_total_keys) {
			$sport_total = int($src_total_ports{$sport} + 0.5);
			printf SORT "total-spt_$port_count: $sport $sport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $dport (@dpt_total_keys) {
			$dport_total = int($dst_total_ports{$dport} + 0.5);
			printf SORT "total-dpt_$port_count: $dport $dport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $sport (@spt_peak_keys) {
			$sport_total = int($src_peak_ports{$sport} + 0.5);
			printf SORT "peak-spt_$port_count: $sport $sport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $dport (@dpt_peak_keys) {
			$dport_total = int($dst_peak_ports{$dport} + 0.5);
			printf SORT "peak-dpt_$port_count: $dport $dport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		printf SORT "total-measured_total: $total_measured_total\n";
		printf SORT "total-measured_peak: $total_measured_peak\n";
		print SORT "<END ANALYSIS HOSTS -->\n";
	}

	# Create column headers with sort links

	$dur_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dur^$next_index>Duration</a>";
	$source_link = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Source^$next_index>Source Host</a>";
	$sport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Sport^$next_index>S Port</a>";
	$dest_link   = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dest^$next_index>Destination Host</a>";
	$dport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dport^$next_index>D Port</a>";
	$flows_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Flows^$next_index>$flows_txt</a>";
	$bytes_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Bytes^$next_index>$bytes_txt</a>";
	$pckts_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Pckts^$next_index>$pckts_txt</a>";
	$agg_rate    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^aRate^$next_index>$ambps_txt</a>";

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
	
	open (DETAILS,"<$work_directory/FlowGrapher_details_$suffix");
	while (<DETAILS>) {

		chop;
		if (substr($_,0,1) eq "#") { next; }

		($indx,$str_secs,$end_secs,$sip,$dip,$sp,$dp,$fl,$oct,$pkt,$dur) = split(/,/);
	
	        if ($sampling_multiplier > 1) { 
			$fl  *= $sampling_multiplier;
			$oct *= $sampling_multiplier;
			$pkt *= $sampling_multiplier;
		}

		if ($dur == 0) { $dur = 1; }
		$dur = $dur/1000;
		$dur = sprintf("%10.3f",$dur);

		$agg_rate = $oct * 8 / $dur / 1000000;
		$agg_rate = sprintf("%10.3f",$agg_rate);

		$formatted_flows = format_number($fl);
		$formatted_bytes = format_number($oct);
		$formatted_pckts = format_number($pkt);
	
		if ($resolve_addresses eq "Y") {
			$sip = dig($sip);
			$dip = dig($dip);
		}

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
		print "<td align=right>$formatted_flows</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$formatted_bytes</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$formatted_pckts</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$agg_rate</td>\n";
		print "</tr>\n";
	
		# Print to Save/Sort file
	
		printf SORT "%-12s  %10.3f  %-$dns_column_widthss  %-6s   %-$dns_column_widthss  %-6s  %8s %15s %11s  %8.3f\n", $indx, $dur, $sip, $sp, $dip, $dp, $formatted_flows, $formatted_bytes, $formatted_pckts, $agg_rate;

	}
}

if (($detail_lines != 0) && (!$LINEAR || $IPFIX)) {

	# Sort on start time (after eliminating the first 22 bytes which were used to find biggest flows)

	foreach $big_flow (@biggest_flows) {
		$big_flow = substr($big_flow,23,260);
	}
	@biggest_flows = sort(@biggest_flows);

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
 
        $dns_column_widths    = $dns_column_width . "s";
        $dns_column_widthss   = $dns_column_width .".". $dns_column_width ."s";

	# Copy Detail Lines to temporary file, for potential user requested sort or eventual saving

	$sort_file = "$work_directory/FlowGrapher_save_" . $suffix;
        open (SORT, ">$sort_file");    
	&start_saved_file($sort_file);
        open (SORT, ">>$sort_file");    

	if ($ANALYSIS) {
		print SORT "<BEGIN ANALYSIS HOSTS -->\n";
		$host_count = 0;
		foreach $sip (@src_total_keys) {
			$sip_total = int($src_total_hosts{$sip} + 0.5);
			printf SORT "total-src_$host_count: $sip $sip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$host_count = 0;
		foreach $dip (@dst_total_keys) {
			$dip_total = int($dst_total_hosts{$dip} + 0.5);
			printf SORT "total-dst_$host_count: $dip $dip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$host_count = 0;
		foreach $sip (@src_peak_keys) {
			$sip_total = int($src_peak_hosts{$sip} + 0.5);
			printf SORT "peak-src_$host_count: $sip $sip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$host_count = 0;
		foreach $dip (@dst_peak_keys) {
			$dip_total = int($dst_peak_hosts{$dip} + 0.5);
			printf SORT "peak-dst_$host_count: $dip $dip_total\n";
			$host_count++; if ($host_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $sport (@spt_total_keys) {
			$sport_total = int($src_total_ports{$sport} + 0.5);
			printf SORT "total-spt_$port_count: $sport $sport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $dport (@dpt_total_keys) {
			$dport_total = int($dst_total_ports{$dport} + 0.5);
			printf SORT "total-dpt_$port_count: $dport $dport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $sport (@spt_peak_keys) {
			$sport_total = int($src_peak_ports{$sport} + 0.5);
			printf SORT "peak-spt_$port_count: $sport $sport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		$port_count = 0;
		foreach $dport (@dpt_peak_keys) {
			$dport_total = int($dst_peak_ports{$dport} + 0.5);
			printf SORT "peak-dpt_$port_count: $dport $dport_total\n";
			$port_count++; if ($port_count == $analyze_count) { last; }
		}
		printf SORT "total-measured_total: $total_measured_total\n";
		printf SORT "total-measured_peak: $total_measured_peak\n";
		print SORT "<END ANALYSIS HOSTS -->\n";
	}

	# Create column headers with sort links

	$start_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Start^1>Start</a>";
	$end_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^End^1>End</a>";
	$len_link    = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Len^0>Len</a>";
	$source_link = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Source^0>Source Host</a>";
	$sport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Sport^0>S Port</a>";
	$dest_link   = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dest^0>Destination Host</a>";
	$dport_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Dport^0>D Port</a>";
	$bytes_link  = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Bytes^0>$totals_txt</a>";
	$mbps_link   = "<a href=$cgi_bin_short/FlowGrapher_Sort.cgi?$active_dashboard^$filter_hash^Mbps^0>$ps_txt</a>";

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

	$detail_lines_abs = abs($detail_lines);
	for ($m=0;$m<=$detail_lines_abs;$m++) {

		if ($biggest_flows[$m] eq "") { next; }
		($big_flow_key,$big_flow_bits,$big_flow_length_ms) = split(/&/,$biggest_flows[$m]);
		($s_epoch,$s_tm,$e_tm,$sip,$sp,$dip,$dp) = split(/;/,$big_flow_key);

		$big_flow_length = $big_flow_length_ms;
		$big_flow_length_ms = sprintf("%-8.1f",$big_flow_length_ms);
		if ($big_flow_length < 1) { $big_flow_length = 1; }

		if ($graph_type =~ /pps/) {
                	$formatted_bytes = format_number($big_flow_bits);
			$big_flow_rate = ($big_flow_bits / $big_flow_length) / 1000;
			$big_flow_rate = sprintf("%10.3f",$big_flow_rate);
		} else {
			$big_flow_bytes = int ($big_flow_bits / 8);
			$formatted_bytes = format_number($big_flow_bytes);
			$big_flow_rate = ($big_flow_bits / $big_flow_length) / 1000000;
			$big_flow_rate = sprintf("%10.3f",$big_flow_rate);
		}

		if ($resolve_addresses eq "Y") {
			$sip = dig($sip);
			$dip = dig($dip);
		}

		# Modify detail line flow times for the situation where SiLK data is in UTC but system time in non-UTC

		if ($IPFIX && ($silk_compiled_localtime ne "Y") && ($system_time eq "NON-UTC")) {

			($start_mn,$start_da,$start_yr) = split(/\//,$start_date);
			$flow_year = $start_yr;

			# Convert flow start time from UTC to LOCAL time:

			$temp_date = substr($s_tm,0,4);
			$temp_time = substr($s_tm,5,8);
			($temp_hr,$temp_min,$temp_sec) = split(/:/,$temp_time);
			$temp_mnth = substr($temp_date,0,2);
			$temp_day  = substr($temp_date,2,2);
			if (($start_mn eq "12") && ($temp_mnth < 6)) { $flow_year++; } 
			if (($start_mn eq "01") && ($temp_mnth > 6)) { $flow_year--; } 
			$s_epoch_gm = timegm($temp_sec,$temp_min,$temp_hr,$temp_day,$temp_mnth-1,$flow_year-1900);
			($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($s_epoch_gm);
			$mnth++;
			if (length($mnth) < 2) { $mnth = "0" . $mnth; }
			if (length($date) < 2) { $date = "0" . $date; }
			if (length($hr)   < 2) { $hr   = "0" . $hr;   }
			if (length($min)  < 2) { $min  = "0" . $min;  }
			if (length($sec)  < 2) { $sec  = "0" . $sec;  }
			$s_tm = $mnth . $date .":". $hr .":". $min .":". $sec;

			# Convert flow end time from UTC to LOCAL time:

			$temp_date = substr($e_tm,0,4);
			$temp_time = substr($e_tm,5,8);
			($temp_hr,$temp_min,$temp_sec) = split(/:/,$temp_time);
			$temp_mnth = substr($temp_date,0,2);
			$temp_day  = substr($temp_date,2,2);
			if (($start_mn eq "12") && ($temp_mnth < 6)) { $flow_year++; } 
			if (($start_mn eq "01") && ($temp_mnth > 6)) { $flow_year--; } 
			$e_epoch_gm = timegm($temp_sec,$temp_min,$temp_hr,$temp_day,$temp_mnth-1,$flow_year-1900);
			($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($e_epoch_gm);
			$mnth++;
			if (length($mnth) < 2) { $mnth = "0" . $mnth; }
			if (length($date) < 2) { $date = "0" . $date; }
			if (length($hr)   < 2) { $hr   = "0" . $hr;   }
			if (length($min)  < 2) { $min  = "0" . $min;  }
			if (length($sec)  < 2) { $sec  = "0" . $sec;  }
			$e_tm = $mnth . $date .":". $hr .":". $min .":". $sec;
		}

		if (($date_format eq "DMY") || ($date_format eq "DMY2")) {

			$flow_date = substr($s_tm,0,4);
			$flow_time = substr($s_tm,4,9);
			$flow_month = substr($flow_date,0,2);
			$flow_day = substr($flow_date,2,2);
			$s_tm_out = $flow_day . $flow_month . $flow_time;

			$flow_date = substr($e_tm,0,4);
			$flow_time = substr($e_tm,4,9);
			$flow_month = substr($flow_date,0,2);
			$flow_day = substr($flow_date,2,2);
			$e_tm_out = $flow_day . $flow_month . $flow_time;

		} else {
			$s_tm_out = $s_tm;
			$e_tm_out = $e_tm;
		}
	
		# Print to screen

		print "<tr>\n";
		print "<td align=left>$s_tm_out</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$e_tm_out</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$big_flow_length_ms</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$sip</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$sp</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=left>$dip</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$dp</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$formatted_bytes</td>\n";
		print "<td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
		print "<td align=right>$big_flow_rate</td>\n";
		print "</tr>\n";

		# Print to Save/Sort file

		printf SORT "%-12s %-9s %-9s %7.1f  %-$dns_column_widthss  %-6s   %-$dns_column_widthss  %-6s  %14s  %8.3f\n", $s_epoch, $s_tm_out, $e_tm_out, $big_flow_length_ms, $sip, $sp, $dip, $dp, $formatted_bytes, $big_flow_rate;

	}
}

print "<tr><td>&nbsp</td></tr>";
print "<tr><td>&nbsp</td></tr>";
print " </table>\n";
print " </div>\n";

close(SORT);

if ($ANALYSIS && !$LINEAR) {
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
	print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_report^$filter_hash\">\n";
	print "  <button class=links type=submit>Save Report</button>\n";
	print "  </form>\n";
	print " </div>\n";
} else {
	&create_UI_service("FlowGrapher_Main","service_bottom",$active_dashboard,$filter_hash);
}

&finish_the_page("FlowGrapher_Main");

# Remove temporary files

$rm_command = "/bin/rm $work_directory/FG_buckets_cat_$suffix";
if (($debug_files ne "Y") && !$ANALYSIS) { system($rm_command); }
$rm_command = "/bin/rm $work_directory/FlowGrapher_filter_$suffix"; 
if (($debug_files ne "Y") && !$ANALYSIS) { system($rm_command); }
$rm_command = "/bin/rm $work_directory/FlowGrapher_output_$suffix"; 
if (($debug_files ne "Y") && !$ANALYSIS) { system($rm_command); }
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
	print "  <br><br><br>";
	print "  $error_text\n";  
	print " </div>\n";
	&create_UI_service("FlowGrapher_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowGrapher_Main");
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
