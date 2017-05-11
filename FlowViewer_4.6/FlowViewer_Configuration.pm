#! /usr/bin/perl
#
#  Purpose:  
#  FlowViewer_Configuration.pm holds global variables for the FlowViewer,
#  FlowGrapher, and FlowMonitor NetFlow analysis tools.
#
#  Description:
#  Various parameters used to configure the system to a local environment.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  None
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  07/04/2005      1.0     Original version.
#  J. Loiacono  01/01/2006      2.0     Flowgrapher, new functions, speed
#  J. Loiacono  01/16/2006      2.1     Introduced $flow_file_length
#  J. Loiacono  07/04/2006      3.0     Added parameters for Monitor, others
#  J. Loiacono  12/25/2006      3.1     Changes for MIN/MAX, permissions
#  J. Loiacono  02/22/2007      3.2     Minor changes for Groups
#  J. Loiacono  12/07/2007      3.3     Exporters, Logging, Time-zone
#                                       File cleanup, Pie charts
#  J. Loiacono  12/15/2007      3.3.1   New $no_devices ... parameter
#  J. Loiacono  09/11/2010      3.4     New default_report parameter
#  J. Loiacono  03/17/2011      3.4     Can now specify deafult report for FV
#                                       Host column widths are now adjutable
#                                       Added 'tries=1' to dig; speeds resolving
#  J. Loiacono  05/21/2011      3.4     Fixed speeded-up FlowGrapher for non-GMT hosts
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  04/15/2013      4.1     New default FlowGrapher report setting
#                                       Fixed @ipfix_devices variable [M. Donnelly]
#  J. Loiacono  09/11/2013      4.2.1   Modified $default_graph for new Linear
#                                       New $date_format parameter
#  J. Loiacono  01/26/2014      4.3     Introduced Detect Scanning
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards and Analysis
#  J. Loiacono  11/02/2014      4.5     New $silk_compiled_localtime
#                                       New $ipset_directory
#                                       New $use_bottom_pulldowns
#                                       New $ipfix_default_device
#                                       New $sensor_config_file [rename]
#                                       New $silk_config_file
#                                       FlowTracker to FlowMonitor name changes 
#  J. Loiacono  01/26/2015      4.6     Removed $time_zone (now from system)
#
#$Author$
#$Date$
#$Header$
#
###########################################################################
#
#               BEGIN EXECUTABLE STATEMENTS
#
 
# Path variable

$ENV{PATH}              .= ':/usr/local/bin:/usr/sbin';

# Server

$FlowViewer_server       = "192.168.100.1"; # (IP address or hostname)

# Service

$FlowViewer_service      = "https";           # (http, or https)

# Directories and Files:

$reports_directory       = "/var/www/html/FlowViewer";
$reports_short           = "/FlowViewer";
$graphs_directory        = "/var/www/html/FlowGrapher";
$graphs_short            = "/FlowGrapher";
$monitor_directory       = "/var/www/html/FlowMonitor";
$monitor_short           = "/FlowMonitor";
$cgi_bin_directory       = "/var/www/cgi-bin/FlowViewer_4.6";
$cgi_bin_short           = "/cgi-bin/FlowViewer_4.6";
$work_directory          = "/var/www/cgi-bin/FlowViewer_4.6/Flow_Working";
$save_directory          = "/var/www/html/FlowViewer_Saves";
$save_short              = "/FlowViewer_Saves";
$names_directory         = "/var/www/cgi-bin/FlowViewer_4.6";
$ipset_directory         = "/var/www/cgi-bin/FlowViewer_4.6";     # Where FlowViewer can find IPset files
$filter_directory        = "/var/www/cgi-bin/FlowMonitor_Files/FlowMonitor_Filters";  
$rrdtool_directory       = "/var/www/cgi-bin/FlowMonitor_Files/FlowMonitor_RRDtool";
$dashboard_directory     = "/var/www/html/FlowViewer_Dashboard";
$dashboard_short         = "/FlowViewer_Dashboard";
#@other_dashboards       = ();          # Set to empty if you have just the one nominal Dashboard
@other_dashboards        = ("/var/www/html/SOC","/var/www/html/NetOps");
#@dashboard_titles       = ();          # Set to empty if you have just the one nominal Dashboard
@dashboard_titles        = ("Performance","SOC","NetOps"); # titles must be in the same order as the directories

$flow_data_directory     = "/data/flows";
$exporter_directory      = "/data/flows/all_routers";
$flow_bin_directory      = "/usr/local/flow-tools/bin";
$rrdtool_bin_directory   = "/usr/bin";

# SiLK parameters

