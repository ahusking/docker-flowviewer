#! /usr/bin/perl
#
#  Purpose:
#  FlowViewer_SaveManage.cgi creates the web page for managing
#  previously saved reports (i.e., Modify, Remove, Archive, Restart.)
#
#  Description:
#
#  FlowViewer_SaveManage.cgi parses through existing saved reports 
#  and graphs and creates the management web-page.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  action               Modify, Remove, Archive, Restart
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Original Version.
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

if ($debug_monitor eq "Y") { open (DEBUG,">$work_directory/DEBUG_SAVE"); }
if ($debug_monitor eq "Y") { print DEBUG "In FlowViewer_SaveManage.cgi\n"; }

($active_dashboard,$action,$remove_file) = split(/\^/,$ENV{'QUERY_STRING'});

if ($debug_monitor eq "Y") { print DEBUG "active_dashboard: $active_dashboard  action: $action  remove_file: $remove_file\n"; }

if (($action eq "RemoveFile") || ($action eq "RemoveFilter")) {
	$move_command = "mv $save_directory/$remove_file $work_directory";
	system($move_command);
	if ($remove_file =~ "Graph") { $move_command = "mv $save_directory/$remove_file.png $work_directory"; }
	system($move_command);
}

&create_UI_top($active_dashboard);
&create_UI_service("FlowViewer","service_top",$active_dashboard,$filter_hash);
&create_UI_sides($active_dashboard);

