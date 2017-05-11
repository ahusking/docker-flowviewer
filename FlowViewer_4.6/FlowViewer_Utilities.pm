#! /usr/bin/perl
#
#  Purpose:  
#  FlowViewer_Utilities.pm holds utility functions that are called 
#  by FlowViewer, FlowGrapher, and FlowMonitor scripts.
#
#  Description:
#  Various conversion and formatting utility functions.
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
#  J. Loiacono  01/01/2006      2.0     Added y_format for FlowGrapher
#  J. Loiacono  04/15/2006      2.3     Added time_check for testing
#  J. Loiacono  07/04/2006      3.0     Included new formatting and filter subs
#                                       Permits host names (thanks Mark Foster)
#  J. Loiacono  12/25/2006      3.1     Allow all network masks, port ranges
#  J. Loiacono  02/22/2007      3.2     Moved create_flowmonitor_html here
#  J. Loiacono  12/07/2007      3.3     Exporter, Next Hop, Sampling, Logo,
#                                       Named IFs, Unit Conv. (thanks C. Kashimoto)
#  J. Loiacono  01/26/2008      3.3.1   E. Lautenschlaeger fix for exporter names
#  J. Loiacono  04/22/2008      3.3.1   Exporter appearing on FlowMonitor output
#  J. Loiacono  06/14/2008      3.3.1   Fixed printing extraneous Interface Names
#  J. Loiacono  03/17/2011      3.4     Now permits up to 20 source/dest networks
#                                       Can exclude IP addresses from requested ranges
#                                       Logo's now have links to Saved reports
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK,
#                                       New User Interface
#  J. Loiacono  09/11/2013      4.2.1   New international date formatting
#  J. Loiacono  09/28/2013      4.2.2   Fixed unitialized @temp_ports
#  J. Loiacono  01/26/2014      4.3     Removed 16-bit limitation on AS
#  J. Loiacono  07/04/2014      4.4     Fixed IP address field checks
#  J. Loiacono  11/02/2014      4.5     Ability to use SiLK localtime
#                                       SiLK IPset processing
#                                       Fixed port=0 filter processing
#  J. Loiacono  01/26/2015      4.6     Timezone from system (not Configuration)
#                                       Added "UTC" to check for "GMT"
#
#$Author$
#$Date$
#$Header$
#
###########################################################################
#
#               BEGIN EXECUTABLE STATEMENTS
#
 
use Time::Local;
use Time::HiRes qw( usleep ualarm gettimeofday tv_interval );

sub format_date {

	my ($sec,$min,$hr,$date,$mnth,$yr) = @_;
	$mnth++; 
	$yr += 1900; 
	if ($date<10) {$date = "0" . $date; } 
	if ($mnth<10) {$mnth = "0" . $mnth; } 
	if ($hr<10) {$hr = "0" . $hr; } 
	if ($min<10) {$min = "0" . $min; } 
	if ($sec<10) {$sec = "0" . $sec; } 
	$formatted_date = $mnth ."\/". $date ."\/". $yr ." ". $hr .":". $min .":". $sec; 
}

sub format_number { 

	my ($number) = @_;
	my $counter;
        $formatted_number = ""; 
        $length_number = length($number); 
        $counter = $length_number; 
        for ($digit=1;$digit<=$length_number;$digit++) { 
                $formatted_number = substr($number,$counter-1,1) . $formatted_number; 
                if (($digit>0) && ($digit%3 == 0)) { $formatted_number = "," . $formatted_number;} 
                $counter = $counter - 1; 
        } 
        if ( substr($formatted_number,0,1) eq ",") { 
                $formatted_number = substr($formatted_number,1,35); } 

	return $formatted_number;
} 

