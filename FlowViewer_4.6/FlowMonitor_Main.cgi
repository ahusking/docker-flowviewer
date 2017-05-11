#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_Main.cgi permits a Web user to analyze Net Flow data stored
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
#  J. Loiacono  02/14/2013      4.0     Fixed error when directories not created
#  J. Loiacono  07/14/2013      4.2     FlowMonitor was accepting SiLK excluded
#                                       capabilities (e.g., Protocols)
#  J. Loiacono  09/11/2013      4.2.1   Minor formatting changes
#                                       Mods for international date formatting
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards
#  J. Loiacono  11/02/2014      4.5     FlowTracker to FlowMonitor rename
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
use File::stat;

if ($debug_monitor eq "Y") { open (DEBUG,">>$work_directory/DEBUG_MONITOR"); }

# Retrieve parameters

($active_dashboard,$action,$monitor_label,$device_revision) = split(/\^/,$ENV{'QUERY_STRING'});
if ($action eq "Revise")  { $action = "Revise Monitor"; }
if ($device_revision ne "") { ($device_revision,$device_name_revision) = split(/=/,$device_revision); } chop($device_name_revision);
$monitor_label =~ s/~/ /g;

if ($debug_monitor eq "Y") { print DEBUG "In FlowMonitor_main.cgi action: $action\n"; }
if ($debug_monitor eq "Y") { print DEBUG "monitor_label: $monitor_label  device_revision: $device_revision\n"; }

read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
@pairs = split(/&/, $buffer);
foreach $pair (@pairs) {
    ($name, $value) = split(/=/, $pair);
    $value =~ tr/+/ /;
    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
    $FORM{$name} = $value;
}

# Clean up input 
      
($ft_link,$FORM{device_name}) = split(/DDD/,$FORM{device_name});
($ft_link,$FORM{exporter})    = split(/EEE/,$FORM{exporter});

$FORM{start_date}     =~ s/\s+//g; $FORM{start_date}     =~ s/,/, /g;   
$FORM{start_time}     =~ s/\s+//g; $FORM{start_time}     =~ s/,/, /g;   
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
$FORM{flow_select}    = 1;

# Determine if user is providing a start time to request a FlowMonitor_Recreate