if (($action eq "ListFiles") || ($action eq "RemoveFile")) {

	# Create a list of Saved Report together with a Remove link
	
	print " <div id=content_scroll>\n";
	print "<br><b>Saved Reports</b><br><br>\n\n";
	print "  <table>\n";
	
	@saved_files = ();
	while ($saved_file = <$save_directory/*>) {
	
                $info_file = $saved_file;

	        ($directory,$saved_label) = $saved_file =~ m/(.*\/)(.*)$/;
	        $length_label = length($saved_label);
	        $start_suffix = $length_label - 4;
	        $label_suffix = substr($saved_label,$start_suffix,4);
	        if (($label_suffix eq ".svf") || ($label_suffix eq ".png")) { next; }
	
	        if ($saved_label =~ /FlowGrapher/) {
	                $created_initials = "FG";
	        } elsif ($saved_label =~ /FlowViewer/) {
	                $created_initials = "FV";
	        } elsif ($saved_label =~ /FlowMonitor/) {
	                $created_initials = "FM";
			$MT_saved_directory = $saved_file ."/*";
			$find_command = "ls $MT_saved_directory \| grep \"\.fil\"";
			open(LS,"$find_command |");
			$info_file = <LS>;
 			close(LS);
			if ($info_file eq "") {
				$find_command = "ls $MT_saved_directory \| grep \"\.grp\"";
				open(LS,"$find_command |");
				$info_file = <LS>;
	 			close(LS);
			}
			$last_slash = rindex($info_file,"/");
			$last_dot   = rindex($info_file,"\.");
			$ft_length  = $last_dot - $last_slash - 1;
			$flowmonitor = substr($info_file,$last_slash+1,$ft_length);
			$remove_label = $saved_label;
			$saved_label = $saved_label ."_". $flowmonitor;
	        } elsif ($saved_label =~ /graph/) {
	                $created_initials = "FG";
	        } else {
	                $created_initials = "FV";
	        }
	
		$sv_report_name = substr($saved_label,16,255);
		$sv_report_name = substr($sv_report_name,0,-5);
	        open (SAVED_FILE,"<$info_file");
	        while (<SAVED_FILE>) {
	                if (/Description/) {
	                        chop $_;
	                        ($label,$sv_report_name) = split(": ",$_);
                                if ($saved_file =~ /FlowMonitor/) { ($input_label,$label,$sv_report_name) = split(": ",$_); }
	                }
                        if (/create_time/) {  
                                chop $_;  
                                ($label,$create_time) = split(": ",$_); 
				if ($saved_file =~ /FlowMonitor/) { ($input_label,$label,$create_time) = split(": ",$_); }
                        }    
                        if (/filter_hash/) {  
                                chop $_;  
                                ($label,$saved_filter_hash) = split(": ",$_); 
				if ($saved_filter_hash =~ /FA/) { $created_initials = "FA"; }
				last;
                        }    
	        }
	        close SAVED_FILE;
	
                $label_key = substr($saved_label,0,2);
                if ($label_key eq "20") {
                        $label_stamp = substr($saved_label,0,15);
                        ($label_date,$label_time) = split(/_/,$label_stamp);
                        $label_date = substr($label_date,4,2) ."/". substr($label_date,6,2) ."/". substr($label_date,0,4);
                        $label_time = substr($label_time,0,2) .":". substr($label_time,2,2) .":". substr($label_time,4,2);
                        $last_access = date_to_epoch($label_date,$label_time);
                } else {
                        $last_access = $create_time;
                }

	        $saved_listing = $last_access ."^". $saved_label ."^". $sv_report_name ."^". $created_initials;
	        push (@saved_files,$saved_listing);
	}
	
	@temp_saved_files   = sort (@saved_files);
	@sorted_saved_files = reverse (@temp_saved_files);
	
	$first_time = 1;
	foreach $sorted_listing (@sorted_saved_files) {
	        ($last_access,$saved_label,$sv_report_name,$created_initials) = split(/\^/,$sorted_listing);
	        if (($saved_label =~ /html/) || (!($saved_label =~ /\./))) {
	                if (($saved_label =~ /index/) || ($sorted_listing eq "")) { next; }
	                $file_date = epoch_to_date($last_access);
	                $mn = substr($file_date,0,2);
			if ($first_time) { $last_mn = $mn; $first_time = 0; }
	                if  ($mn ne $last_mn) { print  "<tr><td>&nbsp</td><td>&nbsp</td></tr>\n"; }
	
	                if ($saved_label =~ /FlowGrapher/) {
	                        $saved_link = "a href=$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=FG_$saved_label";
	                } elsif ($saved_label =~ /FlowViewer/) {
	                        $saved_link = "a href=$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=FV_$saved_label";
                        } elsif ($saved_label =~ /FlowMonitor/) {
				$remove_label = substr($saved_label,0,25);
	                        $saved_link = "a href=$cgi_bin_short/FlowMonitor_Replay.cgi?$active_dashboard^filter_hash=SV_$saved_label";
	                } elsif ($saved_label =~ /graph/) {
	                        $saved_link = "a href=$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=PV_$saved_label";
	                } else {
	                        $saved_link = "a href=$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=PV_$saved_label";
	                }
	
			$remove_link  = "<a href=$cgi_bin_short/FlowViewer_SaveManage.cgi?$active_dashboard^RemoveFile^$saved_label>Remove</a>";
                        if ($saved_label =~ /FlowMonitor/) {
				$remove_link  = "<a href=$cgi_bin_short/FlowViewer_SaveManage.cgi?$active_dashboard^RemoveFile^$remove_label>Remove</a>";
			}
	
			($file_date_out,$file_time_out) = split(/ /,$file_date);
			print "  <tr>\n";
			print "  <td>$file_date_out</td>\n";
			print "  <td>&nbsp</td>\n";
			print "  <td>$file_time_out</td>\n";
			print "  <td>&nbsp&nbsp&nbsp</td>\n";
			print "  <td class=tr_action>$created_initials</td>\n";
			print "  <td>&nbsp&nbsp&nbsp</td>\n";
			print "  <td class=sv_label><$saved_link>$sv_report_name</td>\n";
			print "  <td class=tr_action>$remove_link</td>\n";
			print "  </tr>\n";
	
			$last_mn = $mn;
		}
	}

	print "  </table>\n";
	print " </div>\n";
}

if (($action eq "ListFilters") || ($action eq "RemoveFilter")) {

	# Create a list of Saved Filters together with a Remove link
	
	print " <div id=content_scroll>\n";
	print "<br><b>Saved Filters</b><br><br>\n\n";
	print "  <table>\n";
	
	while ($saved_filter = <$save_directory/*>) {
	
	        ($directory,$saved_label) = $saved_filter =~ m/(.*\/)(.*)$/;
	        $length_label = length($saved_label);
	        $start_suffix = $length_label - 4;
	        $label_suffix = substr($saved_label,$start_suffix,4);
	        if ($label_suffix ne ".svf") { next; }
		$saved_label  = substr($saved_label,0,$start_suffix);
	
	        open (SAVED_FILE,"<$saved_filter");
	        while (<SAVED_FILE>) {
	                if (/filter_title/) {
	                        chop $_;
	                        ($label,$sv_filter_name) = split(": ",$_);
	                }
	        }
	        close SAVED_FILE;
		
	        $saved_listing = $saved_label ."^". $sv_filter_name;
	        push (@saved_filters,$saved_listing);
	}

	@sorted_saved_filters   = sort (@saved_filters);
	
	foreach $sorted_listing (@sorted_saved_filters) {
	        ($saved_label,$sv_filter_name) = split(/\^/,$sorted_listing);
		$remove_link = "<a href=$cgi_bin_short/FlowViewer_SaveManage.cgi?$active_dashboard^RemoveFilter^$saved_label.svf>Remove</a>";
	        $saved_link  = "<a href=$cgi_bin_short/FlowViewer.cgi?$active_dashboard^filter_hash=FL_$saved_label>$sv_filter_name</a>";
	
		print "  <tr>\n";
		print "  <td class=sv_label>$saved_link</td>\n";
		print "  <td class=tr_action>$remove_link</td>\n";
		print "  </tr>\n";
	}

	print "  </table>\n";
	print " </div>\n";
}

&create_UI_service("FlowViewer","service_bottom",$active_dashboard,$filter_hash);
&finish_the_page("FlowViewer");
