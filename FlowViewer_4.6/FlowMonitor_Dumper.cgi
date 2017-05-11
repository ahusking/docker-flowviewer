#! /usr/bin/perl
#
#  Purpose:
#  FlowMonitor_Dumper is invoked at the user's request to list out
#  the textual contents of the monitors.
#
#  Description:
#  A textual list of bits/second and byte quantities associated with the
#  relevant FlowMonitor graph (i.e., Last 24 Hours, Last 7 Days, etc.)
#  is output to the user's web page. This routine simply invokes 
#  'rrdtool dump ...' to generate the text.
#
#  Controlling Parameters 
#  Name                 Description
#  -----------------------------------------------------------------------
#  monitor_name        Name of the monitor in question
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  12/07/2007      3.3     Original version.
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards
#  J. Loiacono  11/02/2014      4.5     FlowTracker to FlowMonitor rename
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
use lib $cgi_bin_directory;

if ($debug_monitor eq "Y") { open (DEBUG,">$work_directory/DEBUG_MONITOR"); }
if ($debug_monitor eq "Y") { print DEBUG "In FlowMonitor_Dumper.cgi\n"; }

($active_dashboard,$dump_type,$dumper_label,$sampling_multiplier) = split(/\^/,$ENV{'QUERY_STRING'}); 

# Retrieve current time to use as a file suffix to permit more than one user to list Monitor text
     