sub date_to_epoch {
 
	my ($in_date,$in_time,$time_zone)  = @_;
	 
	($mon,$day,$yr) = split(/\//,$in_date);
	($hr, $min, $sec) = split(/:/,$in_time);
	$date = $mon."/".$day."/".$yr." ".$hr.":".$min.":".$sec;
	if (($time_zone eq "GMT") || ($time_zone eq "UTC")) {
		$epoch_date = timegm($sec,$min,$hr,$day,$mon-1,$yr); }
	else {
		$epoch_date = timelocal($sec,$min,$hr,$day,$mon-1,$yr); }
	return $epoch_date;
}

sub epoch_to_date {

	my ($epoch_date,$time_zone)  = @_;
	 
	if (($time_zone eq "GMT") || ($time_zone eq "UTC")) {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = gmtime($epoch_date); }
	else {
		($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime($epoch_date); }

	$current_yr_date = $yr_date;
	$mnth++;
	$yr += 1900;
	if ($date<10) {$date = "0" . $date; }
	if ($mnth<10) {$mnth = "0" . $mnth; }
	if ($hr<10) {$hr = "0" . $hr; }
	if ($min<10) {$min = "0" . $min; }
	if ($sec<10) {$sec = "0" . $sec; }
	return $mnth ."\/". $date ."\/". $yr ." ". $hr .":". $min .":". $sec;
}

sub flow_date_time {
 
        my ($flow_time,$time_zone) = @_;
 
        $formatted = epoch_to_date($flow_time,$time_zone);
        ($first_half,$second_half) = split(/ /,$formatted);
        ($mnth,$date,$yr) = split(/\//,$first_half);
        ($hr,$min,$sec) = split(/:/,$second_half);
 
        if ((0 < $date) && ($date < 10)) { $date = substr($date,1,1); }
        if ((0 < $hr) && ($hr < 10)) { $hr = substr($hr,1,1); }
 
        if    ($mnth == 1)  { $month = "January"; }
        elsif ($mnth == 2)  { $month = "February"; }
        elsif ($mnth == 3)  { $month = "March"; }
        elsif ($mnth == 4)  { $month = "April"; }
        elsif ($mnth == 5)  { $month = "May"; }
        elsif ($mnth == 6)  { $month = "June"; }
        elsif ($mnth == 7)  { $month = "July"; }
        elsif ($mnth == 8)  { $month = "August"; }
        elsif ($mnth == 9)  { $month = "September"; }
        elsif ($mnth == 10) { $month = "October"; }
        elsif ($mnth == 11) { $month = "November"; }
        elsif ($mnth == 12) { $month = "December"; }
 
        return $month ." ". $date .", ". $yr ." ". $hr .":". $min .":". $sec;
}

sub day_of_week {

	my ($day_number) = @_;
	 
	if    ($day_number == 0) { $day = "Sun"; }
	elsif ($day_number == 1) { $day = "Mon"; }
	elsif ($day_number == 2) { $day = "Tue"; }
	elsif ($day_number == 3) { $day = "Wed"; }
	elsif ($day_number == 4) { $day = "Thr"; }
	elsif ($day_number == 5) { $day = "Fri"; }
	elsif ($day_number == 6) { $day = "Sat"; }

	return $day;
}

sub month_of_year {

	my ($mnth) = @_;
	 
	if    ($mnth == 0)  { $month = "Jan"; }
	elsif ($mnth == 1)  { $month = "Feb"; }
	elsif ($mnth == 2)  { $month = "Mar"; }
	elsif ($mnth == 3)  { $month = "Apr"; }
	elsif ($mnth == 4)  { $month = "May"; }
	elsif ($mnth == 5)  { $month = "Jun"; }
	elsif ($mnth == 6)  { $month = "Jul"; }
	elsif ($mnth == 7)  { $month = "Aug"; }
	elsif ($mnth == 8)  { $month = "Sep"; }
	elsif ($mnth == 9)  { $month = "Oct"; }
	elsif ($mnth == 10) { $month = "Nov"; }
	elsif ($mnth == 11) { $month = "Dec"; }

	return $month;
}

sub full_month {

	my ($mnth) = @_;

        if    ($mnth == "01")  { $month = "January"; }
        elsif ($mnth == "02")  { $month = "February"; }
        elsif ($mnth == "03")  { $month = "March"; }
        elsif ($mnth == "04")  { $month = "April"; }
        elsif ($mnth == "05")  { $month = "May"; }
        elsif ($mnth == "06")  { $month = "June"; }
        elsif ($mnth == "07")  { $month = "July"; }
        elsif ($mnth == "08")  { $month = "August"; }
        elsif ($mnth == "09")  { $month = "September"; }
        elsif ($mnth == "10")  { $month = "October"; }
        elsif ($mnth == "11")  { $month = "November"; }
        elsif ($mnth == "12")  { $month = "December"; }

	return $month;
}

sub convert_month {

	my ($mnth) = @_;
	 
	if    ($mnth eq "Jan") { $month = "01"; }
	elsif ($mnth eq "Feb") { $month = "02"; }
	elsif ($mnth eq "Mar") { $month = "03"; }
	elsif ($mnth eq "Apr") { $month = "04"; }
	elsif ($mnth eq "May") { $month = "05"; }
	elsif ($mnth eq "Jun") { $month = "06"; }
	elsif ($mnth eq "Jul") { $month = "07"; }
	elsif ($mnth eq "Aug") { $month = "08"; }
	elsif ($mnth eq "Sep") { $month = "09"; }
	elsif ($mnth eq "Oct") { $month = "10"; }
	elsif ($mnth eq "Nov") { $month = "11"; }
	elsif ($mnth eq "Dec") { $month = "12"; }

	return $month;
}

sub y_format { 
     
        my $value = shift; 
        my $ret; 
     
        if ($value >= 1000000) {   
                $ret = int ($value / 1000000) . " M"; }  
        else {   
                $ret = $value; } 
        return $ret; 
}

sub get_suffix {

	my $suffix;

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

	@letters=(A..Z);
	$first_letter  = $letters[rand 26];
	$second_letter = $letters[rand 26];

	$suffix .= $first_letter . $second_letter;
	return $suffix;
}


sub time_check {  
      
        my ($tc_event) = @_;  
      
        $tc_current_time = [gettimeofday]; 
        $tc_elapsed_time = tv_interval( $tc_last_time, $tc_current_time ); 
        if ($tc_last_event eq "") { $tc_elapsed_time = 0; } 
        $tc_total_time  += $tc_elapsed_time; 
     
        printf DEBUG "from: %-30s to: %-30s  elapsed seconds: %-3.6f  running: %-3.6f\n", $tc_last_event, $tc_event, $tc_elapsed_time, $tc_total_time;  
       
        $tc_last_time = $tc_current_time; 
        $tc_last_event = $tc_event;  
}    

sub create_filter_file {

	my $new_filter_file;

	# General parameters for generating Filter Files
	
	my $device_name       = $FORM{'device_name'};
	my $flow_select       = $FORM{'flow_select'};
	my $start_date        = $FORM{'start_date'};
	my $start_time        = $FORM{'start_time'};
	my $end_date          = $FORM{'end_date'};
	my $end_time          = $FORM{'end_time'};
	my $source_addresses  = $FORM{'source_address'};
	my $source_ports      = $FORM{'source_port'};
	my $source_ifs        = $FORM{'source_if'};
	my $sif_names         = $FORM{'sif_name'};
	my $source_ases       = $FORM{'source_as'};
	my $dest_addresses    = $FORM{'dest_address'};
	my $dest_ports        = $FORM{'dest_port'};
	my $dest_ifs          = $FORM{'dest_if'};
	my $dif_names         = $FORM{'dif_name'};
	my $dest_ases         = $FORM{'dest_as'};
	my $protocols         = $FORM{'protocols'};
	my $tos_fields        = $FORM{'tos_fields'};
	my $tcp_flags         = $FORM{'tcp_flags'};
	my $exporter          = $FORM{'exporter'};
	my $nexthop_ips       = $FORM{'nexthop_ip'};
	
	$new_filter_file      = "$filter_file";
	
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

	if ($start_date ne "") {
		$epoch_start = date_to_epoch($start_date,$start_time,"LOCAL"); 
		$flows_start = &flow_date_time($epoch_start,"LOCAL");
	}
	
	if ($end_date ne "") {
		$epoch_end   = date_to_epoch($end_date,$end_time,"LOCAL"); 
		$flows_end   = &flow_date_time($epoch_end,"LOCAL");
	}
	
	# Create the filter to match the input specifications
	
	open (FILTER,">$new_filter_file") || die "cannot open Filter file for write: $new_filter_file";

	$still_more = 1;

	# Set up source address filtering, if any
	 
	if ($source_addresses ne "") {
	 
	        print FILTER "filter-primitive source_address\n";
	        print FILTER "  type ip-address-prefix\n";
	 
	        $source_addresses =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($source_address) = split(/,/,$source_addresses);

	                $start_char = length($source_address) + 1;
	                $source_addresses = substr($source_addresses,$start_char);
	 
			if ($source_address =~ /:/) { &print_error("Ranges not supported for this field."); last; }

	                if (($source_address =~ m/^\s*-*\d+/) && (!($source_address =~ /[A-Za-z]/))) {
		                $_ = $source_address;
		                $num_dots = tr/\.//;
		                if ($num_dots != 3) { &print_error("Not full address: $source_address Try: n.n.n.n/m"); last; }
		 
		                ($a,$b,$c,$d)    = split(/\./,$source_address);
				($source_ip,$source_prefix) = split(/\//,$source_address);

		                if (($source_prefix eq "") && ($d eq "0")) {
		                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24."); last; }
		                if (($source_prefix < 0) || ($source_prefix > 32)) { 
					&print_error("Improper network mask (0 <= mask <= 32)"); last; }
		 
		                if ($a > 255 || $a eq "") { &print_error("Improper network: $source_address Try: n.n.n.n/m"); last; }
		                if ($b > 255 || $b eq "") { &print_error("Improper network: $source_address Try: n.n.n.n/m"); last; }
		                if ($c > 255 || $c eq "") { &print_error("Improper network: $source_address Try: n.n.n.n/m"); last; }
		                if ($d > 255 || $d eq "") { &print_error("Improper network: $source_address Try: n.n.n.n/m"); last; }
			}
	 
	                if (substr($source_address,0,1) eq "-") {
	                        $source_address = substr($source_address,1);
				print FILTER "  deny $source_address\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $source_address\n";
				$include = 1;
	                }
	 
	                if ($source_addresses eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }

	        $save_file .= "_" . $source_address;
	}
	 
	# Set up source interface filtering, if any
	 
	if ($sif_names ne "") { 
		if ($source_ifs eq "") {
			$source_ifs = $sif_names;
		} else {
			$source_ifs = $source_ifs .",". $sif_names;
		}
	}

	if ($source_ifs ne "") {
	 
	        print FILTER "filter-primitive source_if\n";
	        print FILTER "  type ifindex\n";
	 
	        $source_ifs =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($source_if) = split(/,/,$source_ifs);
	                $start_char = length($source_if) + 1;
	                $source_ifs = substr($source_ifs,$start_char);
	 
			if ($source_if =~ /:/)      { &print_error("Ranges not supported for this field."); last; }
	                if (length($source_if) > 4) { &print_error("Improper interface index: $source_if Try: nnn"); last; }
	 
	                if (substr($source_if,0,1) eq "-") {
	                        $source_if = substr($source_if,1,3);
				if ($source_if =~ /[^0-9]/) { &print_error("Improper Source interface index: $source_if Try: nnn"); last; }
	                        print FILTER "  deny $source_if\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $source_if\n";
				if ($source_if =~ /[^0-9]/) { &print_error("Improper Source interface index: $source_if Try: nnn"); last; }
				$include = 1;
	                }
	 
			if ($source_ifs eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }

	        $save_file .= "_" . $source_if;
	}
	 
	# Set up source port filtering, if any
	 
	if ($source_ports ne "") {
	 
	        print FILTER "filter-primitive source_port\n";
	        print FILTER "  type ip-port\n";
	 
	        $source_ports =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($source_port) = split(/,/,$source_ports);
	                $start_char = length($source_port) + 1;
	                $source_ports = substr($source_ports,$start_char);
	 
			$range = 0;
			if ($source_port =~ /:/) {
				$range = 1;
				($start_port,$end_port) = split(/:/,$source_port);
			}

			if ($range) {
	                	if (($start_port < -65536) || ($start_port > 65536)) {
					&print_error("Port out of range -65536 < port < 65536"); 
					last;
				}
	                	if (($end_port < -65536) || ($end_port > 65536)) {
					&print_error("Port out of range -65536 < port < 65536"); 
					last; 
				}
			}
			else {
	                	if (($source_port < -65536) || ($source_port > 65536)) {
					&print_error("Port out of range -65536 < port < 65536"); 
					last;
				}
			}
	 
			if ($range) {
	                	if (substr($start_port,0,1) eq "-") {
	                       		$start_port = substr($start_port,1,6);
					for ($j=$start_port;$j<=$end_port;$j++) { $port_range .= "$j,"; }
	                        	print FILTER "  deny $port_range\n";
	                        	$exclude = 1; }
	                	else {
					for ($j=$start_port;$j<=$end_port;$j++) { $port_range .= "$j,"; }
	                        	print FILTER "  permit $port_range\n";
					$include = 1;
	                	}
			}
			else {
	                	if (substr($source_port,0,1) eq "-") {
	                       		$source_port = substr($source_port,1,256);
	                        	print FILTER "  deny $source_port\n";
	                        	$exclude = 1; }
	                	else {
	                        	print FILTER "  permit $source_port\n";
					$include = 1;
	                	}
	                }
	 
			$range = 0;

	                if ($source_ports eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }

	        $save_file .= "_" . $source_port;
	}
	 
	# Set up source AS filtering, if any
	 
	if ($source_ases ne "") {
	 
	        print FILTER "filter-primitive source_as\n";
	        print FILTER "  type as\n";
	 
	        $source_ases =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($source_as) = split(/,/,$source_ases);
	                $start_char = length($source_as) + 1;
	                $source_ases = substr($source_ases,$start_char);
	 
			if ($source_as =~ /:/) { &print_error("Ranges not supported for this field."); last; }
	 
	                if (substr($source_as,0,1) eq "-") {
	                        $source_as = substr($source_as,1,6);
	                        print FILTER "  deny $source_as\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $source_as\n";
				$include = 1;
	                }
	 
	                if ($source_ases eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $source_as;
	}
	 
	# Set up destination address filtering, if any
	 
	if ($dest_addresses ne "") {
	
	        print FILTER "filter-primitive dest_address\n";
	        print FILTER "  type ip-address-prefix\n";
	 
	        $dest_addresses =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($dest_address) = split(/,/,$dest_addresses);
	                $start_char = length($dest_address) + 1;
	                $dest_addresses = substr($dest_addresses,$start_char);
	 
			if ($dest_address =~ /:/) { &print_error("Ranges not supported for this field."); last; }

	                if (($dest_address =~ m/^\s*-*\d+/) && (!($dest_address =~ /[A-Za-z]/))) {
		                $_ = $dest_address;
		                $num_dots = tr/\.//;
		                if ($num_dots != 3) { &print_error("Not full address: $dest_address Try: n.n.n.n/m"); last; }
		 
		                ($a,$b,$c,$d)    = split(/\./,$dest_address);
				($dest_ip,$dest_prefix)     = split(/\//,$dest_address);
		 
		                if (($dest_prefix eq "") && ($d eq "0")) {
		                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24"); last; }
		                if (($dest_prefix < 0) || ($dest_prefix > 32)) { &print_error("Improper network mask (0 <= mask <= 32)"); last; }
		 
		                if ($a > 255 || $a eq "") { &print_error("Improper network: $dest_address Try: n.n.n.n/m"); last; }
		                if ($b > 255 || $b eq "") { &print_error("Improper network: $dest_address Try: n.n.n.n/m"); last; }
		                if ($c > 255 || $c eq "") { &print_error("Improper network: $dest_address Try: n.n.n.n/m"); last; }
		                if ($d > 255 || $d eq "") { &print_error("Improper network: $dest_address Try: n.n.n.n/m"); last; }
			}
	 
	                if (substr($dest_address,0,1) eq "-") {
	                        $dest_address = substr($dest_address,1);
	                        print FILTER "  deny $dest_address\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $dest_address\n";
				$include = 1;
	                }
	 
	                if ($dest_addresses eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $dest_address;
	}
	 
	# Set up destination interface filtering, if any
	 
	if ($dif_names ne "") { 
		if ($dest_ifs eq "") {
			$dest_ifs = $dif_names;
		} else {
			$dest_ifs = $dest_ifs .",". $dif_names;
		}
	}

	if ($dest_ifs ne "") {
	 
	        print FILTER "filter-primitive dest_if\n";
	        print FILTER "  type ifindex\n";
	 
	        $dest_ifs =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($dest_if) = split(/,/,$dest_ifs);
	                $start_char = length($dest_if) + 1;
	                $dest_ifs = substr($dest_ifs,$start_char);
	 
			if ($dest_if =~ /:/)      { &print_error("Ranges not supported for this field."); last; }
	                if (length($dest_if) > 4) { &print_error("Improper interface index: $dest_if Try: nnn"); last; }
	 
	                if (substr($dest_if,0,1) eq "-") {
	                        $dest_if = substr($dest_if,1,3);
				if ($dest_if =~ /[^0-9]/) { &print_error("Improper Destination interface index: $dest_if Try: nnn"); last; }
	                        print FILTER "  deny $dest_if\n";
	                        $exclude = 1; }
	                else {
				if ($dest_if =~ /[^0-9]/) { &print_error("Improper Destination interface index: $dest_if Try: nnn"); last; }
	                        print FILTER "  permit $dest_if\n";
				$include = 1;
	                }
	 
	                if ($dest_ifs eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }

	        $save_file .= "_" . $dest_if;
	}
	 
	# Set up destination port filtering, if any
	 
	if ($dest_ports ne "") {
	 
	        print FILTER "filter-primitive dest_port\n";
	        print FILTER "  type ip-port\n";
	 
	        $dest_ports =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($dest_port) = split(/,/,$dest_ports);
	                $start_char = length($dest_port) + 1;
	                $dest_ports = substr($dest_ports,$start_char);
	 
			$range = 0;
			if ($dest_port =~ /:/) {
				$range = 1;
				($start_port,$end_port) = split(/:/,$dest_port);
			}

			if ($range) {
	                	if (($start_port < -65536) || ($start_port > 65536)) {
					&print_error("Port out of range -65536 < port < 65536"); 
					last;
				}
	                	if (($end_port < -65536) || ($end_port > 65536)) {
					&print_error("Port out of range -65536 < port < 65536"); 
					last; 
				}
			}
			else {
	                	if (($dest_port < -65536) || ($dest_port > 65536)) {
					&print_error("Port out of range -65536 < port < 65536"); 
					last;
				}
			}
	 
			if ($range) {
	                	if (substr($start_port,0,1) eq "-") {
	                       		$start_port = substr($start_port,1,6);
					for ($j=$start_port;$j<=$end_port;$j++) { $port_range .= "$j,"; }
	                        	print FILTER "  deny $port_range\n";
	                        	$exclude = 1; }
	                	else {
					for ($j=$start_port;$j<=$end_port;$j++) { $port_range .= "$j,"; }
	                        	print FILTER "  permit $port_range\n";
	                        	$include = 1;
	                	}
			}
			else {
	                	if (substr($dest_port,0,1) eq "-") {
	                       		$dest_port = substr($dest_port,1,256);
	                        	print FILTER "  deny $dest_port\n";
	                        	$exclude = 1; }
	                	else {
	                        	print FILTER "  permit $dest_port\n";
	                        	$include = 1;
	                	}
	                }
	 
			$range = 0;

	                if ($dest_ports eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }

	        $save_file .= "_" . $dest_port;
	}
	 
	# Set up destination AS filtering, if any
	 
	if ($dest_ases ne "") {
	 
	        print FILTER "filter-primitive dest_as\n";
	        print FILTER "  type as\n";
	 
	        $dest_ases =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($dest_as) = split(/,/,$dest_ases);
	                $start_char = length($dest_as) + 1;
	                $dest_ases = substr($dest_ases,$start_char);
	 
			if ($dest_as =~ /:/) { &print_error("Ranges not supported for this field."); last; }
	 
	                if (substr($dest_as,0,1) eq "-") {
	                        $dest_as = substr($dest_as,1,6);
	                        print FILTER "  deny $dest_as\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $dest_as\n";
				$include = 1;
	                }
	 
	                if ($dest_ases eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $dest_as;
	}
	
	# Set up Protocol filtering, if any
	
	if ($protocols ne "") {
	 
	        print FILTER "filter-primitive protocol\n";
	        print FILTER "  type ip-protocol\n";
	 
	        $protocols =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($protocol) = split(/,/,$protocols);
	                $start_char = length($protocol) + 1;
	                $protocols = substr($protocols,$start_char);
	 
			if ($protocol =~ /:/) { &print_error("Ranges not supported for this field."); last; }
	                if (($protocol < -255) || ($protocol > 255)) { &print_error("Protocol out of range 1 < Protocol < 255"); last; }
	 
	                if (substr($protocol,0,1) eq "-") {
	                        $protocol = substr($protocol,1,3);
	                        print FILTER "  deny $protocol\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $protocol\n";
				$include = 1;
	                }
	 
	                if ($protocols eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $protocol;
	}
	
	# Set up TCP Flag filtering, if any
	
	if ($tcp_flags ne "") {
	 
	        print FILTER "filter-primitive tcp_flag\n";
	        print FILTER "  type ip-tcp-flags\n";
	 
	        $tcp_flags =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($tcp_flag) = split(/,/,$tcp_flags);
	                $start_char = length($tcp_flag) + 1;
	                $tcp_flags = substr($tcp_flags,$start_char);
	 
			if ($tcp_flag =~ /:/) { &print_error("Ranges not supported for this field."); last; }
	                if (length($tcp_flag) > 4) { &print_error("TCP Flag out of range: 0x00 < TCP Flag < 0xFF"); last; }
	 
			($tcp_flag,$tcp_mask) = split(/\//,$tcp_flag);
	
	                if (substr($tcp_flag,0,1) eq "-") {
	                        $tcp_flag = substr($tcp_flag,1,4);
				if ($tcp_mask ne "") { print FILTER "  mask $tcp_mask\n"; }
	                        print FILTER "  deny $tcp_flag\n";
				$exclude = 1; }
	                else {
				if ($tcp_mask ne "") { print FILTER "  mask $tcp_mask\n"; }
	                        print FILTER "  permit $tcp_flag\n";
				$include = 1;
	                }
	 
	                if ($tcp_flags eq "") { last; }
	        }
	
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $tcp_flag;
	}
	
	# Set up TOS Field filtering, if any
	
	if ($tos_fields ne "") {
	 
	        print FILTER "filter-primitive tos_field\n";
	        print FILTER "  type ip-tos\n";
	 
	        $tos_fields =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($tos_field) = split(/,/,$tos_fields);
	                $start_char = length($tos_field) + 1;
	                $tos_fields = substr($tos_fields,$start_char);
	 
			if ($tos_field =~ /:/) { &print_error("Ranges not supported for this field."); last; }
	                if (length($tos_field) > 4) { &print_error("TOS Field out of range: 0x00 < TOS Field < 0xFF"); last; }

			($tos_field,$tos_mask) = split(/\//,$tos_field);
	
	                if (substr($tos_field,0,1) eq "-") {
	                        $tos_field = substr($tos_field,1,4);
				if ($tos_mask ne "") { print FILTER "  mask $tos_mask\n"; }
	                        print FILTER "  deny $tos_field\n";
				$exclude = 1; }
	                else {
				if ($tos_mask ne "") { print FILTER "  mask $tos_mask\n"; }
	                        print FILTER "  permit $tos_field\n";
				$include = 1;
	                }
	 
	                if ($tos_fields eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $tos_field;
	}
	
	# Set up exporter address filtering, if any
	 
	if ($exporter ne "") {
	 
	        print FILTER "filter-primitive exporter\n";
	        print FILTER "  type ip-address-prefix\n";
	 
	        $exporter =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($exporter_address) = split(/,/,$exporter);
	                $start_char = length($exporter_address) + 1;
	                $exporter = substr($exporter,$start_char);
	 
			if ($exporter_address =~ /:/) { &print_error("Ranges not supported for this field."); last; }

	                if ($exporter_address =~ m/^\s*-*\d+/) {
		                $_ = $exporter_address;
		                $num_dots = tr/\.//;
		                if ($num_dots != 3) { &print_error("Not full address: $exporter_address Try: n.n.n.n/m"); last; }
		 
		                ($a,$b,$c,$d)    = split(/\./,$exporter_address);
				($exporter_ip,$exporter_prefix) = split(/\//,$exporter_address);

		                if (($exporter_prefix eq "") && ($d eq "0")) {
		                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24."); last; }
		                if (($exporter_prefix < 0) || ($exporter_prefix > 32)) { 
					&print_error("Improper network mask (0 <= mask <= 32)"); last; }
		 
		                if ($a > 255 || $a eq "") { &print_error("Improper network: $exporter_address Try: n.n.n.n/m"); last; }
		                if ($b > 255 || $b eq "") { &print_error("Improper network: $exporter_address Try: n.n.n.n/m"); last; }
		                if ($c > 255 || $c eq "") { &print_error("Improper network: $exporter_address Try: n.n.n.n/m"); last; }
		                if ($d > 255 || $d eq "") { &print_error("Improper network: $exporter_address Try: n.n.n.n/m"); last; }
			}
	 
	                if (substr($exporter_address,0,1) eq "-") {
	                        $exporter_address = substr($exporter_address,1);
				print FILTER "  deny $exporter_address\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $exporter_address\n";
				$include = 1;
	                }
	 
	                if ($exporter eq "") { last; }
	        }
	 
	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $exporter_address;
	}
	 
	# Set up Next Hop Ip filtering, if any

	if ($nexthop_ips ne "") {
	 
	        print FILTER "filter-primitive nexthop_ip\n";
	        print FILTER "  type ip-address-prefix\n";
	 
	        $nexthop_ips =~ s/\s+//g;
	
		$include = 0;  $exclude = 0;

		while ($still_more) {
	 
	                ($nexthop_address) = split(/,/,$nexthop_ips);
	                $start_char = length($nexthop_address) + 1;
	                $nexthop_ips = substr($nexthop_ips,$start_char);
	 
			if ($nexthop_address =~ /:/) { &print_error("Ranges not supported for this field."); last; }

	                if ($nexthop_address =~ m/^\s*-*\d+/) {
		                $_ = $nexthop_address;
		                $num_dots = tr/\.//;
		                if ($num_dots != 3) { &print_error("Not full address: $nexthop_address Try: n.n.n.n/m"); last; }
		 
		                ($a,$b,$c,$d)    = split(/\./,$nexthop_address);
				($nexthop_ip,$nexthop_prefix) = split(/\//,$nexthop_address);

		                if (($nexthop_prefix eq "") && ($d eq "0")) {
		                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24."); last; }
		                if (($nexthop_prefix < 0) || ($nexthop_prefix > 32)) { 
					&print_error("Improper network mask (0 <= mask <= 32)"); last; }
		 
		                if ($a > 255 || $a eq "") { &print_error("Improper network: $nexthop_address Try: n.n.n.n/m"); last; }
		                if ($b > 255 || $b eq "") { &print_error("Improper network: $nexthop_address Try: n.n.n.n/m"); last; }
		                if ($c > 255 || $c eq "") { &print_error("Improper network: $nexthop_address Try: n.n.n.n/m"); last; }
		                if ($d > 255 || $d eq "") { &print_error("Improper network: $nexthop_address Try: n.n.n.n/m"); last; }
			}
	 
	                if (substr($nexthop_address,0,1) eq "-") {
	                        $nexthop_address = substr($nexthop_address,1);
				print FILTER "  deny $nexthop_address\n";
	                        $exclude = 1; }
	                else {
	                        print FILTER "  permit $nexthop_address\n";
				$include = 1;
	                }
	 
	                if ($nexthop_ips eq "") { last; }
	        }

	        if (($exclude) && (!$include)) {
	                $exclude = 0;
	                print FILTER "  default permit\n";
		}
	        if (($include) && (!$exclude)) {
	                $include = 0;
	                print FILTER "  default deny\n";
	        }
	 
	        $save_file .= "_" . $nexthop_address;
	}
	 
	# Write out the flow files filter
	
	print FILTER "filter-primitive start_flows\n";
	print FILTER "  type time-date\n";
	print FILTER "  permit ge $flows_start\n";
	print FILTER "  default deny\n";
	print FILTER "filter-primitive end_flows\n";
	print FILTER "  type time-date\n";
	print FILTER "  permit lt $flows_end\n";
	print FILTER "  default deny\n";
	print FILTER " \n";
	print FILTER "filter-definition Flow_Filter\n";
	if ($source_address ne "") {
	        print FILTER "  match ip-source-address source_address\n";
	}
	if ($source_if ne "") {
	        print FILTER "  match input-interface source_if\n";
	}
	if ($source_port ne "") {
	        print FILTER "  match ip-source-port source_port\n";
	}
	if ($source_as ne "") {
	        print FILTER "  match source-as source_as\n";
	}
	if ($dest_address ne "") {
	        print FILTER "  match ip-destination-address dest_address\n";
	}
	if ($dest_if ne "") {
	        print FILTER "  match output-interface dest_if\n";
	}
	if ($dest_port ne "") {
	        print FILTER "  match ip-destination-port dest_port\n";
	}
	if ($dest_as ne "") {
	        print FILTER "  match destination-as dest_as\n";
	}
	if ($protocol ne "") {
	        print FILTER "  match ip-protocol protocol\n";
	}
	if ($tcp_flag ne "") {
	        print FILTER "  match ip-tcp-flags tcp_flag\n";
	}
	if ($tos_field ne "") {
	        print FILTER "  match ip-tos tos_field\n";
	}
	if ($exporter_address ne "") {
	        print FILTER "  match ip-exporter-address exporter\n";
	}
	if ($nexthop_address ne "") {
	        print FILTER "  match ip-nexthop-address nexthop_ip\n";
	}
	
	if ($flow_select == 1) {
		print FILTER "  match end-time start_flows\n";
		print FILTER "  match start-time end_flows\n";
		$flow_select_manner = "Any part of flow in Time Period";
	}
	if ($flow_select == 2) {
		print FILTER "  match end-time start_flows\n";
		print FILTER "  match end-time end_flows\n";
		$flow_select_manner = "Flow end-time in Time Period";
	}
	if ($flow_select == 3) {
		print FILTER "  match start-time start_flows\n";
		print FILTER "  match start-time end_flows\n";
		$flow_select_manner = "Flow start-time in Time Period";
	}
	if ($flow_select == 4) {
		print FILTER "  match start-time start_flows\n";
		print FILTER "  match end-time end_flows\n";
		$flow_select_manner = "Flow entirely in Time Period";
	}
	
	close (FILTER);
}

sub create_ipfix_filter {

	# General parameters for generating Filter Files
	
	my $device_name       = $FORM{'device_name'};
	my $flow_select       = $FORM{'flow_select'};
	my $start_date        = $FORM{'start_date'};
	my $start_time        = $FORM{'start_time'};
	my $end_date          = $FORM{'end_date'};
	my $end_time          = $FORM{'end_time'};
	my $source_addresses  = $FORM{'source_address'};
	my $source_ports      = $FORM{'source_port'};
	my $source_ifs        = $FORM{'source_if'};
	my $sif_names         = $FORM{'sif_name'};
	my $source_ases       = $FORM{'source_as'};
	my $dest_addresses    = $FORM{'dest_address'};
	my $dest_ports        = $FORM{'dest_port'};
	my $dest_ifs          = $FORM{'dest_if'};
	my $dif_names         = $FORM{'dif_name'};
	my $dest_ases         = $FORM{'dest_as'};
	my $protocols         = $FORM{'protocols'};
	my $tos_fields        = $FORM{'tos_fields'};
	my $tcp_flags         = $FORM{'tcp_flags'};
	my $exporter          = $FORM{'exporter'};
	my $nexthop_ips       = $FORM{'nexthop_ip'};
	
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

	$scidr_field          = "";
	$not_scidr_field      = "";
	$sif_field            = "";
	$in_index_field       = "";
	$sport_field          = "";
	$sas_field            = "";
	$dcidr_field          = "";
	$not_dcidr_field      = "";
	$dif_field            = "";
	$out_index_field      = "";
	$dport_field          = "";
	$das_field            = "";
	$proto_field          = "";
	$tcp_flags_field      = "";
	$sensor_field         = "";
	$nhcidr_field         = "";
	$not_nhcidr_field     = "";

	$still_more = 1;

	# Set up source address filtering, if any
	 
	if ($source_addresses ne "") {
	 
	        $source_addresses  =~ s/\s+//g;
		$num_include_saddr = 0;
		$num_exclude_saddr = 0;
		$IPSET = 0;

		if (substr($source_addresses,0,1) eq "/") { 
			if (($print_report >= 12) && ($print_report <= 17)) {
				$sip_prefix_length = substr($source_addresses,1,3);
				if ((($print_report >= 12) && ($print_report <= 14)) && ($sip_prefix_length > 32)) {
					&print_error("This prefix ($source_addresses) is too long for IPv4 addresses. Please correct, or use one of the _v6 reports.");
					last;
				}
				$source_address = $source_addresses;
	        		$save_file .= "_" . $source_address;
				if (substr($dest_addresses,0,1) eq "/") { 
					$dip_prefix_length = substr($dest_addresses,1,3);
					if ((($print_report >= 12) && ($print_report <= 14)) && ($dip_prefix_length > 32)) {
						&print_error("This prefix ($dest_addresses) is too long for IPv4 addresses. Please correct, or use one of the _v6 reports.");
						last;
					}
					$dest_address = $dest_addresses;
	        			$save_file .= "_" . $dest_address;
				}
			} else {
				&print_error("Improper network: $source_address. Network mask is applicable to Printed Prefix Aggregation reports only");
				last;
			}

		} elsif ($source_addresses =~ /\.set$/) {

			$IPSET = 1;
			$still_more = 0;
			if (substr($source_addresses,0,1) ne "-") {
				$source_ipset = $source_addresses;
			} else {
				$num_exclude_saddr = 1;
				$not_source_ipset = substr($source_addresses,1,255);
			}
		}
	
		while ($still_more) {
	 
			$IPv4 = 0; $IPv6 = 0; $unresolved = 0;

	                ($source_address) = split(/,/,$source_addresses);
	                $start_char = length($source_address) + 1;
	                $source_addresses = substr($source_addresses,$start_char);

	                if ($source_address =~ m/^\s*-*\d+/) {
		                $_ = $source_address;
		                $num_dots   = tr/\.//; if ($num_dots   > 0) { $IPv4 = 1; }
		                $num_colons = tr/\://; if ($num_colons > 0) { $IPv6 = 1; }

				if (($IPv4) && ($IPv6)) {
			                &print_error("Support for IPv4-IPv6 embedded addresses not available in this version. $source_address"); last;
				}
	
				if ($IPv4) {
	
			                if ($num_dots != 3) { &print_error("Not full IPv4 address: $source_address Try: n.n.n.n/m"); last; }
			 
			                ($a,$b,$c,$d)    = split(/\./,$source_address);
					($source_ip,$source_prefix) = split(/\//,$source_address);
	
			                if (($source_prefix eq "") && ($d eq "0")) {
			                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24."); last; }
			                if (($source_prefix < 0) || ($source_prefix > 32)) { 
						&print_error("Improper network mask (0 <= mask <= 32)"); last; }
			 
			                if ($a > 255 || $a eq "") { &print_error("Improper IPv4 network: $source_address Try: n.n.n.n/m"); last; }
			                if ($b > 255 || $b eq "") { &print_error("Improper IPv4 network: $source_address Try: n.n.n.n/m"); last; }
			                if ($c > 255 || $c eq "") { &print_error("Improper IPv4 network: $source_address Try: n.n.n.n/m"); last; }
			                if ($d > 255 || $d eq "") { &print_error("Improper IPv4 network: $source_address Try: n.n.n.n/m"); last; }
				}
		 
				if ($IPv6) {
	
			                if ($num_colons > 7) { &print_error("Improper IPv6 address: $source_address.  Too many address segments."); last; }
	
					($source_ip,$source_prefix)   = split(/\//,$source_address);
			                ($a,$b,$c,$d,$e,$f,$g,$h) = split(/\:/,$source_address);
	
	                		if ($source_address =~ /[h-zH-Z]/) { &print_error("Improper IPv6 network. Contains a non-Hex character: $source_address"); last; }

			                if (($source_prefix < 0) || ($source_prefix > 128)) { 
						&print_error("Improper IPv6 network mask (0 <= mask <= 128)"); last; }
			 
			                if (hex($a) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $a"); last; }
			                if (hex($b) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $b"); last; }
			                if (hex($c) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $c"); last; }
			                if (hex($d) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $d"); last; }
			                if (hex($e) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $e"); last; }
			                if (hex($f) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $f"); last; }
			                if (hex($g) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $g"); last; }
			                if (hex($h) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $h"); last; }
				}

			} else {
				$unresolved = 1;
			}
	 
	                if (substr($source_address,0,1) eq "-") {
				$num_exclude_saddr++;
	                        $source_address   = substr($source_address,1);
                                if ($unresolved) {
					$source_ip = &dig_forward($source_address);
				} else {
					$source_ip = $source_address;
				}
				if ($num_exclude_saddr < 2) {
					$not_scidr_field .= $source_ip;  
				} else {
					$not_scidr_field .= "," . $source_ip;  
				}
	                } else {
				$num_include_saddr++;
                                if ($unresolved) {
					$source_ip = &dig_forward($source_address);
				} else {
					$source_ip = $source_address;
				}
				if ($num_include_saddr < 2) {
					$scidr_field .= $source_ip;  
				} else {
					$scidr_field .= "," . $source_ip;  
				}
	                }
	 
	                if ($source_addresses eq "") { last; }
	        }

		if (!$IPSET) {
			$scidr_field      = " --scidr="      . $scidr_field;
			$not_scidr_field  = " --not-scidr="  . $not_scidr_field;
		} else {
			if ($num_exclude_saddr < 1) {
				$sipset_field     = " --sipset="     . $ipset_directory ."/". $source_ipset;
			} else {
				$not_sipset_field = " --not-sipset=" . $ipset_directory ."/". $not_source_ipset;
			}
			$still_more = 1;
		}

	        $save_file .= "_" . $source_address;
	}

	# Set up source interface filtering, if any
	 
	if ($sif_names ne "") { 
		if ($source_ifs eq "") {
			$source_ifs = $sif_names;
		} else {
			$source_ifs = $source_ifs .",". $sif_names;
		}
	}

	if ($source_ifs ne "") {
	 
	        $source_ifs =~ s/\s+//g;
		$num_include_sif = 0;
		$num_exclude_sif = 0;

		while ($still_more) {
	 
	                ($source_if) = split(/,/,$source_ifs);
	                $start_char = length($source_if) + 1;
	                $source_ifs = substr($source_ifs,$start_char);

                        $exclude = 0;
                        if (substr($source_if,0,1) eq "-") {
                                $source_if = substr($source_if,1,12);
                                $exclude = 1;
                        }

			if ($source_if =~ /[^0-9]/) { &print_error("Improper Source interface index: $source_if Try: nnn"); last; }

			$range = 0;
                        if (($source_if =~ /:/) || ($source_if =~ /[\-]/)) {
                                $range = 1;
                                if ($source_if =~ /:/)    { ($start_if,$end_if) = split(/:/,$source_if); }
                                if ($source_if =~ /[\-]/) { ($start_if,$end_if) = split(/[\-]/,$source_if); }
                                if ($end_if < $start_if) {
                                        &print_error("Interface range is backwards:  End IF:$end_if  <  Start IF:$start_if");
                                        last;
                                }
                        }

                        if ($range) {
                                if (($start_if > 10000) || ($start_if > 10000)) {
                                        &print_error("Port out of range. Must be: -10000 <= $source_if <= 10000");
                                        last;
                                }
                                if (($end_if > 10000) || ($end_if > 10000)) {
                                        &print_error("Port out of range. Must be: -10000 <= $source_if <= 10000");
                                        last;
                                }
                        }
                        else {
                                if (($source_if > 10000) || ($source_if > 10000)) {
                                        &print_error("Port out of range. Must be: -10000 <= $source_if <= 10000");
                                        last;
                                }
                        }
	 
			if ($range) {
				if ($exclude) {
					$num_exclude_sif++;
					if ($num_exclude_sif < 2) {
						if ($start_if == 0) {
							$sif_range_start = $end_if + 1;
							$sif_range_end   = 10000;
							$sif_field .= $sif_range_start ."-". $sif_range_end;
						} elsif ($end_if == 10000) {
							$sif_range_start = 0;
							$sif_range_end   = $start_if - 1; 
							$sif_field .= $sif_range_start ."-". $sif_range_end;
						} else {
							$sif_range_start = 0;
							$sif_range_end   = $start_if - 1; 
							$sif_field .= $sif_range_start ."-". $sif_range_end;
							$sif_range_start = $end_if + 1;
							$sif_range_end   = 10000;
							$sif_field .= "," . $sif_range_start ."-". $sif_range_end;
						}
					} else {
						$last_comma = rindex($sif_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($sif_field,$last_comma,15);
						($last_start_if,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_if;
						$first_range_end   = $start_if - 1; 
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $end_if + 1;
						$second_range_end   = 10000;
						$second_range       = $second_range_start ."-". $second_range_end;

						$sif_field = substr($sif_field,0,$last_comma);
						if ($end_if == 10000) {
							$sif_field .= $first_range;
						} else {
							$sif_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_sif++;
					if ($num_include_sif < 2) {
						$sif_field .= $start_if ."-". $end_if;
					} else {
						$sif_field .= "," . $start_if ."-". $end_if;
					}
	                	}

			} else {

				if ($exclude) {
					$num_exclude_sif++;
					if ($num_exclude_sif < 2) {
						if ($source_if == 0) {
							$sif_range_start = 1;
							$sif_range_end   = 10000;
							$sif_field = $sif_range_start ."-". $sif_range_end;
						} elsif ($source_if == 10000) {
							$sif_range_start = 0;
							$sif_range_end   = 9999;
							$sif_field = $sif_range_start ."-". $sif_range_end;
						} else {
							$sif_range_start = 0;
							$sif_range_end   = $source_if - 1; 
							$sif_field = $sif_range_start ."-". $sif_range_end;
							$sif_range_start = $source_if + 1;
							$sif_range_end   = 10000;
							$sif_field .= "," . $sif_range_start ."-". $sif_range_end;
						}
					} else {
						$last_comma = rindex($sif_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($sif_field,$last_comma,15);
						($last_start_if,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_if;
						$first_range_end   = $source_if - 1;
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $source_if + 1;
						$second_range_end   = 10000;
						$second_range       = $second_range_start ."-". $second_range_end;

						$sif_field = substr($sif_field,0,$last_comma);
						if ($first_range_end < $first_range_start) {
							$sif_field .= $second_range;
						} elsif ($second_range_end < $second_range_start) {
							$sif_field .= $first_range;
						} else {
							$sif_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_sif++;
					if ($num_include_sif < 2) {
						$sif_field .= $source_if;  
					} else {
						$sif_field .= "," . $source_if;  
					}
	                	}
	                }
	 
			$range = 0;

	                if ($source_ifs eq "") { last; }
	        }
	 
		$in_index_field  = " --input-index=" . $sif_field;

	        $save_file .= "_" . $source_if;
	}

	# Set up source port filtering, if any
	 
	if ($source_ports ne "") {
	 
		$sport_range_start = 0;

	        $source_ports =~ s/\s+//g;
		$num_include_sport = 0;
		$num_exclude_sport = 0;
	
		@temp_ports  = ();
		@temp_ranges = ();
		@unsorted_ports = split(/\,/,$source_ports);
		foreach $unsorted_port (@unsorted_ports) { 
			$temp_port = $unsorted_port;
			if ($temp_port =~ /:/) { push (@temp_ranges,$temp_port); next; }
			if (substr($unsorted_port,0,1) eq "-") { $temp_port = substr($unsorted_port,1,5); }
			if (length($temp_port) == 1) { $temp_port = "0000" . $temp_port; }
			if (length($temp_port) == 2) { $temp_port = "000"  . $temp_port; }
			if (length($temp_port) == 3) { $temp_port = "00"   . $temp_port; }
			if (length($temp_port) == 4) { $temp_port = "0"    . $temp_port; }
			if (substr($unsorted_port,0,1) eq "-") { $temp_port = "-" . $temp_port; }
			push (@temp_ports,$temp_port);
		}
		@sorted_ports = sort (@temp_ports);
		$sorted_string = "";
		foreach $temp_range (@temp_ranges) { $sorted_string .= $temp_range .","; }
		foreach $sorted_port (@sorted_ports) { 
			$temp_port = $sorted_port;
			if (substr($sorted_port,0,1) eq "-") { $temp_port = substr($sorted_port,1,5); }
			if ($temp_port ne "00000") {
				$temp_port =~ s/^0+//g;
			} else {
				$temp_port = 0;
			}
			if (substr($sorted_port,0,1) eq "-") { $temp_port = "-" . $temp_port; }
			$sorted_string .= $temp_port . ",";
		}
		chop $sorted_string;
		$source_ports = $sorted_string;

		while ($still_more) {
	 
	                ($source_port) = split(/,/,$source_ports);
	                $start_char = length($source_port) + 1;
	                $source_ports = substr($source_ports,$start_char);

                        $exclude = 0;
                        if (substr($source_port,0,1) eq "-") {
                                $source_port = substr($source_port,1,12);
                                $exclude = 1;
                        }

			$range = 0;
                        if (($source_port =~ /:/) || ($source_port =~ /[\-]/)) {
                                $range = 1;
                                if ($source_port =~ /:/)    { ($start_port,$end_port) = split(/:/,$source_port); }
                                if ($source_port =~ /[\-]/) { ($start_port,$end_port) = split(/[\-]/,$source_port); }
                                if ($end_port < $start_port) {
                                        &print_error("Port range is backwards:  End port:$end_port  <  Start port:$start_port");
                                        last;
                                }
                        }

                        if ($range) {
                                if (($start_port > 65535) || ($end_port > 65535)) {
                                        &print_error("Port out of range. Must be: $source_port <= 65535");
                                        last;
                                }
                        }
                        else {
                                if ($source_port > 65535) {
                                        &print_error("Port out of range. Must be: $source_port <= 65535");
                                        last;
                                }
                        }
	 
			if ($range) {
				if ($exclude) {
					$num_exclude_sport++;
					if ($num_exclude_sport < 2) {
						if ($start_port == 0) {
							$sport_range_start = $end_port + 1;
							$sport_range_end   = 65535;
							$sport_field .= $sport_range_start ."-". $sport_range_end;
						} elsif ($end_port == 65535) {
							$sport_range_start = 0;
							$sport_range_end   = $start_port - 1; 
							$sport_field .= $sport_range_start ."-". $sport_range_end;
						} else {
							$sport_range_start = 0;
							$sport_range_end   = $start_port - 1; 
							$sport_field .= $sport_range_start ."-". $sport_range_end;
							$sport_range_start = $end_port + 1;
							$sport_range_end   = 65535;
							$sport_field .= "," . $sport_range_start ."-". $sport_range_end;
						}
					} else {
						$last_comma = rindex($sport_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($sport_field,$last_comma,15);
						($last_start_port,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_port;
						$first_range_end   = $start_port - 1; 
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $end_port + 1;
						$second_range_end   = 65535;
						$second_range       = $second_range_start ."-". $second_range_end;

						$sport_field = substr($sport_field,0,$last_comma);
						if ($end_port == 65535) {
							$sport_field .= $first_range;
						} else {
							$sport_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_sport++;
					if ($num_include_sport < 2) {
						$sport_field .= $start_port ."-". $end_port;
					} else {
						$sport_field .= "," . $start_port ."-". $end_port;
					}
	                	}

			} else {

				if ($exclude) {
					$num_exclude_sport++;
					if ($num_exclude_sport < 2) {
						if ($source_port == 0) {
							$sport_range_start = 1;
							$sport_range_end   = 65535;
							$sport_field = $sport_range_start ."-". $sport_range_end;
						} elsif ($source_port == 65535) {
							$sport_range_start = 0;
							$sport_range_end   = 65534;
							$sport_field = $sport_range_start ."-". $sport_range_end;
						} else {
							$sport_range_start = 0;
							$sport_range_end   = $source_port - 1; 
							$sport_field = $sport_range_start ."-". $sport_range_end;
							$sport_range_start = $source_port + 1;
							$sport_range_end   = 65535;
							$sport_field .= "," . $sport_range_start ."-". $sport_range_end;
						}
					} else {
						$last_comma = rindex($sport_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($sport_field,$last_comma,15);
						($last_start_port,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_port;
						$first_range_end   = $source_port - 1;
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $source_port + 1;
						$second_range_end   = 65535;
						$second_range       = $second_range_start ."-". $second_range_end;

						$sport_field = substr($sport_field,0,$last_comma);
						if ($first_range_end < $first_range_start) {
							$sport_field .= $second_range;
						} elsif ($second_range_end < $second_range_start) {
							$sport_field .= $first_range;
						} else {
							$sport_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_sport++;
					if ($num_include_sport < 2) {
						$sport_field .= $source_port;  
					} else {
						$sport_field .= "," . $source_port;  
					}
	                	}
	                }
	 
			$range = 0;

	                if ($source_ports eq "") { last; }
	        }
	 
		$sport_field  = " --sport=" . $sport_field;

	        $save_file .= "_" . $source_port;
	}
	 
	# Set up source AS filtering, if any (not in SiLK v2.4.5)
	 
	if ($source_ases ne "") {
	 
	        $source_ases =~ s/\s+//g;
		$num_include_sases = 0;
	
	  	&print_error("SiLK software does not support filtering on AS at this time: $source_ases"); last;

		while ($still_more) {
	 
	                ($source_as) = split(/,/,$source_ases);
	                $start_char = length($source_as) + 1;
	                $source_ases = substr($source_ases,$start_char);
	 
	                if (($source_as < -65536) || ($source_as > 65536)) { &print_error("AS out of range -65536 < AS < 65536"); last; }
	 
	                if (substr($source_as,0,1) eq "-") {
	                        $source_as = substr($source_as,1,6);
	  			&print_error("SiLK software does not support exclusion of Autonomous Systems at this time: -$source_ases"); last;
	                } else {
				$num_include_sases++;
				if ($num_include_sases < 2) {
					$sas_field .= $source_as;  
				} else {
					$sas_field .= "," . $source_as;  
				}
                	}
	 
	                if ($source_ases eq "") { last; }
	        }
	 
		$sas_field  = " --sas=" . $sas_field;

	        $save_file .= "_" . $source_as;
	}
	 
	# Set up destination address filtering, if any
	 
	if ($dest_addresses ne "") {
	 
	        $dest_addresses =~ s/\s+//g;
		$num_include_daddr = 0;
		$num_exclude_daddr = 0;
		$IPSET = 0;
	
		if (substr($source_addresses,0,1) eq "/") { 
			if (($print_report >= 12) && ($print_report <= 17)) {
				$sip_prefix_length = substr($source_addresses,1,3);
				if ((($print_report >= 12) && ($print_report <= 14)) && ($sip_prefix_length > 32)) {
					&print_error("This prefix ($source_addresses) is too long for IPv4 addresses. Please correct, or use one of the _v6 reports.");
					last;
				}
				$source_address = $source_addresses;
	        		$save_file .= "_" . $source_address;
				if (substr($dest_addresses,0,1) eq "/") { 
					$dip_prefix_length = substr($dest_addresses,1,3);
					if ((($print_report >= 12) && ($print_report <= 14)) && ($dip_prefix_length > 32)) {
						&print_error("This prefix ($dest_addresses) is too long for IPv4 addresses. Please correct, or use one of the _v6 reports.");
						last;
					}
					$dest_address = $dest_addresses;
	        			$save_file .= "_" . $dest_address;
				}
			} else {
				&print_error("Improper network: $source_address. Network mask is applicable to Printed Prefix Aggregation reports only");
				last;
			}
		}
	
		if (substr($dest_addresses,0,1) eq "/") { 
			if (($print_report >= 12) && ($print_report <= 17)) {
				$dip_prefix_length = substr($dest_addresses,1,3);
				if ((($print_report >= 12) && ($print_report <= 14)) && ($dip_prefix_length > 32)) {
					&print_error("This prefix ($dest_addresses) is too long for IPv4 addresses. Please correct, or use one of the _v6 reports.");
					last;
				}
				$dest_address = $dest_addresses;
	        		$save_file .= "_" . $dest_address;
			} else {
				&print_error("Improper network: $dest_address. Network mask is applicable to Printed Prefix Aggregation reports only");
				last;
			}

		} elsif ($dest_addresses =~ /\.set$/) {

			$IPSET = 1;
			$still_more = 0;
			if (substr($dest_addresses,0,1) ne "-") {
				$dest_ipset = $dest_addresses;
			} else {
				$num_exclude_daddr = 1;
				$not_dest_ipset = substr($dest_addresses,1,255);
			}
		}
	
		while ($still_more) {
	 
			$IPv4 = 0; $IPv6 = 0; $unresolved = 0;

	                ($dest_address) = split(/,/,$dest_addresses);
	                $start_char = length($dest_address) + 1;
	                $dest_addresses = substr($dest_addresses,$start_char);
	 
	                if ($dest_address =~ m/^\s*-*\d+/) {
		                $_ = $dest_address;
		                $num_dots   = tr/\.//; if ($num_dots   > 0) { $IPv4 = 1; }
		                $num_colons = tr/\://; if ($num_colons > 0) { $IPv6 = 1; }

				if (($IPv4) && ($IPv6)) {
			                &print_error("Support for IPv4-IPv6 embedded addresses not available in this version. $dest_address"); last; 
				}
	
				if ($IPv4) {
	
			                if ($num_dots != 3) { &print_error("Not full IPv4 address: $dest_address Try: n.n.n.n/m"); last; }
			 
			                ($a,$b,$c,$d)    = split(/\./,$dest_address);
					($dest_ip,$dest_prefix) = split(/\//,$dest_address);
	
			                if (($dest_prefix eq "") && ($d eq "0")) {
			                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24."); last; }
			                if (($dest_prefix < 0) || ($dest_prefix > 32)) { 
						&print_error("Improper network mask (0 <= mask <= 32)"); last; }
			 
			                if ($a > 255 || $a eq "") { &print_error("Improper IPv4 network: $dest_address Try: n.n.n.n/m"); last; }
			                if ($b > 255 || $b eq "") { &print_error("Improper IPv4 network: $dest_address Try: n.n.n.n/m"); last; }
			                if ($c > 255 || $c eq "") { &print_error("Improper IPv4 network: $dest_address Try: n.n.n.n/m"); last; }
			                if ($d > 255 || $d eq "") { &print_error("Improper IPv4 network: $dest_address Try: n.n.n.n/m"); last; }
				}
		 
				if ($IPv6) {
	
			                if ($num_colons > 7) { &print_error("Improper IPv6 address: $dest_address.  Too many address segments."); last; }
	
					($dest_ip,$dest_prefix)   = split(/\//,$dest_address);
			                ($a,$b,$c,$d,$e,$f,$g,$h) = split(/\:/,$dest_address);
	
	                		if ($dest_address =~ /[h-zH-Z]/) { &print_error("Improper IPv6 network. Contains a non-Hex character: $dest_address"); last; }

			                if (($dest_prefix < 0) || ($dest_prefix > 128)) { 
						&print_error("Improper IPv6 network mask (0 <= mask <= 128)"); last; }
			 
			                if (hex($a) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $a"); last; }
			                if (hex($b) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $b"); last; }
			                if (hex($c) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $c"); last; }
			                if (hex($d) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $d"); last; }
			                if (hex($e) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $e"); last; }
			                if (hex($f) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $f"); last; }
			                if (hex($g) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $g"); last; }
			                if (hex($h) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $h"); last; }
				}

			} else {
				$unresolved = 1;
			}

	                if (substr($dest_address,0,1) eq "-") {
				$num_exclude_daddr++;
	                        $dest_address = substr($dest_address,1);
                                if ($unresolved) {
					$dest_ip = &dig_forward($dest_address);
				} else {
					$dest_ip = $dest_address;
				}
				if ($num_exclude_daddr < 2) {
					$not_dcidr_field .= $dest_ip;  
				} else {
					$not_dcidr_field .= "," . $dest_ip;  
				}
	                } else {
				$num_include_daddr++;
                                if ($unresolved) {
					$dest_ip = &dig_forward($dest_address);
				} else {
					$dest_ip = $dest_address;
				}
				if ($num_include_daddr < 2) {
					$dcidr_field .= $dest_ip;  
				} else {
					$dcidr_field .= "," . $dest_ip;  
				}
	                }
	 
	                if ($dest_addresses eq "") { last; }
	        }

		if (!$IPSET) {
			$dcidr_field      = " --dcidr="      . $dcidr_field;
			$not_dcidr_field  = " --not-dcidr="  . $not_dcidr_field;
		} else {
			if ($num_exclude_daddr < 1) {
				$dipset_field     = " --dipset="     . $ipset_directory ."/". $dest_ipset;
			} else {
				$not_dipset_field = " --not-dipset=" . $ipset_directory ."/". $not_dest_ipset;
			}
			$still_more = 1;
		}

	        $save_file .= "_" . $dest_address;
	}

	# Set up destination interface filtering, if any
	 
	if ($dif_names ne "") { 
		if ($dest_ifs eq "") {
			$dest_ifs = $dif_names;
		} else {
			$dest_ifs = $dest_ifs .",". $dif_names;
		}
	}

	if ($dest_ifs ne "") {
	 
	        $dest_ifs =~ s/\s+//g;
		$num_include_dif = 0;
		$num_exclude_dif = 0;

		while ($still_more) {
	 
	                ($dest_if) = split(/,/,$dest_ifs);
	                $start_char = length($dest_if) + 1;
	                $dest_ifs = substr($dest_ifs,$start_char);

                        $exclude = 0;
                        if (substr($dest_if,0,1) eq "-") {
                                $dest_if = substr($dest_if,1,12);
                                $exclude = 1;
                        }

			if ($dest_if =~ /[^0-9]/) { &print_error("Improper Destination interface index: $dest_if Try: nnn"); last; }

			$range = 0;
                        if (($dest_if =~ /:/) || ($dest_if =~ /[\-]/)) {
                                $range = 1;
                                if ($dest_if =~ /:/)    { ($start_if,$end_if) = split(/:/,$dest_if); }
                                if ($dest_if =~ /[\-]/) { ($start_if,$end_if) = split(/[\-]/,$dest_if); }
                                if ($end_if < $start_if) {
                                        &print_error("Interface range is backwards:  End IF:$end_if  <  Start IF:$start_if");
                                        last;
                                }
                        }

                        if ($range) {
                                if (($start_if > 10000) || ($start_if > 10000)) {
                                        &print_error("Port out of range. Must be: -10000 <= $dest_if <= 10000");
                                        last;
                                }
                                if (($end_if > 10000) || ($end_if > 10000)) {
                                        &print_error("Port out of range. Must be: -10000 <= $dest_if <= 10000");
                                        last;
                                }
                        }
                        else {
                                if (($dest_if > 10000) || ($dest_if > 10000)) {
                                        &print_error("Port out of range. Must be: -10000 <= $dest_if <= 10000");
                                        last;
                                }
                        }
	 
			if ($range) {
				if ($exclude) {
					$num_exclude_dif++;
					if ($num_exclude_dif < 2) {
						if ($start_if == 0) {
							$dif_range_start = $end_if + 1;
							$dif_range_end   = 10000;
							$dif_field .= $dif_range_start ."-". $dif_range_end;
						} elsif ($end_if == 10000) {
							$dif_range_start = 0;
							$dif_range_end   = $start_if - 1; 
							$dif_field .= $dif_range_start ."-". $dif_range_end;
						} else {
							$dif_range_start = 0;
							$dif_range_end   = $start_if - 1; 
							$dif_field .= $dif_range_start ."-". $dif_range_end;
							$dif_range_start = $end_if + 1;
							$dif_range_end   = 10000;
							$dif_field .= "," . $dif_range_start ."-". $dif_range_end;
						}
					} else {
						$last_comma = rindex($dif_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($dif_field,$last_comma,15);
						($last_start_if,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_if;
						$first_range_end   = $start_if - 1; 
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $end_if + 1;
						$second_range_end   = 10000;
						$second_range       = $second_range_start ."-". $second_range_end;

						$dif_field = substr($dif_field,0,$last_comma);
						if ($end_if == 10000) {
							$dif_field .= $first_range;
						} else {
							$dif_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_dif++;
					if ($num_include_dif < 2) {
						$dif_field .= $start_if ."-". $end_if;
					} else {
						$dif_field .= "," . $start_if ."-". $end_if;
					}
	                	}

			} else {

				if ($exclude) {
					$num_exclude_dif++;
					if ($num_exclude_dif < 2) {
						if ($dest_if == 0) {
							$dif_range_start = 1;
							$dif_range_end   = 10000;
							$dif_field = $dif_range_start ."-". $dif_range_end;
						} elsif ($dest_if == 10000) {
							$dif_range_start = 0;
							$dif_range_end   = 9999;
							$dif_field = $dif_range_start ."-". $dif_range_end;
						} else {
							$dif_range_start = 0;
							$dif_range_end   = $dest_if - 1; 
							$dif_field = $dif_range_start ."-". $dif_range_end;
							$dif_range_start = $dest_if + 1;
							$dif_range_end   = 10000;
							$dif_field .= "," . $dif_range_start ."-". $dif_range_end;
						}
					} else {
						$last_comma = rindex($dif_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($dif_field,$last_comma,15);
						($last_start_if,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_if;
						$first_range_end   = $dest_if - 1;
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $dest_if + 1;
						$second_range_end   = 10000;
						$second_range       = $second_range_start ."-". $second_range_end;

						$dif_field = substr($dif_field,0,$last_comma);
						if ($first_range_end < $first_range_start) {
							$dif_field .= $second_range;
						} elsif ($second_range_end < $second_range_start) {
							$dif_field .= $first_range;
						} else {
							$dif_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_dif++;
					if ($num_include_dif < 2) {
						$dif_field .= $dest_if;  
					} else {
						$dif_field .= "," . $dest_if;  
					}
	                	}
	                }
	 
			$range = 0;

	                if ($dest_ifs eq "") { last; }
	        }
	 
		$out_index_field  = " --output-index=" . $dif_field;

	        $save_file .= "_" . $dest_if;
	}
	 
	# Set up destination port filtering, if any
	 
	if ($dest_ports ne "") {
	 
print DEBUG "dest_ports: $dest_ports\n";
		$dport_range_start = 0;

	        $dest_ports =~ s/\s+//g;
		$num_include_dport = 0;
		$num_exclude_dport = 0;
	
		@temp_ports  = ();
		@temp_ranges = ();
		@unsorted_ports = split(/\,/,$dest_ports);
		foreach $unsorted_port (@unsorted_ports) { 
			$temp_port = $unsorted_port;
			if ($temp_port =~ /:/) { push (@temp_ranges,$temp_port); next; }
			if (substr($unsorted_port,0,1) eq "-") { $temp_port = substr($unsorted_port,1,5); }
			if (length($temp_port) == 1) { $temp_port = "0000" . $temp_port; }
			if (length($temp_port) == 2) { $temp_port = "000"  . $temp_port; }
			if (length($temp_port) == 3) { $temp_port = "00"   . $temp_port; }
			if (length($temp_port) == 4) { $temp_port = "0"    . $temp_port; }
			if (substr($unsorted_port,0,1) eq "-") { $temp_port = "-" . $temp_port; }
			push (@temp_ports,$temp_port);
		}
		@sorted_ports = sort (@temp_ports);
		$sorted_string = "";
		foreach $temp_range (@temp_ranges) { $sorted_string .= $temp_range .","; }
		foreach $sorted_port (@sorted_ports) { 
			$temp_port = $sorted_port;
			if (substr($sorted_port,0,1) eq "-") { $temp_port = substr($sorted_port,1,5); }
			if ($temp_port ne "00000") {
				$temp_port =~ s/^0+//g;
			} else {
				$temp_port = 0;
			}
			if (substr($sorted_port,0,1) eq "-") { $temp_port = "-" . $temp_port; }
			$sorted_string .= $temp_port . ",";
		}
		chop $sorted_string;
		$dest_ports = $sorted_string;
print DEBUG "after range calc, dest_ports: $dest_ports\n";

		while ($still_more) {
	 
	                ($dest_port) = split(/,/,$dest_ports);
	                $start_char = length($dest_port) + 1;
	                $dest_ports = substr($dest_ports,$start_char);

                        $exclude = 0;
                        if (substr($dest_port,0,1) eq "-") {
                                $dest_port = substr($dest_port,1,12);
                                $exclude = 1;
                        }

			$range = 0;
                        if (($dest_port =~ /:/) || ($dest_port =~ /[\-]/)) {
                                $range = 1;
                                if ($dest_port =~ /:/)    { ($start_port,$end_port) = split(/:/,$dest_port); }
                                if ($dest_port =~ /[\-]/) { ($start_port,$end_port) = split(/[\-]/,$dest_port); }
                                if ($end_port < $start_port) {
                                        &print_error("Port range is backwards:  End port:$end_port  <  Start port:$start_port");
                                        last;
                                }
                        }

                        if ($range) {
                                if (($start_port > 65535) || ($end_port > 65535)) {
                                        &print_error("Port out of range. Must be: $dest_port <= 65535");
                                        last;
                                }
                        }
                        else {
                                if ($dest_port > 65535) {
                                        &print_error("Port out of range. Must be: $dest_port <= 65535");
                                        last;
                                }
                        }
	 
			if ($range) {
	                	if ($exclude) {
					$num_exclude_dport++;
					if ($num_exclude_dport < 2) {
						if (abs($start_port) == 0) {
							$dport_range_start = $end_port + 1;
							$dport_range_end   = 65535;
							$dport_field .= $dport_range_start ."-". $dport_range_end;
						} elsif ($end_port == 65535) {
							$dport_range_start = 0;
							$dport_range_end   = $start_port - 1; 
							$dport_field .= $dport_range_start ."-". $dport_range_end;
						} else {
							$dport_range_start = 0;
							$dport_range_end   = $start_port - 1; 
							$dport_field .= $dport_range_start ."-". $dport_range_end;
							$dport_range_start = $end_port + 1;
							$dport_range_end   = 65535;
							$dport_field .= "," . $dport_range_start ."-". $dport_range_end;
						}
					} else {
						$last_comma = rindex($dport_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($dport_field,$last_comma,15);
						($last_start_port,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_port;
						$first_range_end   = $start_port - 1; 
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $end_port + 1;
						$second_range_end   = 65535;
						$second_range       = $second_range_start ."-". $second_range_end;

						$dport_field = substr($dport_field,0,$last_comma);
						if ($end_port == 65535) {
							$dport_field .= $first_range;
						} else {
							$dport_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_dport++;
					if ($num_include_dport < 2) {
						$dport_field .= $start_port ."-". $end_port;
					} else {
						$dport_field .= "," . $start_port ."-". $end_port;
					}
	                	}

			} else {

	                	if ($exclude) {
					$num_exclude_dport++;
					if ($num_exclude_dport < 2) {
						if ($dest_port == 0) {
							$dport_range_start = 1;
							$dport_range_end   = 65535;
							$dport_field = $dport_range_start ."-". $dport_range_end;
						} elsif ($dest_port == 65535) {
							$dport_range_start = 0;
							$dport_range_end   = 65534;
							$dport_field = $dport_range_start ."-". $dport_range_end;
						} else {
							$dport_range_start = 0;
							$dport_range_end   = $dest_port - 1; 
							$dport_field = $dport_range_start ."-". $dport_range_end;
							$dport_range_start = $dest_port + 1;
							$dport_range_end   = 65535;
							$dport_field .= "," . $dport_range_start ."-". $dport_range_end;
						}
					} else {
						$last_comma = rindex($dport_field,","); if ($last_comma == -1) { $last_comma = 0; }
						if ($last_comma > 0) { $last_comma++; }
						$last_range = substr($dport_field,$last_comma,15);
						($last_start_port,$remaining) = split(/[\-]/,$last_range);

						$first_range_start = $last_start_port;
						$first_range_end   = $dest_port - 1;
						$first_range       = $first_range_start ."-". $first_range_end;

						$second_range_start = $dest_port + 1;
						$second_range_end   = 65535;
						$second_range       = $second_range_start ."-". $second_range_end;

						$dport_field = substr($dport_field,0,$last_comma);
						if ($first_range_end < $first_range_start) {
							$dport_field .= $second_range;
						} elsif ($second_range_end < $second_range_start) {
							$dport_field .= $first_range;
						} else {
							$dport_field .= $first_range .",". $second_range;
						}
					}
	                	} else {
					$num_include_dport++;
					if ($num_include_dport < 2) {
						$dport_field .= $dest_port;  
					} else {
						$dport_field .= "," . $dest_port;  
					}
	                	}
	                }
	 
			$range = 0;

	                if ($dest_ports eq "") { last; }
	        }
	 
print DEBUG "dport_field: $dport_field\n";
		$dport_field  = " --dport=" . $dport_field;

	        $save_file .= "_" . $dest_port;
	}
	 
	# Set up destination AS filtering, if any
	 
	if ($dest_ases ne "") {
	 
	        $dest_ases =~ s/\s+//g;
		$num_include_dases = 0;
	
	  	&print_error("SiLK software does not support filtering on AS at this time: $dest_ases"); last;

		while ($still_more) {
	 
	                ($dest_as) = split(/,/,$dest_ases);
	                $start_char = length($dest_as) + 1;
	                $dest_ases = substr($dest_ases,$start_char);
	 
	                if (($dest_as < -65536) || ($dest_as > 65536)) { &print_error("AS out of range -65536 < AS < 65536"); last; }
	 
	                if (substr($dest_as,0,1) eq "-") {
	                        $dest_as = substr($dest_as,1,6);
	  			&print_error("SiLK software does not support exclusion of ASes at this time: -$dest_as"); last;
	                } else {
				$num_include_dases++;
				if ($num_include_dases < 2) {
					$das_field .= $dest_as;  
				} else {
					$das_field .= "," . $dest_as;  
				}
                	}
	 
	                if ($dest_ases eq "") { last; }
	        }
	 
		$das_field  = " --das=" . $das_field;

	        $save_file .= "_" . $dest_as;
	}
	 
	# Set up Protocol filtering, if any
	
	if ($protocols ne "") {
	 
	        $protocols =~ s/\s+//g;
		$num_include_proto = 0;
	
		while ($still_more) {
	 
	                ($protocol) = split(/,/,$protocols);
	                $start_char = length($protocol) + 1;
	                $protocols = substr($protocols,$start_char);
	 
	                if (($protocol < -255) || ($protocol > 255)) { &print_error("Protocol out of range 1 < Protocol < 255"); last; }
	 
	                if (substr($protocol,0,1) eq "-") {
	                        $protocol = substr($protocol,1,3);
	  			&print_error("SiLK software does not support exclusion of Protocols at this time: -$protocol"); last;
	                } else {
				$num_include_proto++;
				if ($num_include_proto < 2) {
					$proto_field .= $protocol;  
				} else {
					$proto_field .= "," . $protocol;  
				}
                	}
	 
	                if ($protocols eq "") { last; }
	        }
	 
		$proto_field  = " --protocol=" . $proto_field;

	        $save_file .= "_" . $protocol;
	}
	
	# Set up TCP Flag filtering, if any. Note: accepting only one TCP flag/mask pair for SiLK
	
	if ($tcp_flags ne "") {
	 
	        $tcp_flags =~ s/\s+//g;
	
		$num_flags = 0;
		while ($still_more) {

			$num_flags++;
 
			if ($num_flags == 2) { &print_error("SiLK accepts only one TCP flag and mask combination"); last; }

	                ($tcp_flag) = split(/,/,$tcp_flags);
	                $start_char = length($tcp_flag) + 1;
	                $tcp_flags = substr($tcp_flags,$start_char);

			($tcp_flag,$tcp_mask) = split(/\//,$tcp_flag); 
			  
			$tcp_flag_dec = hex($tcp_flag); 
			$tcp_mask_dec = hex($tcp_mask); 
			  
			$tcp_flag_bin = dec2bin($tcp_flag_dec); 
			$tcp_mask_bin = dec2bin($tcp_mask_dec); 
			  
			for ($i=0;$i<8;$i++) { 
			        if (substr($tcp_mask_bin,$i,1) == 1) { 
			                if (substr($tcp_flag_bin,$i,1) == 1) { $tcp_flags_field .= high_flags($i); } 
			                if (substr($tcp_flag_bin,$i,1) == 0) { $tcp_flags_field .=  low_flags($i); } 
			        }    
			} 
			  
			if (substr($tcp_flags_field,0,1) eq ",") { $tcp_flags_field = substr($tcp_flags_field,1,35); } 
	 
	                if ($tcp_flags eq "") { last; }
		}
	 
		$tcp_flags_field  = " --flags-all=" . $tcp_flags_field;

	        $save_file .= "_" . $tcp_flag;
	}

	# Set up TOS Field filtering, if any (SiLK v2.4.5 doe not support TOS field)
	
	if ($tos_fields ne "") {
	 
		&print_error("SiLK does not currently support filtering on TOS field");
	}
	
	# Set up exporter address filtering, if any
	 
	if ($exporter ne "") {
	 
	        $exporter =~ s/\s+//g;
		$num_include_probe = 0;
		@valid_probes = ();
	
		# Get valid probes (exporters) from the sensor.conf file

		$probe_command = "cat $sensor_config_file | grep probe > $work_directory/valid_probes_$suffix";
		system ($probe_command);

		open (PROBES,"<$work_directory/valid_probes_$suffix");
		while (<PROBES>) {
			($probe_label,$probe) = split(/\s+/,$_);
			if ($probe_label eq "probe") { push (@valid_probes,$probe); }
		}

		while ($still_more) {
	 
	                ($exporter_name) = split(/,/,$exporter);
	                $start_char = length($exporter_name) + 1;
	                $exporter = substr($exporter,$start_char);

	                if (substr($exporter_name,0,1) eq "-") {
	  			&print_error("SiLK software does not support exclusion of Exporters (Sensors) at this time: -$exporter_name"); last;
	                } else {
                		foreach $probe (@valid_probes) { 
					if ($exporter_name eq $probe) { 
						$num_include_probe++;
						if ($num_include_probe < 2) {
							$sensor_field .= $exporter_name;  
						} else {
							$sensor_field .= "," . $exporter_name;  
						}
					}
				}
                	}
	 
	                if ($exporter eq "") { last; }
	        }
	 
		$sensor_field  = " --sensors=" . $sensor_field;

	        $save_file .= "_" . $exporter_name;
	}
	 
	# Set up Next Hop IP filtering, if any

	if ($nexthop_ips ne "") {
	 
	        $nexthop_ips =~ s/\s+//g;
		$num_include_next = 0;
		$num_exclude_next = 0;
	
		if ($nexthop_ips =~ /\.set$/) {

			$IPSET = 1;
			$still_more = 0;
			if (substr($nexthop_ips,0,1) ne "-") {
				$nh_ipset = $nexthop_ips;
			} else {
				$not_nh_ipset = substr($nexthop_ips,1,255);
			}
		}

		while ($still_more) {
	 
			$IPv4 = 0; $IPv6 = 0;

	                ($nexthop_address) = split(/,/,$nexthop_ips);
	                $start_char = length($nexthop_address) + 1;
	                $nexthop_ips = substr($nexthop_ips,$start_char);
	 
	                if ($nexthop_address =~ m/^\s*-*\d+/) {
		                $_ = $nexthop_address;
		                $num_dots   = tr/\.//; if ($num_dots   > 0) { $IPv4 = 1; }
		                $num_colons = tr/\://; if ($num_colons > 0) { $IPv6 = 1; }
			}

			if (($IPv4) && ($IPv6)) {
		                &print_error("Support for IPv4-IPv6 embedded addresses not available in this version. $nexthop_address"); last;
			}

			if ($IPv4) {

		                if ($num_dots != 3) { &print_error("Not full IPv4 address: $nexthop_address Try: n.n.n.n/m"); last; }
		 
		                ($a,$b,$c,$d)    = split(/\./,$nexthop_address);
				($nexthop_ip,$nexthop_prefix) = split(/\//,$nexthop_address);

		                if (($nexthop_prefix eq "") && ($d eq "0")) {
		                        &print_error("Missing or improper IP address prefix.  Use (e.g.) : 192.168.10.0/24."); last; }
		                if (($nexthop_prefix < 0) || ($nexthop_prefix > 32)) { 
					&print_error("Improper network mask (0 <= mask <= 32)"); last; }
		 
		                if ($a > 255 || $a eq "") { &print_error("Improper IPv4 network: $nexthop_address Try: n.n.n.n/m"); last; }
		                if ($b > 255 || $b eq "") { &print_error("Improper IPv4 network: $nexthop_address Try: n.n.n.n/m"); last; }
		                if ($c > 255 || $c eq "") { &print_error("Improper IPv4 network: $nexthop_address Try: n.n.n.n/m"); last; }
		                if ($d > 255 || $d eq "") { &print_error("Improper IPv4 network: $nexthop_address Try: n.n.n.n/m"); last; }
			}
	 
			if ($IPv6) {

		                if ($num_colons > 7) { &print_error("Improper IPv6 address: $nexthop_address.  Too many address segments."); last; }

				($nexthop_ip,$nexthop_prefix)   = split(/\//,$nexthop_address);
		                ($a,$b,$c,$d,$e,$f,$g,$h) = split(/\:/,$nexthop_address);

		                if (($nexthop_prefix < 0) || ($nexthop_prefix > 128)) { 
					&print_error("Improper IPv6 network mask (0 <= mask <= 128)"); last; }
		 
		                if (hex($a) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $a"); last; }
		                if (hex($b) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $b"); last; }
		                if (hex($c) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $c"); last; }
		                if (hex($d) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $d"); last; }
		                if (hex($e) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $e"); last; }
		                if (hex($f) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $f"); last; }
		                if (hex($g) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $g"); last; }
		                if (hex($h) > 65535) { &print_error("Improper IPv6 network. Address segment too large: $h"); last; }
			}
	 
	                if (substr($nexthop_address,0,1) eq "-") {
	                        $nexthop_address   = substr($nexthop_address,1);
				$num_exclude_next++;
				if ($num_exclude_next < 2) {
					$not_nhcidr_field .= $nexthop_address;  
				} else {
					$not_nhcidr_field .= "," . $nexthop_address;  
				}
	                } else {
				$num_include_next++;
				if ($num_include_next < 2) {
					$nhcidr_field .= $nexthop_address;  
				} else {
					$nhcidr_field .= "," . $nexthop_address;  
				}
	                }
	 
	                if ($nexthop_ips eq "") { last; }
	        }

		if (!$IPSET) {
			$nhcidr_field      = " --nhcidr="      . $nhcidr_field;
			$not_nhcidr_field  = " --not-nhcidr="  . $not_nhcidr_field;
		} else {
			$nhipset_field     = " --nhipset="     . $nh_ipset;
			$not_nhipset_field = " --not-nhipset=" . $not_nh_ipset;
			$still_more = 1;
		}

	        $save_file .= "_" . $nexthop_address;
	}

	$partitioning_switches = "";
	($field,$parameter) = split(/=/,$not_nhcidr_field);  if ($parameter ne "") { $partitioning_switches .= $not_nhcidr_field; }
	($field,$parameter) = split(/=/,$nhcidr_field);      if ($parameter ne "") { $partitioning_switches .= $nhcidr_field; }
	($field,$parameter) = split(/=/,$sensor_field);      if ($parameter ne "") { $partitioning_switches .= $sensor_field; }
	($field,$parameter) = split(/=/,$tcp_flags_field);   if ($parameter ne "") { $partitioning_switches .= $tcp_flags_field; }
	($field,$parameter) = split(/=/,$proto_field);       if ($parameter ne "") { $partitioning_switches .= $proto_field; }
	($field,$parameter) = split(/=/,$dport_field);       if ($parameter ne "") { $partitioning_switches .= $dport_field; }
	($field,$parameter) = split(/=/,$sport_field);       if ($parameter ne "") { $partitioning_switches .= $sport_field; }
	($field,$parameter) = split(/=/,$out_index_field);   if ($parameter ne "") { $partitioning_switches .= $out_index_field; }
	($field,$parameter) = split(/=/,$in_index_field);    if ($parameter ne "") { $partitioning_switches .= $in_index_field; }
	($field,$parameter) = split(/=/,$not_dcidr_field);   if ($parameter ne "") { $partitioning_switches .= $not_dcidr_field; }
	($field,$parameter) = split(/=/,$dcidr_field);       if ($parameter ne "") { $partitioning_switches .= $dcidr_field; }
	($field,$parameter) = split(/=/,$not_scidr_field);   if ($parameter ne "") { $partitioning_switches .= $not_scidr_field; }
	($field,$parameter) = split(/=/,$scidr_field);       if ($parameter ne "") { $partitioning_switches .= $scidr_field; }
	($field,$parameter) = split(/=/,$not_sipset_field);  if ($parameter ne "") { $partitioning_switches .= $not_sipset_field; }
	($field,$parameter) = split(/=/,$sipset_field);      if ($parameter ne "") { $partitioning_switches .= $sipset_field; }
	($field,$parameter) = split(/=/,$not_dipset_field);  if ($parameter ne "") { $partitioning_switches .= $not_dipset_field; }
	($field,$parameter) = split(/=/,$dipset_field);      if ($parameter ne "") { $partitioning_switches .= $dipset_field; }
	($field,$parameter) = split(/=/,$not_nhipset_field); if ($parameter ne "") { $partitioning_switches .= $not_nhipset_field; }
	($field,$parameter) = split(/=/,$nhipset_field);     if ($parameter ne "") { $partitioning_switches .= $nhipset_field; }

	return $partitioning_switches;
}

sub convert_octets2string { 

        my ($octets) = @_; 
        my $res; 
        my $unit=0; 
    
        $res = $octets; 
        while ($res > 1024) {  
               $res = $res/1024; 
               $unit = $unit +1; 
        }        
    
        if ($unit == 0) {  
            $res = sprintf("%.0f" , $res); 
        } elsif ($unit == 1) {  
            $res = sprintf("%.2f KB" , $res); 
        } elsif ($unit == 2) {  
            $res = sprintf("%.2f MB" , $res); 
        } elsif ($unit == 3) {  
            $res = sprintf("%.2f GB" , $res); 
        } elsif ($unit == 4) {
            $res = sprintf("%.2f TB" , $res);
        } else {  
            $res = sprintf("%.2f PB" , $res); 
        }        
        return $res; 
}

sub dec2bin { 
        my $str = unpack("B32", pack("N", shift)); 
        $str = substr($str,24,8); 
	return $str; 
} 
  
sub high_flags { 
        if ($i == 0) { $flag_value = ",C/C"; } 
        if ($i == 1) { $flag_value = ",E/E"; } 
        if ($i == 2) { $flag_value = ",U/U"; } 
        if ($i == 3) { $flag_value = ",A/A"; } 
        if ($i == 4) { $flag_value = ",P/P"; } 
        if ($i == 5) { $flag_value = ",R/R"; } 
        if ($i == 6) { $flag_value = ",S/S"; } 
        if ($i == 7) { $flag_value = ",F/F"; } 
        return $flag_value; 
} 
  
sub low_flags { 
        if ($i == 0) { $flag_value = ",/C"; }
        if ($i == 1) { $flag_value = ",/E"; }
        if ($i == 2) { $flag_value = ",/U"; }
        if ($i == 3) { $flag_value = ",/A"; }
        if ($i == 4) { $flag_value = ",/P"; }
        if ($i == 5) { $flag_value = ",/R"; }
        if ($i == 6) { $flag_value = ",/S"; }
        if ($i == 7) { $flag_value = ",/F"; }
        return $flag_value;
}

sub dig_forward {
        my ($host_name) = @_;

        open(DIG,"$dig_forward $host_name 2>&1|");
        $answer_record = 0;
        while (<DIG>) {
                chop;
                if (/ANSWER SECTION/) {
                        $answer_record = 1;
                        next;
                }
                if ($answer_record) {
                        ($in_name,$rec_timeout,$rec_direction,$rec_type,$host_ip) = split(/\s+/,$_);
                        last;
                }
        }
        return $host_ip;
}

return 1;