if ($action ne "Revise Monitor") {
	
	open(DATE,"date 2>&1|");
	while (<DATE>) {
		($d_tz,$m_tz,$dt_tz,$t_tz,$time_zone,$y_tz) = split(/\s+/,$_);
	}

	# Convert into US date format for internal processing
	
	if    ($date_format eq "DMY")  { ($temp_day_s,$temp_mnth_s,$temp_yr_s) = split(/\//,$FORM{start_date}); }
	elsif ($date_format eq "DMY2") { ($temp_day_s,$temp_mnth_s,$temp_yr_s) = split(/\./,$FORM{start_date}); }
	elsif ($date_format eq "YMD")  { ($temp_yr_s,$temp_mnth_s,$temp_day_s) = split(/\-/,$FORM{start_date}); }
	else                           { ($temp_mnth_s,$temp_day_s,$temp_yr_s) = split(/\//,$FORM{start_date}); }

	$recreate_start = $temp_mnth_s ."/". $temp_day_s ."/". $temp_yr_s;
	
	if ($debug_monitor eq "Y") { print DEBUG "FORM{start_date}: $FORM{start_date}  start_date: $start_date  FORM{end_date}: $FORM{end_date}  end_date: $end_date\n"; }

	$start_epoch   = date_to_epoch($recreate_start,$FORM{start_time},$time_zone);
	$current_epoch = time - $start_offset;
	$delta_epoch   = $current_epoch - $start_epoch;
	
	if ($delta_epoch < 7200) {
		$FORM{'start_date'}   = "01/01/2000";
		$FORM{'start_time'}   = "00:00:00";
		$FORM{'end_date'}     = "01/01/2000";
		$FORM{'end_time'}     = "00:00:00";
	} else {
		$recreate = 1;
	}
} else {
	$FORM{'start_date'}   = "01/01/2000";
	$FORM{'start_time'}   = "00:00:00";
	$FORM{'end_date'}     = "01/01/2000";
	$FORM{'end_time'}     = "00:00:00";
}

# Parameters for generating a FlowMonitor report

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
$sampling_multiplier = $FORM{'sampling_multiplier'};
$monitor_label      = $FORM{'monitor_label'};
$monitor_type       = $FORM{'monitor_type'};
$general_comment     = $FORM{'general_comment'};
$alert_threshold     = $FORM{'alert_threshold'};
$alert_frequency     = $FORM{'alert_frequency'};
$alert_destination   = $FORM{'alert_destination'};
$revision_comment    = $FORM{'revision_comment'};
$notate_graphs       = $FORM{'notate_graphs'};
$silk_rootdir        = $FORM{'silk_rootdir'};
$silk_class          = $FORM{'silk_class'};
$silk_flowtype       = $FORM{'silk_flowtype'};
$silk_type           = $FORM{'silk_type'};
$silk_sensors        = $FORM{'silk_sensors'};
$silk_switches       = $FORM{'silk_switches'};

# Convert into US date format for internal processing

if    ($date_format eq "DMY")  { ($temp_day_s,$temp_mnth_s,$temp_yr_s) = split(/\//,$FORM{start_date}); }
elsif ($date_format eq "DMY2") { ($temp_day_s,$temp_mnth_s,$temp_yr_s) = split(/\./,$FORM{start_date}); }
elsif ($date_format eq "YMD")  { ($temp_yr_s,$temp_mnth_s,$temp_day_s) = split(/\-/,$FORM{start_date}); }
else                           { ($temp_mnth_s,$temp_day_s,$temp_yr_s) = split(/\//,$FORM{start_date}); }

$start_date = $temp_mnth_s ."/". $temp_day_s ."/". $temp_yr_s;
	
if ($debug_monitor eq "Y") { print DEBUG "FORM{start_date}: $FORM{start_date}  start_date: $start_date  FORM{end_date}: $FORM{end_date}  end_date: $end_date\n"; }

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

$filter_file    = $filter_directory  ."/". $monitor_file .".fil";
$group_file     = $filter_directory  ."/". $monitor_file .".grp";
$rrdtool_file   = $rrdtool_directory ."/". $monitor_file .".rrd";

$html_directory = $monitor_directory ."/". $monitor_file;
$html_file      = $html_directory ."/index.html";

if ($debug_monitor eq "Y") {
	print DEBUG " monitor_file: $monitor_file\n";
	print DEBUG " monitor_type: $monitor_type\n";
	print DEBUG "   filter_file: $filter_file\n";
	print DEBUG "    group_file: $group_file\n";
	print DEBUG "  rrdtool_file: $rrdtool_file\n";
	print DEBUG "html_directory: $html_directory\n";
	print DEBUG "     html_file: $html_file\n";
}
	
# Make the Filter directory if it doesn't exist

if (!-e $filter_directory) {

        mkdir $filter_directory, $filter_dir_perms || die "Cannot mkdir Monitor Filter Directory: $filter_directory: $!";
        chmod $filter_dir_perms, $filter_directory;

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
	print " <br>\n";
	print " <table>\n";
	print " <tr><td>The directory for storing Monitor Filter files has been created:</td></tr>\n";
	print " <tr><td></td></tr>\n";
	print " <tr><td><i>$filter_directory</i></td></tr>\n";
	print " <tr><td></td></tr>\n";
	print " <tr><td>Please ensure this directory has adequate permissions for your</td></tr>\n";
	print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";
	print " </table>\n";
	print " </div>\n";

	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");
	exit;
}

# Make the RRDtool directory if it doesn't exist

if (!-e $rrdtool_directory) {

        mkdir $rrdtool_directory, $rrd_dir_perms || die "Cannot mkdir Monitor RRDtool directory: $rrdtool_directory: $!";
        chmod $rrd_dir_perms, $rrdtool_directory;

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
	print " <br>\n";
	print " <table>\n";
	print " <tr><td>The directory for storing Monitor RRDtool files has been created:</td></tr>\n";
	print " <tr><td></td></tr>\n";
	print " <tr><td><i>$rrdtool_directory</i></td></tr>\n";
	print " <tr><td></td></tr>\n";
	print " <tr><td>Please ensure this directory has adequate permissions for your</td></tr>\n";
	print " <tr><td>web server process owner (e.g., 'apache') to write into it.</td></tr>\n";
	print " </table>\n";
	print " </div>\n";

	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");
}

if (($monitor_type ne "Group") && (($no_devices_or_exporters eq "N") && (($device_name eq "") && ($exporter eq "")))) {

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
	print " <span class=text16>FlowMonitor: $monitor_label</span>\n";
	print " <center>\n";
	print " <br><br>\n";
	print " <table>\n";
        print "  <tr><td colspan=2>Must select a device or an exporter. <p>Use the \"Back\" button to preserve inputs</td></tr>\n";
	print " </table>\n";
	print " </div>\n";

	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");
	exit;
}

# Determine if we are looking at an IPFIX device

$IPFIX = 0;
foreach $ipfix_device (@ipfix_devices) {
        if ($device_name eq $ipfix_device) { $IPFIX = 1; if ($debug_monitor eq "Y") { print DEBUG "This device is exporting IPFIX\n";} }
}

if ($action eq "Revise Monitor") {

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	print " <div id=content_scroll>\n";
	print "  <span class=text16>FlowMonitor: $monitor_label</span>\n";
	print "  <table>\n";
	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td width=500 align=left><font color=#CF7C29><b>Old Filtering Criteria:</b></font></td></tr>\n";
	print "  <tr><td>&nbsp</td></tr>\n";

        open  (OLD_FILTER,"<$filter_file");
        while (<OLD_FILTER>) {
                chop;
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        ($input,$field,$field_value) = split(/: /);
                        if ($field eq "revision") {
                                push (@revisions,$field_value);
                                ($old_notate_graphs,$old_revision_date,$old_revision_comment) = split(/\|/,$field_value);
				$revision_date_out = epoch_to_date($old_revision_date,"LOCAL");
                                $revision_date_out =~ s/\^/:/g;
                                print "  <tr><td align=left>revision: $old_notate_graphs | $revision_date_out | $old_revision_comment</td></tr>\n";
                        } else {
				s/input: //;
                                print "  <tr><td align=left>$_</td></tr>\n";
                        }
                }
        }
        close (OLD_FILTER);

        if ($IPFIX) {
                open (NEW_FILTER,">$filter_file") || die "cannot open Filter file for write: $filter_file";
        } else {
                create_filter_file (%FORM, $filter_file);
        }

        open (NEW_FILTER,">>$filter_file");
        print NEW_FILTER "\n\n";
        print NEW_FILTER " input: monitor_type: $monitor_type\n";
        print NEW_FILTER " input: device_name: $device_name\n";
        print NEW_FILTER " input: monitor_label: $monitor_label\n";
        print NEW_FILTER " input: general_comment: $general_comment\n";
        print NEW_FILTER " input: source_addresses: $source_addresses\n";
        print NEW_FILTER " input: source_ports: $source_ports\n";
        print NEW_FILTER " input: source_ifs: $source_ifs\n";
        print NEW_FILTER " input: sif_names: $sif_names\n";
        print NEW_FILTER " input: source_ases: $source_ases\n";
        print NEW_FILTER " input: dest_addresses: $dest_addresses\n";
        print NEW_FILTER " input: dest_ports: $dest_ports\n";
        print NEW_FILTER " input: dest_ifs: $dest_ifs\n";
        print NEW_FILTER " input: dif_names: $dif_names\n";
        print NEW_FILTER " input: dest_ases: $dest_ases\n";
        print NEW_FILTER " input: protocols: $protocols\n";
        print NEW_FILTER " input: tos_fields: $tos_fields\n";
        print NEW_FILTER " input: tcp_flags: $tcp_flags\n";
        print NEW_FILTER " input: exporter: $exporter\n";
        print NEW_FILTER " input: nexthop_ips: $nexthop_ips\n";
        print NEW_FILTER " input: sampling_multiplier: $sampling_multiplier\n";
        print NEW_FILTER " input: alert_threshold: $alert_threshold\n";
        print NEW_FILTER " input: alert_frequency: $alert_frequency\n";
        print NEW_FILTER " input: alert_destination: $alert_destination\n";
        print NEW_FILTER " input: alert_last_notified: \n";
        print NEW_FILTER " input: alert_consecutive: \n";
        print NEW_FILTER " input: IPFIX: $IPFIX\n";
        print NEW_FILTER " input: silk_rootdir: $silk_rootdir\n";
        print NEW_FILTER " input: silk_class: $silk_class\n";
        print NEW_FILTER " input: silk_flowtype: $silk_flowtype\n";
        print NEW_FILTER " input: silk_type: $silk_type\n";
        print NEW_FILTER " input: silk_sensors: $silk_sensors\n";
        print NEW_FILTER " input: silk_switches: $silk_switches\n";

        foreach $revision (@revisions) {
                print NEW_FILTER " input: revision: $revision\n";
        }

        # Need to determine revision date/time as it will apply to next collection

        open (INFO,">$work_directory/FlowMonitor_Management_info");
        $rrd_info_command = "$rrdtool_bin_directory/rrdtool info $rrdtool_file > $work_directory/FlowMonitor_Management_info";
        system($rrd_info_command);

        open (INFO,"<$work_directory/FlowMonitor_Management_info");
        while (<INFO>) {
                chop;
                $lead = substr($_,0,11);
                if ($lead eq "last_update") {
                        ($lead,$last_update) = split(/ = /);
                }
        }
        close (INFO);

        print NEW_FILTER " input: revision: $notate_graphs|$last_update|$revision_comment\n";
        close (NEW_FILTER);

	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td align=left><font color=#CF7C29><b>New Filtering Criteria:</b></font></td></tr>\n";
	print "  <tr><td>&nbsp</td></tr>\n";

        open  (NEW_FILTER,"<$filter_file");
        while (<NEW_FILTER>) {
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        ($input,$field,$field_value) = split(/: /);
                        if ($field eq "revision") {
                                ($new_notate_graphs,$revision_date,$new_revision_comment) = split(/\|/,$field_value);
                                ($notate_graphs,$revision_date,$revision_comment) = split(/\|/,$field_value);
                                $revision_date_out = epoch_to_date($revision_date,"LOCAL");
                                $revision_date_out =~ s/\^/:/g;
                                print "  <tr><td align=left>revision: $new_notate_graphs | $revision_date_out | $new_revision_comment</td></tr>\n";
                        } else {
				s/input: //;
                                print "  <tr><td align=left>$_</td></tr>\n";
                        }
                }
        }
        close (NEW_FILTER);

	print "  <tr><td>&nbsp</td></tr>\n";
	print "  </table>";

        print "  <table>\n";
        print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td><form method=post action=\"$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List\">\n";
        print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        print "  </table>\n";
        print "  </div>\n";

	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");

	exit;
}

if ($monitor_label eq "") {

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
	&create_UI_sides($active_dashboard);
	print " <div id=content>\n";
	print " <span class=text16>FlowMonitor: $monitor_label</span>\n";
	print " <center>\n";
	print " <br>\n";
	print " <table>\n";
        print "  <tr><td colspan=2>You must provide a Monitor Label which will be the title of your monitor.</td></tr>\n";
	print " </table>\n";
	print " </div>\n";

	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");
	exit;
}

if ($recreate) {

	# Cannot Recreate a Group

	if ($monitor_type eq "Group") {

		&create_UI_top($active_dashboard);
		&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
		&create_UI_sides($active_dashboard);
		print " <div id=content>\n";
		print " <span class=text16>FlowMonitor: $monitor_label</span>\n";
		print " <center>\n";
		print " <br>\n";
		print " <table>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
                print "  <tr><td>Recreates are permitted for Individual FlowMonitors only. New Groups will extend\n";
                print "back in time as far back as the existing component Individual FlowMonitors already go. They\n";
                print "will appear fully with the next run of FlowGrapher. If you wish to Recreate a Group from new\n";
		print "FlowMonitors, Recreate the Individual FlowMonitors first.\n";
		print " </td></tr>\n";
		print " </table>\n";

        	print "  <table>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
        	print "  <tr><td><form method=post action=\"$cgi_bin_short/FlowMonitor.cgi?$active_dashboard\">\n";
        	print "  <button class=links type=submit>Return</button></form></td></tr>\n";
        	print "  </table>\n";

		print " </div>\n";
		&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
		&finish_the_page("FlowMonitor_Main");

                exit;
	}

	# Make sure this is not a duplicate of an existing FlowMonitor

	while ($existing_filter = <$filter_directory/*>) {
	
	        if ($filter_file eq $existing_filter) {
	
	                $match = 1;
	
			&create_UI_top($active_dashboard);
			&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
			&create_UI_sides($active_dashboard);
			print " <div id=content>\n";
			print " <span class=text16>FlowMonitor: $monitor_label</span>\n";
			print " <center>\n";
			print " <br>\n";
			print " <table>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
	                print "  <tr><td colspan=2>An existing Filter file has been found with the same Monitor label.</td></tr>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
	                print "  <tr><td width=140 align=right><b>Monitor Label: &nbsp&nbsp</b></td><td align=left><font color=$filename_color><b><i>$monitor_label</i></b></font></td></tr>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
	                print "  <tr><td width=140 align=right><b>Monitor Filter File: &nbsp&nbsp</b></td><td align=left><font color=$filename_color><b><i>$filter_file</i></b></font></td></tr>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
			print " </table>\n";
			print " <table>\n";
	                print "  <tr><td>If you wish to replace the existing Monitor, please remove the existing one\n";
	                print "first, and resubmit the FlowMonitor form. Or, if you wish to continue an existing\n";
	                print "Monitor, but with new filtering criteria, visit the Manage All FlowMonitors page\n";
	                print "and select the \'Revise\' option from the entry in the list of FlowMonitors.\n";
			print " </td></tr>\n";
			print " </table>\n";
			print " </div>\n";
	
			&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
			&finish_the_page("FlowMonitor_Main");
	
	                exit;
	        }
	}

	$saved_suffix = &get_suffix;
	$save_file = "$work_directory/FlowMonitor_Recreate_saved_$saved_suffix";
	$filter_hash = "FM_FlowMonitor_Recreate_saved_$saved_suffix";
	start_saved_file($save_file);

	$recreate_command = "$cgi_bin_directory/FlowMonitor_Recreate $save_file &";
	system($recreate_command);

	&create_UI_top($active_dashboard);
	&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);
	print " <div id=content_wide>\n";
	&create_filter_output("FlowMonitor_Main",$filter_hash);
	print " <center>\n";
	print " <br>\n";
	print " <table>\n";
	print "  <br>\n";
        print "  <tr><td colspan=3>You have successfully started a <b><i>FlowMonitor Recreate</i></b>. The graphs for this new FlowMonitor will appear after the first</td></tr>\n";
        print "  <tr><td colspan=3>FlowMonitor_Grapher run after the Recreate completes. The Recreate is running in the background and you may continue</td></tr>\n";
        print "  <tr><td colspan=3>using FlowViewer. Longer Recreate timeframes will result in longer runs and the FlowMonitor will be available somewhat later.</td></tr>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td width=140 align=right><b>Monitor Label: &nbsp&nbsp</td><td align=left><b><font color=$filename_color><b><i>$monitor_label</i></b></font></td></tr>\n";
        print "  <tr><td width=140 align=right><b>Filter File: &nbsp&nbsp</td><td align=left><b><font color=$filename_color><b><i>$filter_file</i></b></font></td></tr>\n";
        print "  <tr><td width=140 align=right><b>RRDtool Database: &nbsp&nbsp<b></td><td align=left><font color=$filename_color><b><i>$rrdtool_file</i></b></font></td></tr>\n";
        print "  <tr><td width=140 align=right><b>HTML Directory: &nbsp&nbsp<b></td><td align=left><font color=$filename_color><b><i>$html_directory</i></b></font></td></tr>\n\n";
	print " </table>\n";
	print " </div>\n";

	&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page("FlowMonitor_Main");
	exit;
}

# Start up the Saved file

$saved_suffix = &get_suffix;
$saved_hash   = "FlowMonitor_save_$saved_suffix";
$filter_hash  = "FM_$saved_hash";
$saved_html   = "$work_directory/$saved_hash";
&start_saved_file($saved_html);

# Start the FlowMonitor Report web page output

&create_UI_top($active_dashboard);
&create_UI_service("FlowMonitor_Main","service_top",$active_dashboard,$filter_hash);

# If this is a group monitor, bring up Group Monitor input page

if ($monitor_type eq "Group") {

        # Compare Monitor Label to existing Monitors

        while ($existing_filter = <$filter_directory/*>) {

                if ($filter_file eq $existing_filter) {

			&create_UI_sides($active_dashboard);
			print " <div id=content>\n";
			print " <span class=text16>FlowMonitor: $monitor_label</span>\n";
			print " <center>\n";
			print " <br>\n";
			print " <table>\n";
	      	  	print "  <tr><td>&nbsp</td></tr>\n";
	                print "  <tr><td colspan=2>An existing Filter file has been found with the same Monitor label.</td></tr>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
	                print "  <tr><td align=right>Monitor Label: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$monitor_label</i></b></font></td></tr>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
	                print "  <tr><td align=right>Monitor Filter File: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$filter_file</i></b></font></td></tr>\n";
	        	print "  <tr><td>&nbsp</td></tr>\n";
			print " </table>\n";
			print " <table>\n";
                	print "  <tr><td>If you wish to replace the existing Monitor with this Group, please \n";
                	print "remove the existing one first, and resubmit the FlowMonitor form. Note that Group \n";
                	print "and Individual monitors cannot have the same name. Or, if you wish to continue an \n";
			print "existing Monitor, but with new filtering criteria, vistit the Manage All FlowMonitors\n";
                	print "page (a pulldown) and select the \'Revise\' option from the entry in the list of Monitors\n";
			print " </td></tr>\n";
			print " </table>\n";
			print " </div>\n";

                        exit;
                }
        }

        # Create the web page to hold the RRDtool graphs

        if (!-e $html_directory) {
                mkdir $html_directory, $html_dir_perms || die "cannot mkdir $html_directory: $!";
                chmod $html_dir_perms, $html_directory;
        }

        # Initialize the filter group file

        open (GROUP,">$group_file");
        print GROUP " input: monitor_label: $monitor_label\n";
        print GROUP " input: monitor_type: $monitor_type\n";
        print GROUP " input: general_comment: $general_comment\n";
        close (GROUP);

        # Invoke the FlowMonitor_Group.cgi to collect group inputs

        $action = "From FlowMonitor_Main";
        $command_list = "$active_dashboard^$action+$monitor_label+$general_comment";
        $command_list =~ s/ /~/g;
        $invoke_command = "$cgi_bin_directory/FlowMonitor_Group.cgi $command_list";

        system($invoke_command);

        exit;
}

# For Individual monitors

while ($existing_filter = <$filter_directory/*>) {

        if ($filter_file eq $existing_filter) {

                $match = 1;

		&create_UI_sides($active_dashboard);
		print " <div id=content>\n";
		print " <span class=text16>FlowMonitor: $monitor_label</span>\n";
		print " <center>\n";
		print " <br>\n";
		print " <table>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
                print "  <tr><td colspan=2>An existing Filter file has been found with the same Monitor label.</td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
                print "  <tr><td align=right>Monitor Label: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$monitor_label</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
                print "  <tr><td align=right>Monitor Filter File: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$filter_file</i></b></font></td></tr>\n";
        	print "  <tr><td>&nbsp</td></tr>\n";
		print " </table>\n";
		print " <table>\n";
                print "  <tr><td>If you wish to replace the existing Monitor, please remove the existing one\n";
                print "first, and resubmit the FlowMonitor form. Or, if you wish to continue an existing\n";
                print "Monitor, but with new filtering criteria, visit the Manage All FlowMonitors page\n";
                print "and select the \'Revise\' option from the entry in the list of FlowMonitors.\n";
		print " </td></tr>\n";
		print " </table>\n";
		print " </div>\n";

		&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
		&finish_the_page("FlowMonitor_Main");

                exit;
        }
}

print " <div id=content_wide>\n";
&create_filter_output("FlowMonitor_Main",$filter_hash);
print " <center>\n";
print " <br>\n";
print " <table>\n";

if (!$match) {

        # Create the filter to match the input specifications

	if ($IPFIX) {
		open (FILTER,">$filter_file") || die "cannot open Filter file for write: $filter_file";
		create_ipfix_filter;
	} else {
		create_filter_file (%FORM, $filter_file);
	}

        open (FILTER,">>$filter_file");
        print FILTER "\n\n";
        print FILTER " input: monitor_type: $monitor_type\n";
        print FILTER " input: device_name: $device_name\n";
        print FILTER " input: monitor_label: $monitor_label\n";
        print FILTER " input: general_comment: $general_comment\n";
        print FILTER " input: source_addresses: $source_addresses\n";
        print FILTER " input: source_ports: $source_ports\n";
        print FILTER " input: source_ifs: $source_ifs\n";
        print FILTER " input: sif_names: $sif_names\n";
        print FILTER " input: source_ases: $source_ases\n";
        print FILTER " input: dest_addresses: $dest_addresses\n";
        print FILTER " input: dest_ports: $dest_ports\n";
        print FILTER " input: dest_ifs: $dest_ifs\n";
        print FILTER " input: dif_names: $dif_names\n";
        print FILTER " input: dest_ases: $dest_ases\n";
        print FILTER " input: protocols: $protocols\n";
        print FILTER " input: tos_fields: $tos_fields\n";
        print FILTER " input: tcp_flags: $tcp_flags\n";
        print FILTER " input: exporter: $exporter\n";
        print FILTER " input: nexthop_ips: $nexthop_ips\n";
        print FILTER " input: sampling_multiplier: $sampling_multiplier\n";
        print FILTER " input: alert_threshold: $alert_threshold\n";
        print FILTER " input: alert_frequency: $alert_frequency\n";
        print FILTER " input: alert_destination: $alert_destination\n";
        print FILTER " input: alert_last_notified: \n";
        print FILTER " input: alert_consecutive: \n";
        print FILTER " input: IPFIX: $IPFIX\n";
        print FILTER " input: silk_rootdir: $silk_rootdir\n";
        print FILTER " input: silk_class: $silk_class\n";
        print FILTER " input: silk_flowtype: $silk_flowtype\n";
        print FILTER " input: silk_type: $silk_type\n";
        print FILTER " input: silk_sensors: $silk_sensors\n";
        print FILTER " input: silk_switches: $silk_switches\n";

        chmod $filter_file_perms, $filter_file;

        # Create the RRDtool database for this Monitor

        $start_rrd = time - (40 * 60);

        $rrdtool_command =     "$rrdtool_bin_directory/rrdtool create $rrdtool_file ".
                                "--step 300 ".
                                "--start $start_rrd ".
                                "DS:flowbits:GAUGE:600:U:U ".
                                "RRA:AVERAGE:0.5:1:600 ".
                                "RRA:AVERAGE:0.5:6:700 ".
                                "RRA:AVERAGE:0.5:24:775 ".
                                "RRA:AVERAGE:0.5:288:1100 ".
                                "RRA:MAX:0.5:1:600 ".
                                "RRA:MAX:0.5:6:700 ".
                                "RRA:MAX:0.5:24:775 ".
                                "RRA:MAX:0.5:288:1100";

        system($rrdtool_command);
        chmod $rrd_file_perms, $rrdtool_file;

        # Create the Directory to hold the RRDtool graphs

        if (!-e $html_directory) {
                mkdir $html_directory, $html_dir_perms || die "cannot mkdir $html_directory: $!";
                chmod $html_dir_perms, $html_directory;
        }

	print "  <br>\n";
        print "  <tr><td>&nbsp</td><td colspan=2>You have successfully setup a new FlowMonitor. The graphs for this new</td></tr>\n";
        print "  <tr><td>&nbsp</td><td colspan=2>FlowMonitor will appear after the next FlowGrapher run (e.g., < 5 minutes.)</td></tr>\n";
       	print "  <tr><td>&nbsp</td></tr>\n";
        print "  <tr><td align=right>Monitor Label: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$monitor_label</i></b></font></td></tr>\n";
        print "  <tr><td align=right>Filter File: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$filter_file</i></b></font></td></tr>\n";
        print "  <tr><td align=right>RRDtool Database: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$rrdtool_file</i></b></font></td></tr>\n";
        print "  <tr><td align=right>HTML Directory: &nbsp&nbsp</td><td align=left><font color=#CF7C29><b><i>$html_directory</i></b></font></td></tr>\n\n";
}

chmod $filter_file_perms, $filter_file;

print " </table>\n";
print " </div>\n";

&create_UI_service("FlowMonitor_Main","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowMonitor_Main");