($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime(time);
$mnth++; 
$yr += 1900; 
if ((0 < $mnth) && ($mnth < 10)) { $mnth = "0" . $mnth; }
if ((0 < $date) && ($date < 10)) { $date = "0" . $date; } 
if ((0 <= $hr)  && ($hr   < 10)) { $hr  = "0"  . $hr; } 
if ((0 <= $min) && ($min  < 10)) { $min = "0"  . $min; }  
if ((0 <= $sec) && ($sec  < 10)) { $sec = "0"  . $sec; }  
$prefix = $yr . $mnth . $date ."_". $hr . $min . $sec;  
$suffix = $hr . $min . $sec;

if ($dump_type eq "24_hours")  { $dump_type_out = "Last 24 Hours"; }
if ($dump_type eq "7_days")    { $dump_type_out = "Last 7 Days"; }
if ($dump_type eq "4_weeks")   { $dump_type_out = "Last 4 Weeks"; }
if ($dump_type eq "12_months") { $dump_type_out = "Last 12 Months"; }
if ($dump_type eq "3_years")   { $dump_type_out = "Last 3 Years"; }

$rrdtool_file  = "$rrdtool_directory/$dumper_label.rrd";
if (!-e $rrdtool_file) {
	$rrdtool_file  = "$rrdtool_directory/$dumper_label.archive";
}

$dump_file     = "$work_directory/FlowMonitor_dump_$suffix";

$dump_command = "$rrdtool_bin_directory/rrdtool dump $rrdtool_file > $dump_file";
system($dump_command);

# Get Averages

open (DUMP,"<$dump_file");
while (<DUMP>) {

	# Find start area

	if (($dump_type eq "24_hours")  && (/300 seconds/))   { $in_archive = 1; }
	if (($dump_type eq "7_days")    && (/1800 seconds/))  { $in_archive = 1; }
	if (($dump_type eq "4_weeks")   && (/7200 seconds/))  { $in_archive = 1; }
	if (($dump_type eq "12_months") && (/86400 seconds/)) { $in_archive = 1; }
	if (($dump_type eq "3_years")   && (/86400 seconds/)) { $in_archive = 1; }

	if (($in_archive)  && (/\<database/)) { $in_database = 1; };
	if (($in_database) && (/\/database/)) { $done = 1; };

	if ($in_database) { 

		($date,$time,$tz,$epoch,$value) = (split(/\s+/)) [2,3,4,6,8];
		$value = substr($value,8,35);
		$first_angle = index($value,"<");
		$value = substr($value,0,$first_angle);
		($abs,$man) = split(/e\+/,$value);
		$value_int = int($abs * (10**$man));

		if ($dump_type eq "24_hours") { 
			$est_total_bytes = int($value_int * 300 / 8);
			$est_total_bytes = format_number($est_total_bytes);
		} elsif ($dump_type eq "7_days") { 
			$est_total_bytes = int($value_int * 1800 / 8);
			$est_total_bytes = format_number($est_total_bytes);
		} elsif ($dump_type eq "4_weeks") { 
			$est_total_bytes = int($value_int * 7200 / 8);
			$est_total_bytes = format_number($est_total_bytes);
		} elsif ($dump_type eq "12_months") { 
			$est_total_bytes = int($value_int * 86400 / 8);
			$est_total_bytes = format_number($est_total_bytes);
		} elsif ($dump_type eq "3_years") { 
			$est_total_bytes = int($value_int * 86400 / 8);
			$est_total_bytes = format_number($est_total_bytes);
		}

		$average = format_number($value_int);
		$line = join("^",$date,$time,$tz,$epoch,$average,$est_total_bytes);
		push (@averages,$line);
	}

	if ($done) { 
		$in_archive  = 0;
		$in_database = 0;
		$done        = 0;
		last; 
	}
}
close (DUMP);

# Get Maximums

open (DUMP,"<$dump_file");
while (<DUMP>) {

	# Find start area

	if (/MAX/) {$in_maximums = 1; }

	if (($in_maximums) && ($dump_type eq "24_hours")  && (/300 seconds/))   { $in_archive = 1; };
	if (($in_maximums) && ($dump_type eq "7_days")    && (/1800 seconds/))  { $in_archive = 1; };
	if (($in_maximums) && ($dump_type eq "4_weeks")   && (/7200 seconds/))  { $in_archive = 1; };
	if (($in_maximums) && ($dump_type eq "12_months") && (/86400 seconds/)) { $in_archive = 1; };
	if (($in_maximums) && ($dump_type eq "3_years")   && (/86400 seconds/)) { $in_archive = 1; };

	if (($in_archive)  &&  (/\<database/)) { $in_database = 1; };
	if (($in_database) &&  (/\/database/)) { $done = 1; };

	if ($in_database) { 
		($date,$time,$tz,$epoch,$value) = (split(/\s+/)) [2,3,4,6,8];
		$value = substr($value,8,35);
		$first_angle = index($value,"<");
		$value = substr($value,0,$first_angle);
		($abs,$man) = split(/e\+/,$value);
		$value_int = int($abs * (10**$man));
		$maximum = format_number($value_int);
		$line = join("^",$date,$time,$tz,$epoch,$maximum);
		push (@maximums,$line);
	}

	if ($done) { last; }
}
close (DUMP);

# Output the report

&create_UI_top($active_dashboard);
&create_UI_service("FlowMonitor","service_top",$active_dashboard,$filter_hash);

# Create the FlowMonitor Display Content

&get_monitor_title($dumper_label);

print " <div id=content_wide>\n";
print " <span class=text16>$monitor_title</span><br><br>\n";
print "Listing of the contents of the <i>\'$dump_type_out\'</i><br>\n"; 

if ($sampling_multiplier ne "") { print "*Listed values are the original exported values multiplied by the Sampling Multiplier: $sampling_multiplier<br><br>\n"; }

if ($dump_type eq "24_hours")  { print "Time represents end of 5-minute period (values are for the previous 5 minutes)\n";}
if ($dump_type eq "7_days")    { print "Time represents end of 30-minute period (values are for the previous 30 minutes)\n";}
if ($dump_type eq "4_weeks")   { print "Time represents end of 2-hour period (values are for the previous 2 hours)\n";}
if ($dump_type eq "12_months") { print "Time represents end of 24-hour period (values are for the previous day)\n";}
if ($dump_type eq "3_years")   { print "Time represents end of 24-hour period (values are for the previous day)\n";}
print "   (nan = \'not a number\')<br><br>\n\n";

print "   <table>\n";
if ($sampling_multiplier ne "") { 
	print "   <tr>\n";
	print "   <td width=100 align=left>Date</td>\n";
	print "   <td width=80 align=left>Time</td>\n";
	print "   <td width=40 align=left>TZ</td>\n";
	print "   <td width=100 align=left>Epoch</td>\n";
	print "   <td width=120 align=right>Average (bps)*</td>\n";
	print "   <td width=120 align=right>Max 5-min (bps)*</td>\n";
	print "   <td width=120 align=right>Total Bytes (extrap.)*</td>\n";
	print "   </tr>\n";
} else {
	print "   <tr>\n";
	print "   <td width=100 align=left>Date</td>\n";
	print "   <td width=80 align=left>Time</td>\n";
	print "   <td width=40 align=left>TZ</td>\n";
	print "   <td width=100 align=left>Epoch</td>\n";
	print "   <td width=120 align=right>Average (bps)</td>\n";
	print "   <td width=120 align=right>Max 5-min (bps)</td>\n";
	print "   <td width=120 align=right>Total Bytes (extrap.)</td>\n";
	print "   </tr>\n";
}
print "   </table>\n";
print "   <br>\n";

# Output each line

print "   <table>\n";
$num_records = $#averages;
for ($i=1;$i<$num_records;$i++) {
	($a_date,$a_time,$a_tz,$a_epoch,$average,$est_total_bytes) = split(/\^/,$averages[$i]);
	($m_date,$m_time,$m_tz,$m_epoch,$maximum)                  = split(/\^/,$maximums[$i]);

	($temp_yr,$temp_mnth,$temp_day) = split(/-/,$a_date);

        if    ($date_format eq "DMY")  { $a_date_out = $temp_day ."/". $temp_mnth ."/". $temp_yr; }
        elsif ($date_format eq "DMY2") { $a_date_out = $temp_day .".". $temp_mnth .".". $temp_yr; }
        elsif ($date_format eq "MDY")  { $a_date_out = $temp_mnth ."/". $temp_day ."/". $temp_yr; }
        else                           { $a_date_out = $temp_yr ."-". $temp_mnth ."-". $temp_day; }

	print "   <tr>\n";
	print "   <td width=100 align=left>$a_date_out</td>\n";
	print "   <td width=80 align=left>$a_time</td>\n";
	print "   <td width=40 align=left>$a_tz</td>\n";
	print "   <td width=100 align=left>$a_epoch</td>\n";
	print "   <td width=120 align=right>$average</td>\n";
	print "   <td width=120 align=right>$maximum</td>\n";
	print "   <td width=120 align=right>$est_total_bytes</td>\n";
	print "   </tr>\n";
}
print "   </table>\n";
print " </div>\n";

&create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowMonitor");

# Remove the temporary dump file

$rm_command = "rm $dump_file";
system ($rm_command);