$silk_data_directory     = "/data/flows";
$silk_bin_directory      = "/usr/local/bin";
$site_config_file        = "/data/flows/silk.conf";          # If left blank, will look for silk.conf in specified Data Rootdir (see User's Guide)
$sensor_config_file      = "/data/flows/sensor.conf";
$silk_compiled_localtime = "";          # Set to "Y" if you compiled SiLK with --enable-localtime switch

$silk_capture_buffer_pre = (125 * 60);  # Start of SiLK file concatenation
$silk_capture_buffer_post= (5 * 60);    # End of SiLK file concatenation

$silk_init_loadscheme    = 1;           # For Flows Initiated/Second - see SiLK rwcount documentation
$silk_active_loadscheme  = 5;           # For Flows Active/Second - see SiLK rwcount documentation
$silk_class_default      = "";          # General SiLK file structure info. silk.conf, sensor.conf
$silk_flowtype_default   = "";          # General SiLK file structure info. silk.conf, sensor.conf
$silk_type_default       = "all";       # General SiLK file structure info. silk.conf, sensor.conf
$silk_sensors_default    = "";          # General SiLK file structure info. silk.conf, sensor.conf
$silk_switches_default   = "";          # General SiLK file structure info. silk.conf, sensor.conf

# General parameters

$version                 = "4.6";
$no_devices_or_exporters = "N";         # Applies to special flow-tools environments only
@devices                 = ("router_1","router_2","router_3","router_4","router_5","router_6"); # for flow-tools
@ipfix_devices           = ("router_ipfix_1","router_ipfix_2","Site");   # for SiLK, if none: @ipfix_devices = ();
@ipfix_storage           = ("router_ipfix_1:15G","router_ipfix_2:10G");  # If using FlowViewer_CleanSilk, set to storage requirements for each device
$ipfix_default_device    = "";          # All initial, blank forms will have this selected instead of "Select Device"
#@exporters              = ("192.168.200.1:New York Router","192.168.200.2:Prague Router");
@exporters               = ();

$flow_capture_interval   = (35 * 60);
$flow_file_length        = (15 * 60);
$start_offset            = (90 * 60);   # e.g., 90 minutes ago
$end_offset              = (30 * 60);   # e.g., 30 minutes ago
$use_even_hours          = "Y";
$N                       = 3;
$use_NDBM                = "N";
$pie_chart_default       = 0;           # 0 = None;  1 = With Others;  2 = Without Others
$number_slices           = 9;
$pie_colors              = ['pie2 color1','pie2 color2','pie2 color3','pie2 color4','pie2 color5','pie2 color6','pie2 color7','pie2 color8','pie2 color9','pie2 color10'];
$maximum_days            = "91";
$remove_workfiles_time   = 2*86400;
$remove_graphfiles_time  = 7*86400;
$remove_reportfiles_time = 7*86400;
$time_zone_dst_offset    = (60 * 60);   # Number of seconds of the Daylight Savings adjustment in your timezone
$date_format             = "MDY";       # MDY=MM/DD/YYYY  DMY=DD/MM/YYYY  DMY2=DD.MM.YYYY  YMD=YYYY-MM-DD
$labels_in_titles        = "1";         # Set to "1" for labels in Monitor graph titles; "0" off
$sip_prefix_length       = "16";
$dip_prefix_length       = "16";

# UI Parameters

$left_title              = "SWAN Network";
$left_title_link         = "$cgi_bin_short/FV.cgi";
$right_title             = "Monitoring SWAN Network Data Flows";
$right_title_link        = "$cgi_bin_short/FV.cgi";
$use_bottom_pulldowns    = "Y";

# Debug Parameters 

$debug_viewer            = "Y";
$debug_grapher           = "Y";
$debug_monitor           = "Y";
$debug_group             = "Y";
$debug_files             = "N";

# Graphing parameters
 
$transparent        = "0";   
$x_ticks            = "T";
$long_ticks         = "T";
$skip_undef         = "T";
$graph_height       = 310;
$graph_width        = 600;
$t_margin           = 10;
$b_margin           = 60;
$l_margin           = 10;
$r_margin           = 20;
$bgclr              = "white";
$borderclrs         = "black";
$boxclr             = "white";
$fgclr              = "gray90";
$labelclr           = "black";
$axislabelclr       = "black";
$legendclr          = "black";
$valuesclr          = "black";
$textclr            = "black";
$x_axis_font        = "('arial', 16)";
$title_font         = "('arial', 18)";
$horz_max           = ($graph_width / 2) - 44;
$horz_pct           = ($graph_width / 2) - 44;
$horz_avg           = ($graph_width / 2) - 44;
$horz_min           = ($graph_width / 2) - 44;
$vert_max           = ($graph_height - 70) + 2;
$vert_pct           = ($graph_height - 70) + 16;
$vert_avg           = ($graph_height - 70) + 30;
$vert_min           = ($graph_height - 70) + 44;
$horz_mth           = 15;
$analyze_count      = 8;         # Any number from 3 to 10 inclusive. Must have at least [ $analyze_count+1 ] analyze_colors
$analyze_peak_width = 1000;      # Number of observations to examine for peaks (per period)
#$analyze_colors    = ['gray95','pale green','pale brown','pale red','pale blue','pale yellow'];
#$analyze_colors    = ['gray95','pastel orange','pastel rose','pastel blue','pastel green','pastel yellow'];
#$analyze_colors    = ['gray95','pie2 color1','pie2 color2','pie2 color3','pie2 color4','pie2 color5','pie2 color6','pie2 color7','pie2 color8','pie2 color9','pie2 color10'];
#$analyze_colors    = ['gray95','auto mixed1','auto mixed2','auto mixed3','auto mixed4','auto mixed5','auto mixed6','auto mixed7','auto mixed8','auto mixed9','auto mixed10'];
#$analyze_colors    = ['gray95','analysis1','analysis2','analysis4','analysis5','analysis9','auto mixed1'];
$analyze_colors     = ['gray95','analysis1','analysis2','analysis3','analysis4','analysis5','analysis6','analysis7','analysis8','analysis9','analysis10'];
$analyze_extension  = 20;        # Number of pixels to extend FlowGrapher_Analyze graph height

# Monitor parameters
 
$actives_webpage    = "index.html";
$log_directory      = "/var/www/cgi-bin/FlowViewer_4.6/logs";
$log_collector_short= "Y";
$log_collector_med  = "N";
$log_collector_long = "N";
$log_grapher_short  = "Y";
$log_grapher_long   = "N";
$collection_offset  = 1800;
$collection_period  = 300;
$graphing_period    = 300;
$recreate_cat_length= 6*(60*60); # Time length of concatenated file

$rrd_dir_perms      = 0777;      # Scale these back once everything is working 
$filter_dir_perms   = 0777;
$work_dir_perms     = 0777;
$html_dir_perms     = 0777;

$html_file_perms    = 0777;
$graph_file_perms   = 0777;
$rrd_file_perms     = 0777;
$filter_file_perms  = 0777;
$monitor_file_perms = 0777;
$saved_filters_perms= 0777;
$actives_file_perms = 0777;

$rrd_area           = "FFE0C0";   
$rrd_line           = "000000";   
$rrd_peak           = "000000";
$rrd_width          = 600;
$rrd_height         = 150;
$rrd_font           = "000000AA";
$rrd_back           = "FFFFFF";
$rrd_canvas         = "FFFFFF";
$rrd_grid           = "CCCCCC88";
$rrd_mgrid          = "FF000033";
$rrd_frame          = "FFFFFF";
$rrd_shadea         = "FFFFFF";
$rrd_shadeb         = "FFFFFF";
$rrd_thick          = 0.3;
$rrd_lower_limit    = 0;
$rrd_slope_mode     = "--slope-mode";      # $rrd_slope_mode = ""; will square graphs up
$rrd_vrule_color    = "FF0000";
$rrd_hrule_color    = "FF0000";
$thumbnail_width    = 250;
$thumbnail_height   = 80;
$hr_width           = $rrd_width + 130;

# Standard Deviation Alert parameters

$sigma_type_1       = "6:2.67";   # Num of obs in mean : number of sigmas for threshold : Must restart FlowMonitor_Collector
$sigma_type_2       = "12:4";     # Num of obs in mean : number of sigmas for threshold : Must restart FlowMonitor_Collector
$sigma_type_3       = "12:3";     # Num of obs in mean : number of sigmas for threshold : Must restart FlowMonitor_Collector

# Scanning Parameters

$dscan_parameters   = "-w -W";    # flow-tools only, ignores inbound and outbound port 80
$scan_model         = "2";        # SiLK only: 0=TRW&BLR; 1=TRW only;  2=BLR only
$trw_internal_set   = "$cgi_bin_directory/edc_ipset.set";       # SiLK only: file_name, required when using TRW model

# Webpage Parameters

$filename_color     = "#CF7C29";
$dns_column_width   = 60;
$detail_lines       = 200;
$asn_width          = 60;
$default_report     = 10;         # See FlowViewer Users Guide for details
$default_graph      = "bps";      # See FlowViewer Users Guide for details
$default_lines      = 100;
$default_identifier = "DNS";      # Use "IP" for IP addresses; "DNS" to resolve addresses to names
$default_flows      = 1;          # See FlowViewer Users Guide for details

# Commands (full directory names)
 
$dig                = "/usr/bin/dig +time=1 +tries=1 -x ";
$dig_forward        = "/usr/bin/dig +time=1 +tries=1 ";
