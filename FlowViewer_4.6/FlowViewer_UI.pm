#! /usr/bin/perl
#
#  Purpose:  
#  FlowViewer_UI.pm holds utility functions that are called 
#  by FlowViewer, FlowGrapher, and FlowMonitor scripts to create
#  the version 4.0 User Interface.
#
#  Description:
#  Various user interface utility functions.
#
#  Input arguments:
#  Name                 Description
#  -----------------------------------------------------------------------
#  None
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  05/08/2012      4.0     Original Version.
#  J. Loiacono  08/07/2013      4.2     Fixed exporter NamedInterfaces [M. Donnelly]
#  J. Loiacono  09/11/2013      4.2.1   Mods to accomodate new Linear processing
#                                       Mods for international date formatting
#  J. Loiacono  01/26/2014      4.3     Introduced Detect Scanning
#  J. Loiacono  07/04/2014      4.4     Multiple dashboards and Analysis
#  J. Loiacono  11/02/2014      4.5     FlowTracker to FlowMonitor rename
#                                       Added option to eliminate bottom pulldowns
#  J. Loiacono  01/26/2015      4.6     Timezone from system (not Configuration)
#                                       Fixed wrong listing of very old Saved files
#
#$Author$
#$Date$
#$Header$
#
###########################################################################
#
#               BEGIN EXECUTABLE STATEMENTS
#
 
use File::stat;
use Time::Local;
use Time::HiRes qw( usleep ualarm gettimeofday tv_interval );

sub create_UI_top {

	my ($active_dashboard) = @_;
	$active_dashboard =~ s/\\//;

	# Create the top FlowViewer title and Local Information

	print  "Content-type:text/html\n\n";
	print  "<!DOCTYPE html PUBLIC \"-//W3C//DTD HTML 4.01//EN\"\n";
	print  "\"http://www.w3.org/TR/html4/strict.dtd\">\n\n";
	print  "<html lang=en>\n";
	print  "<head>\n";
	print  "<meta http-equiv=Content-Type content=\"text/html; charset=utf-8\">\n";
	print  "<title>FlowViewer - Maintaining Network Traffic Situational Awareness</title>\n";
	print  "<link rel=\"stylesheet\" href=\"$reports_short/FlowViewer.css\" type=\"text/css\">\n";
	print  "</head>\n";
	print  "<body>\n";
	print  "<center>\n";
	print  "<br>\n";
	print  "\n";

	print  "<div id=container>\n";
	print  " <div id=title_left>\n";
	if ($active_dashboard ne "Main_Only") {
		foreach $dashboard_title (@dashboard_titles) {
                	$dashboard_name = $dashboard_title;
			$dashboard_name =~ s/ /~/;
			if ($dashboard_name eq $active_dashboard) { next; }
			$dashboard_link = "$cgi_bin_short/FV.cgi?$dashboard_name";
			print  "  <a href=$dashboard_link><span class=link16>$dashboard_title&nbsp&nbsp&nbsp</span></a>\n";
		}
	} else {
		print  "  <a href=$left_title_link><span class=link16>$left_title</span></a>\n";
	}
	print  " </div>\n";
	print  " <div id=title_right>\n";
	if ($active_dashboard ne "Main_Only") {
		$dashboard_name = $active_dashboard;
		$dashboard_name =~ s/\~/ /;
		$dashboard_link = "$cgi_bin_short/FV.cgi?$active_dashboard";
		print  "  <a href=$dashboard_link><span class=link16>Active Dashboard: $dashboard_name</span></a>\n";
	} else {
		print  "  <a href=$right_title_link><span class=link16>$right_title</span></a>\n";
	}
	print  " </div>\n";
	print  " <div id=title_center>\n";
	print  "  <a href=$cgi_bin_short/FV.cgi><span class=text20>FlowViewer</span></a>\n";
	print  "  <p>\n";
	print  "  <a href=$cgi_bin_short/FV.cgi><span class=text12>Powered by flow-tools and SiLK</span></a>\n";
	print  " </div>\n";
	print  "\n";
}

sub create_UI_service {

	my ($called_by,$service_location,$active_directory,$filter_hash) = @_;

	print  " <div id=$service_location>\n";

	if ($service_location eq "service_top") {

		@filters = (); @actives = (); @groups = (); @archives = ();
		@filters = <$filter_directory/*>; 
		foreach $filter_file (@filters) { 
			if    ($filter_file =~ /\.fil/)     { push (@actives,$filter_file); }
			elsif ($filter_file =~ /\.grp/)     { push (@groups,$filter_file); }
			elsif ($filter_file =~ /\.archive/) { push (@archives,$filter_file); }
		}

		@actives  = sort(@actives); unshift (@actives,"start_actives");
		@groups   = sort(@groups); unshift (@groups,"start_groups");
		@archives = sort(@archives); unshift (@archives,"start_archives");
		@filters  = (@actives, @groups, @archives);
 
	}

	# Create the left-side Active Monitors pulldown

	if (($service_location eq "service_top") || (($service_location eq "service_bottom") && ($use_bottom_pulldowns eq "Y"))) {

		print  "  <select class=monitors_left name=monitors onchange=window.location.href=this[selectedIndex].value\;>\n";
		print  "   <option selected value=\"\">Select an Active or Archived FlowMonitor</option>\n";
		print  "   <option disabled> </option>\n";
		print  "   <option value=$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^List^>   Manage All FlowMonitors</option>\n";
	
		foreach $filter_file (@filters) { 
	
			if ($filter_file eq "start_actives") { 
				print "   <option disabled> </option>\n";
				print "   <option disabled>--- Individuals</option>\n";
				print "   <option disabled> </option>\n"; 
				next;
			} elsif ($filter_file eq "start_groups") {
				print "   <option disabled> </option>\n";
				print "   <option disabled>--- Groups</option>\n";
	                        print "   <option disabled> </option>\n"; 
				next;
			} elsif ($filter_file eq "start_archives") {
				print "   <option disabled> </option>\n";
				print "   <option disabled>--- Archives</option>\n";
				print "   <option disabled> </option>\n"; 
				next;
			}
	
		        $monitor_file = $filter_file;
		        $monitor_file =~ s#.*/##;  
		        open (FILTER,"<$filter_file");  
		        while (<FILTER>) {  
		                chop;    
		                $key = substr($_,0,8); 
		                if ($key eq " input: ") { 
		                        ($input,$field,$field_value) = split(/: /);  
		                        if (($field eq "monitor_label") || ($field eq "tracking_label"))  {    
		                                $ft_monitor_label  = $field_value; 
		                                ($monitor_prefix,$monitor_suffix) = split(/\./,$monitor_file); 
		                                $ft_filter_hash = "MT_" . $monitor_prefix;
						print  "   <option value=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$ft_filter_hash>$ft_monitor_label</option>\n";
					}
				}
			}
			close(FILTER);
		}

		print  "  </select>\n";

	} else  {

		print "  <span class=pulldown_spacer></span>\n";
	}
	
	if ($called_by =~ /FlowViewer/) {

		print "  <span class=button_lead></span>\n";
		if (($called_by =~ /Main/) && ($service_location eq "service_bottom")) { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_filter^$filter_hash\">\n";
			print "  <button class=links type=submit>Save Filter</button>\n";
		} else { 
			print "  <form method=post action=\"$cgi_bin_short/FlowGrapher.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
			print "  <button class=links type=submit>FlowGrapher</button>\n";
		}
		print "  </form>\n";
		print "  <span class=button_spacer></span>\n";
		print "  <form method=post action=\"$cgi_bin_short/FlowViewer.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
		print "  <button class=active type=submit>FlowViewer</button>\n";
		print "  </form>\n";
		print "  <span class=button_spacer></span>\n";
		if (($called_by =~ /Main/) && ($service_location eq "service_bottom")) { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_report^$filter_hash\">\n";
			print "  <button class=links type=submit>Save Report</button>\n";
		} else {
			print "  <form method=post action=\"$cgi_bin_short/FlowMonitor.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
			print "  <button class=links type=submit>FlowMonitor</button>\n";
		}
		print "  </form>\n";

	} elsif ($called_by =~ /FlowGrapher/) {

		print "  <span class=button_lead></span>\n";
		if (($called_by =~ /Main/) && ($service_location eq "service_bottom")) { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_filter^$filter_hash\">\n";
			print "  <button class=links type=submit>Save Filter</button>\n";
		} else { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
			print "  <button class=links type=submit>FlowViewer</button>\n";
		}
		print "  </form>\n";
		print "  <span class=button_spacer></span>\n";
		print "  <form method=post action=\"$cgi_bin_short/FlowGrapher.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
		print "  <button class=active type=submit>FlowGrapher</button>\n";
		print "  </form>\n";
		print "  <span class=button_spacer></span>\n";
		if (($called_by =~ /Main/) && ($service_location eq "service_bottom")) { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_report^$filter_hash\">\n";
			print "  <button class=links type=submit>Save Report</button>\n";
		} else {
			print "  <form method=post action=\"$cgi_bin_short/FlowMonitor.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
			print "  <button class=links type=submit>FlowMonitor</button>\n";
		}
		print "  </form>\n";
	
	} elsif ($called_by =~ /FlowMonitor/) {

		print "  <span class=button_lead></span>\n";
		if (($called_by =~ /Display/) && ($service_location eq "service_bottom")) { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_filter^$filter_hash\">\n";
			print "  <button class=links type=submit>Save Filter</button>\n";
		} else { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
			print "  <button class=links type=submit>FlowViewer</button>\n";
		}
		print "  </form>\n";
		print "  <span class=button_spacer></span>\n";
		print "  <form method=post action=\"$cgi_bin_short/FlowMonitor.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
		print "  <button class=active type=submit>FlowMonitor</button>\n";
		print "  </form>\n";
		print "  <span class=button_spacer></span>\n";
		if (($called_by =~ /Display/) && ($service_location eq "service_bottom")) { 
			print "  <form method=post action=\"$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^name_report^$filter_hash\">\n";
			print "  <button class=links type=submit>Save Report</button>\n";
		} else {
			print "  <form method=post action=\"$cgi_bin_short/FlowGrapher.cgi?$active_dashboard^filter_hash=$filter_hash\">\n";
			print "  <button class=links type=submit>FlowGrapher</button>\n";
		}
		print "  </form>\n";
	}

	# Create the right-side Saved Reports pulldown

	if (($service_location eq "service_top") || (($service_location eq "service_bottom") && ($use_bottom_pulldowns eq "Y"))) {

		print  "  <select class=monitors_right name=saved onchange=window.location.href=this[selectedIndex].value;>\n";
		print  "   <option selected value=\"\">Select a Saved Report</option>\n";
		print  "   <option disabled> </option>\n";
		print  "   <option value=$cgi_bin_short/FlowViewer_SaveManage.cgi?$active_dashboard^ListFiles>   Manage All Saved Reports</option>\n";
	
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
			} elsif (($saved_label =~ /FlowMonitor/) || ($saved_label =~ /FlowTracker/)) {
				$created_initials = "FM";
				$MT_saved_directory = $save_directory ."/". $saved_label;
	        		open(LS,"ls $MT_saved_directory 2>&1|");
	        		while (<LS>) {
					if ((/\.fil/) || (/\.grp/)) { 
						$info_file = $MT_saved_directory ."/". $_;
						($MT_label,$MT_suffix) = split(/\./);
						$saved_label = $saved_label ."_". $MT_label;
					}
	        		}
			} elsif ($saved_label =~ /graph/) {
				$created_initials = "FG";
			} else {
				$created_initials = "FV";
			}
	
			$last_underscore = rindex($saved_label,"_"); $len_label = $last_underscore - 16; 
			$sv_report_name = substr($saved_label,16,$len_label);
	
			$create_time = "";
	                open (SAVED_FILE,"<$info_file"); 
	                while (<SAVED_FILE>) { 
	                        if (/Description/) {  
	                                chop $_;  
	                                ($label,$sv_report_name) = split(": ",$_); 
					if (($saved_file =~ /FlowMonitor/) || ($saved_file =~ /FlowTracker/)) { ($input_label,$label,$sv_report_name) = split(": ",$_); }
	                        }    
	                        if (/create_time/) {  
	                                chop $_;  
	                                ($label,$create_time) = split(": ",$_); 
					if (($saved_file =~ /FlowMonitor/) || ($saved_file =~ /FlowTracker/)) { ($input_label,$label,$create_time) = split(": ",$_); }
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
				if ($create_time ne "") {
					$last_access = $create_time;
				} else {
					$last_access = stat($info_file)->mtime;
				}
			}
	                $saved_listing = $last_access ."^". $saved_label ."^". $sv_report_name ."^". $created_initials; 
	                push (@saved_files,$saved_listing); 
	        }    
	 
	        @temp_saved_files = sort (@saved_files); 
	        @sorted_saved_files = reverse (@temp_saved_files); 
	 
		$last_mn = "";
	        foreach $sorted_listing (@sorted_saved_files) { 
	                ($last_access,$saved_label,$sv_report_name,$created_initials) = split(/\^/,$sorted_listing);    
	                if (($saved_label =~ /html/) || (!($saved_label =~ /\./))) {  
	                        if (($saved_label =~ /index/) || ($sorted_listing eq "")) { next; }
				$file_date = epoch_to_date($last_access);
				$mn = substr($file_date,0,2);
	 
	                        if  ($mn ne $last_mn) { print  "   <option disabled></option>\n"; }
	 
				$sv_report_title = "$file_date &nbsp&nbsp $created_initials &nbsp&nbsp $sv_report_name";
	
				if ($saved_label =~ /FlowGrapher/) {
					print  "   <option value=$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=FG_$saved_label>$sv_report_title</option>\n";
				} elsif ($saved_label =~ /FlowViewer/) {
					print  "   <option value=$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=FV_$saved_label>$sv_report_title</option>\n";
				} elsif (($saved_label =~ /FlowMonitor/) || ($saved_label =~ /FlowTracker/)) {
					print  "   <option value=$cgi_bin_short/FlowMonitor_Replay.cgi?$active_dashboard^filter_hash=SV_$saved_label>$sv_report_title</option>\n";
				} elsif ($saved_label =~ /graph/) {
					print  "   <option value=$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=PV_$saved_label>$sv_report_title</option>\n";
				} else {
					print  "   <option value=$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=PV_$saved_label>$sv_report_title</option>\n";
				}
	
	                        $last_mn = $mn;
	                }
	        }
	
		print  "  </select>\n";
	}

	print  " </div>\n";
}

sub create_UI_sides {

	my ($active_dashboard) = @_;

	$switch_dashboard = $active_dashboard;
	$switch_dashboard =~ s/\~/ /;
	$active_db_directory = $dashboard_directory;
	for ($i=0;$i<=$#dashboard_titles;$i++) {
		if (($dashboard_titles[$i] eq $switch_dashboard) && ($i > 0)) { $active_db_directory = $other_dashboards[$i-1]; }
	}

        while ($dashboard_file = <$active_db_directory/*>) {  

                ($directory,$thumbnail_file) = $dashboard_file =~ m/(.*\/)(.*)$/; 

		($th_filter_hash,$suffix) = split(/\./,$thumbnail_file);
		$last_underscore = rindex($th_filter_hash,"_"); $th_filter_hash = substr($th_filter_hash,0,$last_underscore);
		$last_underscore = rindex($th_filter_hash,"_"); $th_filter_hash = substr($th_filter_hash,0,$last_underscore);
		$th_filter_hash = "MT_" . $th_filter_hash;

		$last_slash = rindex($active_db_directory,"/");
		$active_short = substr($active_db_directory,$last_slash+1,255);
		$thumbnail_file = "/$active_short/$thumbnail_file";

		if ($dashboard_file =~ "_1.png") { 
			$side_thumbnails{pos_1} = $thumbnail_file;
			$side_hash{pos_1}       = $th_filter_hash; }
		if ($dashboard_file =~ "_2.png") { 
			$side_thumbnails{pos_2} = $thumbnail_file;
			$side_hash{pos_2}       = $th_filter_hash; }
		if ($dashboard_file =~ "_3.png") { 
			$side_thumbnails{pos_3} = $thumbnail_file;
			$side_hash{pos_3}       = $th_filter_hash; }
		if ($dashboard_file =~ "_4.png") { 
			$side_thumbnails{pos_4} = $thumbnail_file;
			$side_hash{pos_4}       = $th_filter_hash; }
		if ($dashboard_file =~ "_5.png") { 
			$side_thumbnails{pos_5} = $thumbnail_file;
			$side_hash{pos_5}       = $th_filter_hash; }
		if ($dashboard_file =~ "_6.png") { 
			$side_thumbnails{pos_6} = $thumbnail_file;
			$side_hash{pos_6}       = $th_filter_hash; }
		if ($dashboard_file =~ "_7.png") { 
			$side_thumbnails{pos_7} = $thumbnail_file;
			$side_hash{pos_7}       = $th_filter_hash; }
		if ($dashboard_file =~ "_8.png") { 
			$side_thumbnails{pos_8} = $thumbnail_file;
			$side_hash{pos_8}       = $th_filter_hash; }
	}

	# Create the left side with Dashboard FlowMonitor Thumbnails

	print " <div id=left_main>\n";
	if ($side_thumbnails{pos_1} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_1}>\n";
		print " <img class=linked src=$side_thumbnails{pos_1} border=0></a>\n";
	} else {
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
	}
	if ($side_thumbnails{pos_3} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_3}>\n";
		print " <img class=linked src=$side_thumbnails{pos_3} border=0></a>\n"; }
	if ($side_thumbnails{pos_5} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_5}>\n";
		print " <img class=linked src=$side_thumbnails{pos_5} border=0></a>\n"; }
	if ($side_thumbnails{pos_7} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_7}>\n";
		print " <img class=linked src=$side_thumbnails{pos_7} border=0></a>\n"; }
	print " </div>\n";

	# Create the right side with Dashboard FlowMonitor Thumbnails

	print " <div id=right_main>\n";
	if ($side_thumbnails{pos_2} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_2}>\n";
		print " <img class=linked src=$side_thumbnails{pos_2} border=0></a>\n";
	} else {
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
		print "&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp\n";
	}
	if ($side_thumbnails{pos_4} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_4}>\n";
		print " <img class=linked src=$side_thumbnails{pos_4} border=0></a>\n"; }
	if ($side_thumbnails{pos_6} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_6}>\n";
		print " <img class=linked src=$side_thumbnails{pos_6} border=0></a>\n"; }
	if ($side_thumbnails{pos_8} ne "") {
		print " <a href=$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=$side_hash{pos_8}>\n";
		print " <img class=linked src=$side_thumbnails{pos_8} border=0></a>\n"; }
	print " </div>\n";
}

sub finish_the_page {

	my ($called_by) = @_;

	# Finish the web page

	print  "</div>\n";
	print  "</body>\n";
	print  "</html>\n";
}

sub create_filtering_form {

	($called_by,$filter_hash) = @_;

	if ($called_by eq "FlowViewer")  { print " <form method=post action=$cgi_bin_short/FlowViewer_Main.cgi>\n"; }
	if ($called_by eq "FlowGrapher") { print " <form method=post action=$cgi_bin_short/FlowGrapher_Main.cgi>\n"; }
	if ($called_by eq "FlowMonitor") { print " <form method=post action=$cgi_bin_short/FlowMonitor_Main.cgi>\n"; }
	if ($called_by eq "FlowMonitor_Sol") { print " <form method=post action=$cgi_bin_short/FlowMonitor_Main.cgi?$active_dashboard^Revise^$filter_hash>\n"; $skip_date = "Y";}
		
	load_filtering_parameters($called_by,$filter_hash);

	if ($new_device   ne "") { $form_device_name = $new_device; }
	if ($new_exporter ne "") { $form_exporter    = $new_exporter; }

	print " <fieldset class=level1>\n";
	if ($called_by eq "FlowViewer" ) { print "  <legend class=level1>&nbspCreate a FlowViewer Report</legend>\n"; }
	if ($called_by eq "FlowGrapher") { print "  <legend class=level1>&nbspCreate a FlowGrapher Report</legend>\n"; }
	if ($called_by eq "FlowMonitor") { print "  <legend class=level1>&nbspCreate a FlowMonitor</legend>\n"; }
	if ($called_by =~ "FlowMonitor_Sol") { 
		$monitor_hash = $form_monitor_label;
		$monitor_hash =~ s/ /~/g;
		print "  <legend class=level1>&nbspRevise FlowMonitor: $form_monitor_label</legend>\n";
	}
	print "\n";

	# List the saved filters in the pulldown

	print "  <fieldset class=level2_float>\n";
	print "   <legend class=level2>Saved Filters</legend>\n";
	print "   <span class=select>\n";
	print "    <select class=long name=saved_filter onchange=window.location.href=this[selectedIndex].value\;>\n";

	if (($filter_source eq "FL") && ($new_device eq "") && ($new_exporter eq "")) { 
		print "     <option value=$cgi_bin_short/$called_by.cgi?$active_dashboard^>Select Saved Filter</option>\n";
		print "     <option disabled> </option>\n";
		print "     <option value=$cgi_bin_short/FlowViewer_SaveManage.cgi?$active_dashboard^ListFilters>   Manage All Saved Filters</option>\n";
		print "     <option disabled> </option>\n";
	} else {
		print "     <option selected>Select Saved Filter</option>\n";
		print "     <option disabled> </option>\n";
		print "     <option value=$cgi_bin_short/FlowViewer_SaveManage.cgi?$active_dashboard^ListFilters>   Manage All Saved Filters</option>\n";
		print "     <option disabled> </option>\n";
	}

        open(GREP,"grep filter_title $save_directory/\*.svf 2>&1|");
        while (<GREP>) {
		chop;
		$num_colons = tr/://;
		if ($num_colons == 1) {
			($filter_label,$saved_title) = split(/:/);
		        $filter_label = $saved_title;
		        $filter_label =~ s/^\s+//;
		        $filter_label =~ s/\s+$//;
		        $filter_label =~ s/\&/-/g;
		        $filter_label =~ s/\//-/g;
		        $filter_label =~ s/\(/-/g;
		        $filter_label =~ s/\)/-/g;
		        $filter_label =~ s/\./-/g;
		        $filter_label =~ s/\s+/_/g;
		        $filter_label =~ tr/[A-Z]/[a-z]/;
			$saved_file = "$save_directory/$filter_label.svf";
		} else {
			($saved_file,$filter_label,$saved_title) = split(/:/);
		}
		$saved_title = substr($saved_title,1,255);
		if ($saved_title eq "No such file or directory") { $saved_title = "No Filters saved yet"; }
		($directory,$file_name) = $saved_file =~ m/(.*\/)(.*)$/;
		$file_name = substr($file_name,0,-4);
		$saved_hash = "FL_" . $file_name;
		if (($filter_source eq "FL") && ($saved_title eq $filter_title)) {
			print "     <option selected value=$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=$saved_hash>$saved_title</option>\n";
		} else { 
			print "     <option value=$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=$saved_hash>$saved_title</option>\n";
		}
        }
	close(GREP);

	print "    </select>\n";
	print "   </span>\n";
	print "   <span class=saved_spacer></span>\n";
	print "  </fieldset>\n";
	print "\n";

	# Prepare the Device and Exporter pulldowns

	if (($form_device_name eq "") && ($ipfix_default_device ne "")) { $form_device_name = $ipfix_default_device; }

	$IPFIX = 0;
	foreach $ipfix_device (@ipfix_devices) {
		if ($form_device_name eq $ipfix_device) { $IPFIX = 1; }
	}

	print "  <fieldset class=level2>\n";
	print "   <legend class=level2>Netflow Source</legend>\n";
	print "   <span class=select>\n";

	if ($IPFIX) {
		print "    <select class=shortie name=device_name onchange=window.location.href=this[selectedIndex].value\;>\n";
	} else {
		print "    <select class=med name=device_name onchange=window.location.href=this[selectedIndex].value\;>\n";
	}

        if ($form_device_name ne "") {
		if ($called_by eq "FlowMonitor_Sol") {
			print "    <option value=$cgi_bin_short/FlowMonitor.cgi?$active_dashboard^>Select Device</option>\n";
		} else {
			print "    <option value=$cgi_bin_short/$called_by.cgi?$active_dashboard^>Select Device</option>\n";
		}
		print "    <option disabled> </option>\n";
        } else {  
		if ($called_by eq "FlowMonitor_Sol") {
			print "    <option selected value=$cgi_bin_short/FlowMonitor.cgi?$active_dashboard^>Select Device</option>\n";
		} else {
			print "    <option selected value=$cgi_bin_short/$called_by.cgi?$active_dashboard^>Select Device</option>\n";
		}
		print "    <option disabled> </option>\n";
        }

	@all_devices = (@devices,@ipfix_devices);
	if ($all_devices[0] ne "") {
        	foreach $all_device_name (@all_devices) {
			if ($all_device_name eq $form_device_name) {
				if ($called_by eq "FlowMonitor_Sol") {
					$device_hash = $monitor_hash ."^DDD". $form_device_name;
        				$option_value = "$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Solicit^$device_hash";
				} else {
					$device_hash = $filter_hash ."^DDD". $form_device_name;
        				$option_value = "$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=$device_hash";
				}
				print "    <option selected value=$option_value>$form_device_name</option>\n";
			} else { 
				if ($called_by eq "FlowMonitor_Sol") {
					$device_hash = $monitor_hash ."^DDD". $all_device_name;
        				$option_value = "$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Solicit^$device_hash";
				} else {
					$device_hash = $filter_hash ."^DDD". $all_device_name;
        				$option_value = "$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=$device_hash";
				}
				print "    <option value=$option_value>$all_device_name</option>\n";
			}
		}
	}

        print "    </select>\n";
	print "   </span>\n";

	if ($IPFIX) {

		if (($form_silk_rootdir eq "") || ($new_device ne "")) {
			$grep_command = "grep path-format $silk_data_directory/silk.conf";
			open(GREP,"$grep_command 2>&1|"); 
			while (<GREP>) {
				chop;
				($left_part,$path_format) = split(/path-format/);
				if ($left_part =~ /\#/) {
					$form_silk_rootdir = "$silk_data_directory/$form_device_name";
				} else {
					$path_format =~ s/\s+//g;
					$path_format =~ s/\///g;
					$path_format =~ s/\"//g;
					($left_part,$dir1,$dir2,$dir3,$dir4,$dir5,$dir6,$dir7) = split(/\%/,$path_format);
					if ($dir1 ne "T") {
						$form_silk_rootdir = $silk_data_directory;
					} else {
						$form_silk_rootdir = "$silk_data_directory/$form_device_name";
					}
				}
			}
		}

		if ($form_device_name eq "Site") { $form_silk_rootdir = $silk_data_directory; }

		print "   <span class=rootdir_spacer></span>\n";
		print "    <label class=textin for=silk_rootdir>Data Rootdir:</label>\n";
		print "    <input class=right_dir type=text name=silk_rootdir value=\"$form_silk_rootdir\">\n";

	} else {

		print "   <span class=source_spacer></span>\n";
		print "   <span class=select>\n";
		print "    <select class=med name=exporter onchange=window.location.href=this[selectedIndex].value\;>\n";
	
	        if ($form_exporter ne "") {
			if ($called_by eq "FlowMonitor_Sol") {
				print "    <option value=$cgi_bin_short/FlowMonitor.cgi?$active_dashboard>Select Exporter</option>\n";
			} else {
				print "    <option value=$cgi_bin_short/$called_by.cgi?$active_dashboard>Select Exporter</option>\n";
			}
			print "    <option disabled> </option>\n";
	        } else {  
			if ($called_by eq "FlowMonitor_Sol") {
				print "    <option selected value=$cgi_bin_short/FlowMonitor.cgi?$active_dashboard>Select Exporter</option>\n";
			} else {
				print "    <option selected value=$cgi_bin_short/$called_by.cgi?$active_dashboard>Select Exporter</option>\n";
			}
			print "    <option disabled> </option>\n";
	        }
	
		if ($exporters[0] ne "") {
	        	foreach $exporter_pair (@exporters) {
				($exporter_ip,$exporter_name) = split(/:/,$exporter_pair);
				if ($exporter_ip eq $form_exporter) {
					if ($called_by eq "FlowMonitor_Sol") {
						$exporter_hash = $monitor_hash ."^EEE". $form_exporter;
	        				$option_value = "$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Solicit^$exporter_hash";
					} else {
						$exporter_hash = $filter_hash . "^EEE$exporter_ip";
	        				$option_value = "$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=$exporter_hash";
					}
	                        	print "    <option selected value=$option_value>$exporter_name</option>\n";
				} else { 
					if ($called_by eq "FlowMonitor_Sol") {
						$exporter_hash = $monitor_hash ."^EEE". $exporter_ip;
	        				$option_value = "$cgi_bin_short/FlowMonitor_Management.cgi?$active_dashboard^Solicit^$exporter_hash";
					} else {
						$exporter_hash = $filter_hash ."^EEE". $exporter_ip;
	        				$option_value = "$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=$exporter_hash";
					}
					print "    <option value=$option_value>$exporter_name</option>\n";
				}
			}
		}
	}

        print "    </select>\n";
	print "   </span>\n";
	print "  </fieldset>\n";
	print "\n";

	# Prepare the Period Start and End times (calculate if not saved.)

	if ($called_by =~ "FlowMonitor") { 
		if ($skip_date ne "Y") { 
			($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime(time-$start_offset);
			$mnth += 1;
			$yr   += 1900;
			$min_delta = $min % 5;
			$min = $min - $min_delta;
			if (length $mnth  < 2) { $mnth  = "0" . $mnth; }
			if (length $date  < 2) { $date  = "0" . $date; }
			if (length $hr    < 2) { $hr    = "0" . $hr; }
			if (length $min   < 2) { $min   = "0" . $min; }
			if (length $sec   < 2) { $sec   = "0" . $sec; }
			if ($date_format eq "DMY") {
				$start_date_out = $date ."/". $mnth ."/". $yr;
			} elsif ($date_format eq "DMY2") {
				$start_date_out = $date .".". $mnth .".". $yr;
			} elsif ($date_format eq "YMD") {
				$start_date_out = $yr ."-". $mnth ."-". $date;
			} else {
				$start_date_out = $mnth ."/". $date ."/". $yr;
			}
			if ($use_even_hours eq "Y") {
			        $start_time_out = $hr .":00:00";
			} else {
			        $start_time_out = $hr .":". $min .":00";
			}
		
			print "  <fieldset class=level2>\n";
			print "   <span class=input_text>\n";
			print "    <label for=start_date>Start Date</label>\n";
			print "    <input class=left_date type=text name=start_date value=\"$start_date_out\">\n";
			print "   </span>\n";
			print "   <span class=time_spacer></span>\n";
			print "   <span class=input_text>\n";
			print "    <label for=start_time>Start Time &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp (Adjust this only if Recreating a FlowMonitor)</label>\n";
			print "    <input class=left_date type=text name=start_time value=\"$start_time_out\">\n";
			print "   </span>\n";
			print "  </fieldset>\n";
			print "\n";
		} else {
			$skip_date = "";
		}

	} else {

		$start_date_out = $form_start_date;
		$start_time_out = $form_start_time;
		$end_date_out   = $form_end_date;
		$end_time_out   = $form_end_time;
	
		if ($start_date_out eq "") {
			
			($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime(time-$start_offset);
			$mnth += 1;
			$yr   += 1900;
			$min_delta = $min % 5;
			$min = $min - $min_delta;
			if (length $mnth  < 2) { $mnth  = "0" . $mnth; }
			if (length $date  < 2) { $date  = "0" . $date; }
			if (length $hr    < 2) { $hr    = "0" . $hr; }
			if (length $min   < 2) { $min   = "0" . $min; }
			if (length $sec   < 2) { $sec   = "0" . $sec; }
			if ($date_format eq "DMY") {
				$start_date_out = $date ."/". $mnth ."/". $yr;
			} elsif ($date_format eq "DMY2") {
				$start_date_out = $date .".". $mnth .".". $yr;
			} elsif ($date_format eq "YMD") {
				$start_date_out = $yr ."-". $mnth ."-". $date;
			} else {
				$start_date_out = $mnth ."/". $date ."/". $yr;
			}
			if ($use_even_hours eq "Y") {
			        $start_time_out = $hr .":00:00";
			} else {
			        $start_time_out = $hr .":". $min .":00";
			}
			
			($sec,$min,$hr,$date,$mnth,$yr,$day,$yr_date,$DST) = localtime(time-$end_offset);
			$mnth += 1;
			$yr   += 1900;
			$min_delta = $min % 5;
			$min = $min - $min_delta;
			if (length $mnth  < 2) { $mnth  = "0" . $mnth; }
			if (length $date  < 2) { $date  = "0" . $date; }
			if (length $hr    < 2) { $hr    = "0" . $hr; }
			if (length $min   < 2) { $min   = "0" . $min; }
			if (length $sec   < 2) { $sec   = "0" . $sec; }
			if ($date_format eq "DMY") {
				$end_date_out = $date ."/". $mnth ."/". $yr;
			} elsif ($date_format eq "DMY2") {
				$end_date_out = $date .".". $mnth .".". $yr;
			} elsif ($date_format eq "YMD") {
				$end_date_out = $yr ."-". $mnth ."-". $date;
			} else {
				$end_date_out = $mnth ."/". $date ."/". $yr;
			}
			if ($use_even_hours eq "Y") {
			        $end_time_out = $hr .":00:00";
			} else {
			        $end_time_out = $hr .":". $min .":00";
			}
		}
	
		print "  <fieldset class=level2>\n";
		print "   <span class=input_text>\n";
		print "    <label for=start_date>Start Date</label>\n";
		print "    <input class=left_date type=text name=start_date value=\"$start_date_out\">\n";
		print "   </span>\n";
		print "   <span class=time_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=start_time>Start Time</label>\n";
		print "    <input class=left_date type=text name=start_time value=\"$start_time_out\">\n";
		print "   </span>\n";
		print "   <span class=date_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=end_date>End Date</label>\n";
		print "    <input class=left_date type=text name=end_date value=\"$end_date_out\">\n";
		print "   </span>\n";
		print "   <span class=time_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=end_time>End Time</label>\n";
		print "    <input class=left_date type=text name=end_time value=\"$end_time_out\">\n";
		print "   </span>\n";
		print "  </fieldset>\n";
		print "\n";
	}

	# Prepare the Source related fields

	print "  <fieldset class=level2>\n";
	print "   <span class=input_text_long>\n";
	print "    <label for=source_address>Source IP Addresses</label>\n";
	print "    <input class=left_addr type=text name=source_address value=\"$form_source_addresses\">\n";
	print "   </span>\n";
	print "   <br><br>\n";
	print "   <span class=input_text>\n";
	print "    <label for=source_port>Source Port</label>\n";
	print "    <input class=left_port type=text name=source_port value=\"$form_source_ports\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=source_as>Source AS</label>\n";
	print "    <input class=left_port type=text name=source_as value=\"$form_source_ases\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=source_if>Source I/F</label>\n";
	print "    <input class=left_port type=text name=source_if value=\"$form_source_ifs\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "    <label for=sif_name>Source IF Name</label>\n";
	print "    <select class=long name=sif_name></b>\n";
	print "     <option selected value=\"\">Interface Names\n";

	if ($form_device_name ne "") {
	        $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Devices";
	} elsif ($form_exporter ne "") {
	        $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Exporters";
	}

	open (NAMED,"<$interfaces_file");
	chomp (@interfaces = <NAMED>);
	close (NAMED);

	print "      <optgroup label=\"Include ...\"></option>\n";
	foreach $interface (@interfaces) {
	        if (($interface eq "") || (substr($interface,0,1) eq "#")) { next; }
	        ($device,$interface_index,$interface_name) = split(/:/,$interface);
	        if (($device eq $form_device_name) || ($device eq $form_exporter)) {
	                if ($interface_index eq $form_sif_names) {
	                        print "      <option selected value=$interface_index>$interface_index $interface_name</option>\n";
	                } else {
	                        print "      <option value=$interface_index>$interface_index $interface_name</option>\n";
	                }
	        }
	}

	print "      <optgroup label=\"Exclude ...\"></option>\n";
	foreach $interface (@interfaces) {
	        if ($interface eq "") { next; }
	        ($device,$interface_index,$interface_name) = split(/:/,$interface);
	        $interface_index *= -1;
	        if (($device eq $form_device_name) || ($device eq $form_exporter)) {
	                if ($interface_index eq $form_sif_names) {
	                        print "      <option selected value=$interface_index>$interface_index $interface_name\n";
	                } else {
	                        print "      <option value=$interface_index>$interface_index $interface_name\n";
	                }
	        }
	}

	print "    </select>\n";
	print "   </span>\n";
	print "  </fieldset>\n";
	print "\n";

	# Prepare the Destination related fields

	print "  <fieldset class=level2>\n";
	print "   <span class=input_text_long>\n";
	print "    <label for=dest_address>Destination IP Addresses</label>\n";
	print "    <input class=left_addr type=text name=dest_address value=\"$form_dest_addresses\">\n";
	print "   </span>\n";
	print "   <br><br>\n";
	print "   <span class=input_text>\n";
	print "    <label for=dest_port>Dest Port</label>\n";
	print "    <input class=left_port type=text name=dest_port value=\"$form_dest_ports\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=dest_as>Dest AS</label>\n";
	print "    <input class=left_port type=text name=dest_as value=\"$form_dest_ases\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=dest_if>Dest I/F</label>\n";
	print "    <input class=left_port type=text name=dest_if value=\"$form_dest_ifs\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "    <label for=dif_name>Dest IF Name</label>\n";
	print "    <select class=long name=dif_name></b>\n";
	print "     <option selected value=\"\">Interface Names\n";

	print "      <optgroup label=\"Include ...\"></option>\n";
	foreach $interface (@interfaces) {
	        if (($interface eq "") || (substr($interface,0,1) eq "#")) { next; }
	        ($device,$interface_index,$interface_name) = split(/:/,$interface);
	        if (($device eq $form_device_name) || ($device eq $form_exporter)) {
	                if ($interface_index eq $form_dif_names) {
	                        print "      <option selected value=$interface_index>$interface_index $interface_name</option>\n";
	                } else {
	                        print "      <option value=$interface_index>$interface_index $interface_name</option>\n";
	                }
	        }
	}

	print "      <optgroup label=\"Exclude ...\"></option>\n";
	foreach $interface (@interfaces) {
	        if ($interface eq "") { next; }
	        ($device,$interface_index,$interface_name) = split(/:/,$interface);
	        $interface_index *= -1;
	        if (($device eq $form_device_name) || ($device eq $form_exporter)) {
	                if ($interface_index eq $form_dif_names) {
	                        print "      <option selected value=$interface_index>$interface_index $interface_name\n";
	                } else {
	                        print "      <option value=$interface_index>$interface_index $interface_name\n";
	                }
	        }
	}

	print "     </select>\n";
	print "   </span>\n";
	print "  </fieldset>\n";
	print "\n";

	# Prepare the Additional Fields 

	print "  <fieldset class=level2>\n";
	print "   <span class=input_text>\n";
	print "    <label for=tos_fields>TOS Field</label>\n";
	print "    <input class=left_port type=text name=tos_fields value=\"$form_tos_fields\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=tcp_flags>TCP Flags</label>\n";
	print "    <input class=left_port type=text name=tcp_flags value=\"$form_tcp_flags\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=protocols>Protocol</label>\n";
	print "    <input class=left_port type=text name=protocols value=\"$form_protocols\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "   <span class=input_text>\n";
	print "    <label for=nexthop_ip>NextHop IPs</label>\n";
	print "    <input class=left_next type=text name=nexthop_ip value=\"$form_nexthop_ip\">\n";
	print "   </span>\n";
	print "  </fieldset>\n";
}

sub create_reporting_form {

	$IPFIX = 0;
	foreach $ipfix_device (@ipfix_devices) {
		if ($form_device_name eq $ipfix_device) { $IPFIX = 1; }
	}

	print "  <fieldset class=level2>\n";
	print "   <legend class=level2>Reporting Parameters</legend>\n";
	print "    <span class=select>\n";
	print "    <label for=stat_report>Statistics Reports</label>\n";
	print "    <select class=long name=stat_report></b>\n";
	print "     <option value=0>Select Statistics Report";
	print "     <option disabled> </option>\n";

	if ($form_stat_report eq "") { $form_stat_report = $default_report; }
	if ($form_stat_report == 99) { print "     <option value=99 selected>Summary\n"; }
	else  { print "     <option value=99>Summary\n"; } 
	if ($form_stat_report == 30) { print "     <option value=30 selected>Detect Scanning\n"; }
	else  { print "     <option value=30>Detect Scanning\n"; } 
	if ($form_stat_report == 6)  { print "     <option value=6 selected>UDP/TCP Source Port\n"; }
	else  { print "     <option value=6>UDP/TCP Source Port\n"; } 
	if ($form_stat_report == 5)  { print "     <option value=5 selected>UDP/TCP Destination Port\n"; }
	else  { print "     <option value=5>UDP/TCP Destination Port\n"; } 
	if ($form_stat_report == 7)  { print "     <option value=7 selected>UDP/TCP Port\n"; }
	else  { print "     <option value=7>UDP/TCP Port\n"; } 
	if ($form_stat_report == 8)  { print "     <option value=8 selected>Destination IP\n"; }
	else  { print "     <option value=8>Destination IP\n"; } 
	if ($form_stat_report == 9)  { print "     <option value=9 selected>Source IP\n"; }
	else  { print "     <option value=9>Source IP\n"; } 
	if ($form_stat_report == 10) { print "     <option value=10 selected>Source/Destination IP\n"; }
	else  { print "     <option value=10>Source/Destination IP\n"; } 
	if ($form_stat_report == 11) { print "     <option value=11 selected>Source or Destination IP\n"; }
	else  { print "     <option value=11>Source or Destination IP\n"; } 
	if ($form_stat_report == 12) { print "     <option value=12 selected>IP Protocol\n"; }
	else  { print "     <option value=12>IP Protocol\n"; } 
	if ($form_stat_report == 17) { print "     <option value=17 selected>Input Interface\n"; }
	else  { print "     <option value=17>Input Interface\n"; } 
	if ($form_stat_report == 18) { print "     <option value=18 selected>Output Interface\n"; }
	else  { print "     <option value=18>Output Interface\n"; } 
	if ($form_stat_report == 23) { print "     <option value=23 selected>Input/Output Interface\n"; }
	else  { print "     <option value=23>Input/Output Interface\n"; } 
	if ($form_stat_report == 19) { print "     <option value=19 selected>Source AS\n"; }
	else  { print "     <option value=19>Source AS\n"; } 
	if ($form_stat_report == 20) { print "     <option value=20 selected>Destination AS\n"; }
	else  { print "     <option value=20>Destination AS\n"; } 
	if ($form_stat_report == 21) { print "     <option value=21 selected>Source/Destination AS\n"; }
	else  { print "     <option value=21>Source/Destination AS\n"; } 
	if ($form_stat_report == 22) { print "     <option value=22 selected>IP ToS\n"; }
	else  { print "     <option value=22>IP ToS\n"; } 
	if ($form_stat_report == 24) { print "     <option value=24 selected>Source Prefix\n"; }
	else  { print "     <option value=24>Source Prefix\n"; } 
	if ($form_stat_report == 25) { print "     <option value=25 selected>Destination Prefix\n"; }
	else  { print "     <option value=25>Destination Prefix\n"; } 
	if ($form_stat_report == 26) { print "     <option value=26 selected>Source/Destination Prefix\n"; }
	else  { print "     <option value=26>Source/Destination Prefix\n"; } 
	if ($form_stat_report == 27) { print "     <option value=27 selected>Exporter IP\n"; }
	else  { print "     <option value=27>Exporter IP\n"; } 

	print "    </select>\n";
	print "    </span>\n";
	print "   <span class=port_spacer></span>\n";
	print "    <span class=select>\n";
	print "    <label for=print_report>Printed Reports</label>\n";
	print "    <select class=long name=print_report></b>\n";

        if ($form_print_report ne "") {
		print "     <option value=0 >Select Print Report";
		print "     <option disabled> </option>\n";
	} else {
		print "     <option value=0 selected>Select Print Report";
		print "     <option disabled> </option>\n";
	}

	if ($form_print_report == 1)  { print "     <option value=1 selected>Flow Times\n"; } 
	else { print "     <option value=1>Flow Times\n"; } 
	if ($form_print_report == 4)  { print "     <option value=4 selected>AS Numbers\n"; } 
	else { print "     <option value=4>AS Numbers\n"; } 
	if ($form_print_report == 5)  { print "     <option value=5 selected>132 Columns\n"; } 
	else { print "     <option value=5>132 Columns\n"; } 
	if ($form_print_report == 9)  { print "     <option value=9 selected>1 Line with Tags\n"; } 
	else { print "     <option value=9>1 Line with Tags\n"; } 
	if ($form_print_report == 10) { print "     <option value=10 selected>AS Aggregation\n"; } 
	else { print "     <option value=10>AS Aggregation\n"; } 
	if ($form_print_report == 11) { print "     <option value=11 selected>Protocol Port Aggregation\n"; } 
	else { print "     <option value=11>Protocol Port Aggregation\n"; } 
	if ($form_print_report == 12) { print "     <option value=12 selected>Source Prefix Aggregation\n"; } 
	else { print "     <option value=12>Source Prefix Aggregation\n"; } 
	if ($form_print_report == 13) { print "     <option value=13 selected>Destination Prefix Aggregation\n"; } 
	else { print "     <option value=13>Destination Prefix Aggregation\n"; } 
	if ($form_print_report == 14) { print "     <option value=14 selected>Prefix Aggregation\n"; } 
	else { print "     <option value=14>Prefix Aggregation\n"; } 
	if ($form_print_report == 15) { print "     <option value=15 selected>Source Prefix Aggregation v6\n"; } 
	else { print "     <option value=15>Source Prefix Aggregation v6\n"; } 
	if ($form_print_report == 16) { print "     <option value=16 selected>Destination Prefix Aggregation v6\n"; } 
	else { print "     <option value=16>Destination Prefix Aggregation v6\n"; } 
	if ($form_print_report == 17) { print "     <option value=17 selected>Prefix Aggregation v6\n"; } 
	else { print "     <option value=17>Prefix Aggregation v6\n"; } 
	if ($form_print_report == 24) { print "     <option value=24 selected>Full Catalyst\n"; } 
	else { print "     <option value=24>Full Catalyst\n"; } 

	print "    </select>\n";
	print "    </span>\n";
	print "   <span class=flow_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=flow_analysis>Flow Analysis</label>\n";
	print "   <select class=shortie name=flow_analysis></b>\n";

	if ($form_flow_analysis eq "") { $form_flow_analysis = $default_flows; }
	if (($form_flow_analysis eq "") || ($form_flow_analysis == 0)) { print "    <option value=0 selected>Off\n"; }
	else { print "    <option value=0>Off\n"; }
	if ($form_flow_analysis == 1) { print "    <option value=1 selected>On\n"; }
	else { print "    <option value=1>On\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <br><br><br>\n";

	print "   <span class=select>\n";
	print "   <label for=flow_select>Include Flow If:</label>\n";
	print "   <select class=long name=flow_select></b>\n";

	if (($form_flow_select eq "") || ($form_flow_select == 1)) { print "    <option value=1 selected>Any Part in Specified Time Span\n"; }
	else { print "    <option value=1>Any Part in Specified Time Span\n"; }
	if ($form_flow_select == 2) { print "    <option value=1 selected>End Time in Specified Time Span\n"; }
	else { print "    <option value=2>End Time in Specified Time Span\n"; }
	if ($form_flow_select == 3) { print "    <option value=1 selected>Start Time in Specified Time Span\n"; }
	else { print "    <option value=3>Start Time in Specified Time Span\n"; }
	if ($form_flow_select == 4) { print "    <option value=1 selected>Entirely in Specified Time Span\n"; }
	else { print "    <option value=4>Entirely in Specified Time Span\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=cutoff_lines>Cutoff Lines</label>\n";
	if ($form_cutoff_lines eq "") { $form_cutoff_lines = $default_lines; }
	print "    <input class=left_port type=text name=cutoff_lines value=\"$form_cutoff_lines\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=cutoff_octets>Cutoff Octets</label>\n";
	print "    <input class=left_port type=text name=cutoff_octets value=\"$form_cutoff_octets\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=sampling_multiplier>Sampling Multi</label>\n";
	print "    <input class=left_port type=text name=sampling_multiplier value=\"$form_sampling_multiplier\">\n";
	print "   </span>\n";
	print "   <br><br><br>\n";

	print "   <span class=select>\n";
	print "   <label for=pie_charts>Pie Charts</label>\n";
	print "   <select class=short name=pie_charts></b>\n";

	if ($form_pie_charts eq "") { $form_pie_charts = $pie_chart_default; }
	if (($form_pie_charts eq "") || ($form_pie_charts == 0)) { print "    <option value=0 selected>None\n"; }
	else { print "    <option value=0>None\n"; }
	if ($form_pie_charts == 1) { print "    <option value=1 selected>With Others\n"; }
	else { print "    <option value=1>With Others\n"; }
	if ($form_pie_charts == 2) { print "    <option value=2 selected>Without Others\n"; }
	else { print "    <option value=2>Without Others\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=resolve_addresses>Resolve Addresses</label>\n";
	print "   <select class=short name=resolve_addresses></b>\n";

	if ($default_identifier eq "DNS") {
		if (($form_resolve_addresses eq "") || ($form_resolve_addresses eq "Y")) { print "    <option value=Y selected>DNS Names\n"; }
		else { print "    <option value=Y>DNS Names\n"; }
		if ($form_resolve_addresses eq "N") { print "    <option value=N selected>IP Addresses\n"; }
		else { print "    <option value=N>IP Addresses\n"; }
	} else {
		if (($form_resolve_addresses eq "") || ($form_resolve_addresses eq "N")) { print "    <option value=N selected>IP Addresses\n"; }
		else { print "    <option value=N>IP Addresses\n"; }
		if ($form_resolve_addresses eq "Y") { print "    <option value=Y selected>DNS Names\n"; }
		else { print "    <option value=Y>DNS Names\n"; }
	}

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=unit_conversion>Octet Units</label>\n";
	print "   <select class=short name=unit_conversion></b>\n";

	if (($form_unit_conversion eq "") || ($form_unit_conversion eq "Y")) { print "    <option value=Y selected>Use Units\n"; }
	else { print "    <option value=Y>Use Units\n"; }
	if ($form_unit_conversion eq "N") { print "    <option value=N selected>Numeric Only\n"; }
	else { print "    <option value=N>Numeric Only\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=sort_field>Sort Field</label>\n";
	print "   <select class=short name=sort_field></b>\n";

	if (($form_sort_field eq "") || ($form_sort_field == 1)) { print "    <option value=1 selected>Octets\n"; }
	else { print "    <option value=1>Octets\n"; }
	if (($form_sort_field == 2) || ($form_monitor_type =~ /fps/)) { print "    <option value=2 selected>Flows\n"; }
	else { print "    <option value=2>Flows\n"; }
	if (($form_sort_field == 3) || ($form_monitor_type =~ /pps/)) { print "    <option value=3 selected>Packets\n"; }
	else { print "    <option value=3>Packets\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print " </fieldset>\n";
}

sub create_graphing_form {

	$IPFIX = 0;
	foreach $ipfix_device (@ipfix_devices) {
		if ($form_device_name eq $ipfix_device) { $IPFIX = 1; }
	}

	print "  <fieldset class=level2>\n";
	print "   <legend class=level2>Graphing Parameters</legend>\n";

	print "   <span class=select>\n";
	print "   <label for=flow_select>Include Flow If:</label>\n";
	print "   <select class=long name=flow_select></b>\n";

	if (($form_flow_select eq "") || ($form_flow_select == 1)) { print "    <option value=1 selected>Any Part in Specified Time Span\n"; }
	else { print "    <option value=1>Any Part in Specified Time Span\n"; }
	if ($form_flow_select == 2) { print "    <option value=1 selected>End Time in Specified Time Span\n"; }
	else { print "    <option value=2>End Time in Specified Time Span\n"; }
	if ($form_flow_select == 3) { print "    <option value=1 selected>Start Time in Specified Time Span\n"; }
	else { print "    <option value=3>Start Time in Specified Time Span\n"; }
	if ($form_flow_select == 4) { print "    <option value=1 selected>Any Part in Specified Time Span\n"; }
	else { print "    <option value=4>Entirely in Specified Time Span\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=graph_type>Graph Type</label>\n";
	print "   <select class=med name=graph_type></b>\n";

	if ($form_graph_type eq "") { $form_graph_type = $default_graph; }
	if (($form_graph_type eq "bps")  || ($form_monitor_type =~ "bps"))  { print "    <option value=bps selected>Bits/Second\n"; }
	else { print "    <option value=bps>Bits/Second\n"; }
	if (($form_graph_type eq "pps")  || ($form_monitor_type =~ "pps"))  { print "    <option value=pps selected>Packets/Second\n"; }
	else { print "    <option value=pps>Packets/Second\n"; }
	if (($form_graph_type eq "fpsi") || ($form_monitor_type eq "fpsi") || ($form_monitor_type eq "Individual-fps")) { print "    <option value=fpsi selected>Flows Initiated/Second\n"; }
	else { print "    <option value=fpsi>Flows Initiated/Second\n"; }
	if (($form_graph_type eq "fpsa") || ($form_monitor_type eq "fpsa") || ($form_monitor_type =~ "fps-prorated")) { print "    <option value=fpsa selected>Flows Active/Second\n"; }
	else { print "    <option value=fpsa>Flows Active/Second\n"; }
	if  ($form_graph_type eq "bpsa") { print "    <option value=bpsa selected>Bits/Second - Analysis\n"; }
	else { print "    <option value=bpsa>Bits/Second - Analysis\n"; }
	if  ($form_graph_type eq "ppsa") { print "    <option value=ppsa selected>Packets/Second - Analysis\n"; }
	else { print "    <option value=ppsa>Packets/Second - Analysis\n"; }
	if ($form_graph_type eq "fpsia") { print "    <option value=fpsia selected>Flows Initiated/Second - Analysis\n"; }
	else { print "    <option value=fpsia>Flows Initiated/Second - Analysis\n"; }
	if ($form_graph_type eq "fpsaa") { print "    <option value=fpsaa selected>Flows Active/Second - Analysis\n"; }
	else { print "    <option value=fpsaa>Flows Active/Second - Analysis\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=stats_method>Statistics From</label>\n";
	print "   <select class=med name=stats_method></b>\n";

	if (($form_stats_method eq "") || ($form_stats_method eq "Nonzeroes")) { print "    <option value=Nonzeroes selected>Nonzero Values\n"; }
	else { print "    <option value=Nonzeroes>Nonzero Values\n"; }
	if ($form_stats_method eq "All") { print "    <option value=All selected>All Values\n"; }
	else { print "    <option value=All>All Values\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <br><br>\n";

	print "   <span class=select>\n";
	print "   <label for=resolve_addresses>Resolve Addresses</label>\n";
	print "   <select class=short name=resolve_addresses></b>\n";

	if ($default_identifier eq "DNS") {
		if (($form_resolve_addresses eq "") || ($form_resolve_addresses eq "Y")) { print "    <option value=Y selected>DNS Names\n"; }
		else { print "    <option value=Y>DNS Names\n"; }
		if ($form_resolve_addresses eq "N") { print "    <option value=N selected>IP Addresses\n"; }
		else { print "    <option value=N>IP Addresses\n"; }
	} else {
		if (($form_resolve_addresses eq "") || ($form_resolve_addresses eq "N")) { print "    <option value=N selected>IP Addresses\n"; }
		else { print "    <option value=N>IP Addresses\n"; }
		if ($form_resolve_addresses eq "Y") { print "    <option value=Y selected>DNS Names\n"; }
		else { print "    <option value=Y>DNS Names\n"; }
	}

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=graph_multiplier>Graph Width</label>\n";
	print "   <select class=shorter name=graph_multiplier></b>\n";

	if (($form_graph_multiplier eq "") || ($form_graph_multiplier eq "1")) { print "    <option value=1 selected>1\n"; }
	else { print "    <option value=1>1\n"; }
	if ($form_graph_multiplier eq "2") { print "    <option value=2 selected>2\n"; }
	else { print "    <option value=2>2\n"; }
	if ($form_graph_multiplier eq "3") { print "    <option value=3 selected>3\n"; }
	else { print "    <option value=3>3\n"; }
	if ($form_graph_multiplier eq "4") { print "    <option value=4 selected>4\n"; }
	else { print "    <option value=4>4\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=bucket_size>Bucket Size</label>\n";
	print "   <select class=shorter name=bucket_size></b>\n";

	if ($form_bucket_size eq "1") { print "    <option value=1 selected>1\n"; }
	else { print "    <option value=1>1\n"; }
	if ($form_bucket_size eq "2") { print "    <option value=2 selected>2\n"; }
	else { print "    <option value=2>2\n"; }
	if ($form_bucket_size eq "3") { print "    <option value=3 selected>3\n"; }
	else { print "    <option value=3>3\n"; }
	if ($form_bucket_size eq "4") { print "    <option value=4 selected>4\n"; }
	else { print "    <option value=4>4\n"; }
	if (($form_bucket_size eq "5") || ($form_bucket_size eq "")) { print "    <option value=5 selected>5\n"; }
	else { print "    <option value=5>5\n"; }
	if ($form_bucket_size eq "10") { print "    <option value=10 selected>10\n"; }
	else { print "    <option value=10>10\n"; }
	if ($form_bucket_size eq "15") { print "    <option value=15 selected>15\n"; }
	else { print "    <option value=15>15\n"; }
	if ($form_bucket_size eq "30") { print "    <option value=30 selected>30\n"; }
	else { print "    <option value=30>30\n"; }
	if ($form_bucket_size eq "60") { print "    <option value=60 selected>60\n"; }
	else { print "    <option value=60>60\n"; }
	if ($form_bucket_size eq "300") { print "    <option value=300 selected>300\n"; }
	else { print "    <option value=300>300\n"; }
	if ($form_bucket_size eq "300E") { print "    <option value=300E selected>300E\n"; }
	else { print "    <option value=300E>300E\n"; }

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=sampling_multiplier>Sampling Multi</label>\n";
	print "    <input class=left_graph type=text name=sampling_multiplier value=\"$form_sampling_multiplier\" id=sampling_multiplier>\n";
	print "   </span>\n";

	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=detail_lines>Detail Lines</label>\n";
	if ($form_detail_lines eq "") { $form_detail_lines = $detail_lines; }
	print "    <input class=left_graph type=text align=right name=detail_lines value=\"$form_detail_lines\" id=detail_lines>\n";
	print "   </span>\n";

	print "   </select>\n";
	print "   </span>\n";
	print " </fieldset>\n";
}

sub create_monitor_form {

	$IPFIX = 0;
	foreach $ipfix_device (@ipfix_devices) {
		if ($form_device_name eq $ipfix_device) { $IPFIX = 1; }
	}

	print "  <fieldset class=level2>\n";
	print "   <legend class=level2>Monitor Parameters</legend>\n";

	print "   <span class=input_text>\n";
	print "   <label for=monitor_label>Monitor Label</label>\n";
	print "    <input class=left_monitor type=text name=monitor_label value=\"$form_monitor_label\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=monitor_type>Monitor Type</label>\n";
	print "   <select class=med name=monitor_type></b>\n";
	if (($form_monitor_type eq "") || ($form_monitor_type eq "Individual") || ($form_monitor_type eq "bps")) { print "    <option value=bps selected>Bits/Second</option>\n"; }
	else { print "    <option value=bps>Bits/Second</option>\n"; }
	if (($form_graph_type =~ /pps/) || ($form_monitor_type eq "pps")) { print "    <option value=pps selected>Packets/Second</option>\n"; }
	else { print "    <option value=pps>Packets/Second</option>\n"; }
	if (($form_graph_type =~ /fpsi/) || ($form_monitor_type eq "fpsi")) { print "    <option value=fpsi selected>Flows Initiated/Second</option>\n"; }
	else { print "    <option value=fpsi>Flows Initiated/Second</option>\n"; }
	if (($form_graph_type =~ /fpsa/) || ($form_monitor_type eq "fpsa")) { print "    <option value=fpsa selected>Flows Active/Second</option>\n"; }
	else { print "    <option value=fpsa>Flows Active/Second</option>\n"; }
	if ($form_monitor_type eq "Group") { print "    <option value=Group selected>Group</option>\n"; }
	else { print "    <option value=Group>Group</option>\n"; }
	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=sampling_multiplier>Sampling Multi</label>\n";
	print "    <input class=left_port type=text name=sampling_multiplier value=\"$form_sampling_multiplier\">\n";
	print "   </span>\n";
	print "   <br><br>\n";

	print "   <span class=input_text>\n";
	print "   <label for=alert_destination>Alert Destination (email address)</label>\n";
	print "    <input class=left_monitor type=text name=alert_destination value=\"$form_alert_destination\">\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=select>\n";
	print "   <label for=alert_frequency>Alert Frequency</label>\n";
	print "   <select class=med name=alert_frequency></b>\n";
	if (($form_alert_frequency eq "") || ($form_alert_frequency eq "none")) { print "    <option value=none selected>No Notification</option>\n"; }
	else { print "    <option value=none>No Notification</option>\n"; }
	if ($form_alert_frequency eq "daily") { print "    <option value=daily selected>Single miss - Once a Day</option>\n"; }
	else { print "    <option value=daily>Single miss - Once a Day</option>\n"; }
	if ($form_alert_frequency eq "daily3") { print "    <option value=daily3 selected>3 Consecutive - Once a Day</option>\n"; }
	else { print "    <option value=daily3>3 Consecutive - Once a Day</option>\n"; }
	if ($form_alert_frequency eq "daily6") { print "    <option value=daily6 selected>6 Consecutive - Once a Day</option>\n"; }
	else { print "    <option value=daily6>6 Consecutive - Once a Day</option>\n"; }
	if ($form_alert_frequency eq "daily12") { print "    <option value=daily12 selected>12 Consecutive - Once a Day</option>\n"; }
	else { print "    <option value=daily12>12 Consecutive - Once a Day</option>\n"; }
	if ($form_alert_frequency eq "eachtime") { print "    <option value=eachtime selected>Single miss - Each Occurence</option>\n"; }
	else { print "    <option value=eachtime>Single miss - Each Occurrence</option>\n"; }
	if ($form_alert_frequency eq "eachtime3") { print "    <option value=eachtime3 selected>3 Consecutive - Each Occurence</option>\n"; }
	else { print "    <option value=eachtime3>3 Consecutive - Each Occurrence</option>\n"; }
	if ($form_alert_frequency eq "eachtime6") { print "    <option value=eachtime6 selected>6 Consecutive - Each Occurence</option>\n"; }
	else { print "    <option value=eachtime6>6 Consecutive - Each Occurrence</option>\n"; }
	if ($form_alert_frequency eq "eachtime12") { print "    <option value=eachtime12 selected>12 Consecutive - Each Occurence</option>\n"; }
	else { print "    <option value=eachtime12>12 Consecutive - Each Occurrence</option>\n"; }
	if ($form_alert_frequency eq "sigma1") { print "    <option value=sigma1 selected>Sigma Type 1 Check</option>\n"; }
	else { print "    <option value=sigma1>Sigma Type 1 Check</option>\n"; }
	if ($form_alert_frequency eq "sigma2") { print "    <option value=sigma2 selected>Sigma Type 2 Check</option>\n"; }
	else { print "    <option value=sigma2>Sigma Type 2 Check</option>\n"; }
	if ($form_alert_frequency eq "sigma3") { print "    <option value=sigma3 selected>Sigma Type 3 Check</option>\n"; }
	else { print "    <option value=sigma3>Sigma Type 3 Check</option>\n"; }
	print "   </select>\n";
	print "   </span>\n";
	print "   <span class=port_spacer></span>\n";

	print "   <span class=input_text>\n";
	print "   <label for=alert_threshold>Alert Threshold</label>\n";
	print "    <input class=left_port type=text name=alert_threshold value=\"$form_alert_threshold\">\n";
	print "   </span>\n";
	print "   <br><br>\n";

	print "   <span class=input_text>\n";
	print "   <label for=general_comment>General Comment</label>\n";
	print "    <input class=left_addr type=text name=general_comment value=\"$form_general_comment\">\n";
	print "   </span>\n";

	print " </fieldset>\n";
}

sub create_revision_form {

	print "  <fieldset class=level2>\n";
	print "   <legend class=level2>Revision Notes</legend>\n";

	print "   <span class=input_text>\n";
	print "   <label for=revision_comment>Revision Comment</label>\n";
	print "    <input class=left_rev type=text name=revision_comment value=\"$form_revision_comment\" id=revision_comment>\n";
	print "   </span>\n";

	print "   <span class=select>\n";
	print "   <label for=monitor_type>Notate Graphs</label>\n";
	print "   <select class=short name=notate_graphs></b>\n";
	print "    <option value=N selected>No</option>\n";
	print "    <option value=Y>Yes</option>\n";
	print "   </select>\n";
	print "   </span>\n";

	print " </fieldset>\n";
}

sub create_SiLK_form {

	# If using IPFIX, prepare the SiLK Selection

	$IPFIX = 0;
	foreach $ipfix_device (@ipfix_devices) {
		if ($form_device_name eq $ipfix_device) { $IPFIX = 1; }
	}

	if ($IPFIX) {

		# For legacy use of "silk_field", convert to silk_type

		if (substr($form_silk_field,1,1) eq "1") { $form_silk_type = "in,"; }
		if (substr($form_silk_field,2,1) eq "1") { $form_silk_type .= "out,"; }
		if (substr($form_silk_field,3,1) eq "1") { $form_silk_type .= "inweb,"; }
		if (substr($form_silk_field,4,1) eq "1") { $form_silk_type .= "outweb,"; }
		if (substr($form_silk_field,5,1) eq "1") { $form_silk_type .= "int2int,"; }
		if (substr($form_silk_field,6,1) eq "1") { $form_silk_type .= "ext2ext,"; }
		if (substr($form_silk_type,-1,1) eq ",") { $form_silk_type = substr($form_silk_type,0,-1); }

		if ($form_silk_other ne "") { $form_silk_type = $form_silk_other; }

		if ($form_silk_class eq "")    { $form_silk_class    = $silk_class_default; }
		if ($form_silk_flowtype eq "") { $form_silk_flowtype = $silk_flowtype_default; }
		if ($form_silk_type eq "")     { $form_silk_type     = $silk_type_default; }
		if ($form_silk_sensors eq "")  { $form_silk_sensors  = $silk_sensors_default; }
		if ($form_silk_switches eq "") { $form_silk_switches = $silk_switches_default; }

		print "  <fieldset class=level2>\n";
		print "   <legend class=level2>SiLK Selection</legend>\n";

		print "   <span class=input_text>\n";
		print "    <label for=silk_class>Class</label>\n";
		print "    <input class=silk_source type=text name=silk_class value=\"$form_silk_class\">\n";
		print "   </span>\n";
		print "   <span class=silk_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=silk_flowtype>Flowtype</label>\n";
		print "    <input class=silk_source type=text name=silk_flowtype value=\"$form_silk_flowtype\">\n";
		print "   </span>\n";
		print "   <span class=silk_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=silk_type>Type</label>\n";
		print "    <input class=silk_source type=text name=silk_type value=\"$form_silk_type\">\n";
		print "   </span>\n";
		print "   <span class=silk_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=silk_sensors>Sensors</label>\n";
		print "    <input class=silk_source type=text name=silk_sensors value=\"$form_silk_sensors\">\n";
		print "   </span>\n";
		print "   <span class=silk_spacer></span>\n";
		print "   <span class=input_text>\n";
		print "    <label for=silk_switches>Other Switches</label>\n";
		print "    <input class=silk_source type=text name=silk_switches value=\"$form_silk_switches\">\n";
		print "   </span>\n";
		print "  </fieldset>\n";

	}
}

sub create_submit_buttons {

	my ($called_by) = @_;

	if ($called_by ne "FlowMonitor_Sol") { print "   <br>\n"; }
	print "  <table>\n";
	print "  <tr>\n";
	print "  <td class=td_left>\n";
	if ($called_by eq "FlowViewer")      { print "   <input class=button type=submit value=\"Generate Textual Report\">\n"; } 
	if ($called_by eq "FlowGrapher")     { print "   <input class=button type=submit value=\"Generate Graph Report\">\n"; } 
	if ($called_by eq "FlowMonitor")     { print "   <input class=button type=submit value=\"Create Monitor\">\n"; } 
	if ($called_by eq "FlowMonitor_Sol") { print "   <input class=button type=submit value=\"Revise Monitor\">\n"; $called_by = "FlowMonitor"; } 
	print "  </td>\n";
	print "  <td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "  <td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "  <td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print "  <td>&nbsp&nbsp&nbsp&nbsp&nbsp</td>\n";
	print " <input type=hidden name=active_dashboard value=\"$active_dashboard\">\n";
	print "  <td class=td_right>\n";
	print "  <a href=\"$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=\">\n";
	print "  <button class=reset type=button onClick=window.location.href=\"$cgi_bin_short/$called_by.cgi?$active_dashboard^filter_hash=\">Reset Form Values</button>\n";
	print "  </a>\n";
	print "  </td>\n";
	print "  </tr>\n";
	print "  </table>\n";
	if ($called_by ne "FlowMonitor_Sol") { print "  <br>\n"; }
	print " </fieldset>\n";
	print " </form>\n";
}

sub create_filter_output {

	my ($called_by,$filter_hash) = @_;

	load_filtering_parameters($called_by,$filter_hash);

	if ($called_by =~ "FlowMonitor_Replay") {
		print "  <br>\n";
		print "  <span class=text16>$form_Description</span>\n";
		print "  <br>\n";
	}

	if ($called_by =~ "FlowMonitor") {
		print "  <br>\n";
		print "  <span class=text16>$form_monitor_label</span>\n";
		print "  <br>\n";
	}

	if ($form_monitor_type eq "Group") {
		if ($form_general_comment ne "") {
			print "  <br>\n";
			print "  <span class=text10>$form_general_comment</span>\n";
		}
		return;
	}

	open(DATE,"date 2>&1|");
	while (<DATE>) {
		($d_tz,$m_tz,$dt_tz,$t_tz,$time_zone,$y_tz) = split(/\s+/,$_);
	}

	print "  <table class=filter>\n";

	if (($called_by =~ "FlowViewer") || ($called_by =~ "FlowGrapher")) {
		print "  <tr>\n";
		if ($called_by =~ "FlowViewer") {

			if ($stat_report == 99)  { $report_title = "Summary"; }
			if ($stat_report == 5)   { $report_title = "UDP/TCP Destination Port"; }
			if ($stat_report == 6)   { $report_title = "UDP/TCP Source Port"; }
			if ($stat_report == 7)   { $report_title = "UDP/TCP Port"; }
			if ($stat_report == 8)   { $report_title = "Destination IP"; }
			if ($stat_report == 9)   { $report_title = "Source IP"; }
			if ($stat_report == 10)  { $report_title = "Source/Destination IP"; }
			if ($stat_report == 11)  { $report_title = "Source or Destination IP"; }
			if ($stat_report == 12)  { $report_title = "IP Protocol"; }
			if ($stat_report == 17)  { $report_title = "Input Interface"; }
			if ($stat_report == 18)  { $report_title = "Output Interface"; }
			if ($stat_report == 19)  { $report_title = "Source AS"; }
			if ($stat_report == 20)  { $report_title = "Destination AS"; }
			if ($stat_report == 21)  { $report_title = "Source/Destination AS"; }
			if ($stat_report == 22)  { $report_title = "IP ToS"; }
			if ($stat_report == 23)  { $report_title = "Input/Output Interface"; }
			if ($stat_report == 24)  { $report_title = "Source Prefix"; }
			if ($stat_report == 25)  { $report_title = "Destination Prefix"; }
			if ($stat_report == 26)  { $report_title = "Source/Destination Prefix"; }
			if ($stat_report == 27)  { $report_title = "Exporter IP"; }
			if ($stat_report == 30)  { $report_title = "Detect Scanning"; }
	
			if ($print_report == 1)  { $report_title = "Flow Times"; }
			if ($print_report == 4)  { $report_title = "AS Numbers"; }
			if ($print_report == 5)  { $report_title = "132 Columns"; }
			if ($print_report == 9)  { $report_title = "1 Line with Tags"; }
			if ($print_report == 10) { $report_title = "AS Aggregation"; }
			if ($print_report == 11) { $report_title = "Protocol Port Aggregation"; }
			if ($print_report == 12) { $report_title = "Source Prefix Aggregation"; }
			if ($print_report == 13) { $report_title = "Destination Prefix Aggregation"; }
			if ($print_report == 14) { $report_title = "Prefix Aggregation"; }
			if ($print_report == 15) { $report_title = "Source Prefix Aggregation v6"; }
			if ($print_report == 16) { $report_title = "Destination Prefix Aggregation v6"; }
			if ($print_report == 17) { $report_title = "Prefix Aggregation v6"; }
			if ($print_report == 24) { $report_title = "Full (Catalyst)"; }

			print "  <td class=label>Report:&nbsp&nbsp</td>\n";
			print "  <td class=value>$report_title</td>\n";
			print "  <td class=label>Sort Field:&nbsp&nbsp</td>\n";

			if ($form_sort_field == 1) { print "  <td class=value>Octets</td>\n"; }
			if ($form_sort_field == 2) { print "  <td class=value>Flows</td>\n"; }
			if ($form_sort_field == 3) { print "  <td class=value>Packets</td>\n"; }

		} elsif ($called_by =~ "FlowGrapher") {

			print "  <td class=label>Report:&nbsp&nbsp</td>\n";
			if    ($form_graph_type eq "bps")   { $graph_type_out = "Bits/Second"; }
			elsif ($form_graph_type eq "bpsa")  { $graph_type_out = "Bits/Second Analysis"; }
			elsif ($form_graph_type eq "pps")   { $graph_type_out = "Packets/Second"; }
			elsif ($form_graph_type eq "ppsa")  { $graph_type_out = "Packets/Second Analysis"; }
			elsif ($form_graph_type eq "fpsi")  { $graph_type_out = "Flows Initiated/Second"; }
			elsif ($form_graph_type eq "fpsa")  { $graph_type_out = "Flows Active/Second"; }
			elsif ($form_graph_type eq "fpsia") { $graph_type_out = "Flows Initiated/Second Analysis"; }
			elsif ($form_graph_type eq "fpsaa") { $graph_type_out = "Flows Active/Second Analysis"; }
			print "  <td class=value>$graph_type_out</td>\n";
			print "  <td class=label>Bucket Size:&nbsp&nbsp</td>\n";
			print "  <td class=value>$form_bucket_size sec</td>\n";

		}
		print "  </tr>\n";
		print "  <tr>\n";
		print "  <td class=label>Start Time:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_start_date $form_start_time $time_zone</td>\n";
		print "  <td class=label>End Time:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_end_date $form_end_time $time_zone</td>\n";
		print "  </tr>\n";
	}

	if ($form_exporter ne "") { 
        	foreach $exporter_pair (@exporters) {
			($exporter_ip,$exporter_name) = split(/:/,$exporter_pair);
			if ($form_exporter eq $exporter_ip) { last; }
		}
	}

	print "  <tr>\n";
	print "  <td class=label>Device Name:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_device_name</td>\n";
	print "  <td class=label>Exporter:&nbsp&nbsp</td>\n";
	print "  <td class=value>$exporter_name</td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "  <td class=label>Source IPs:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_source_addresses</td>\n";
	print "  <td class=label>Destination IPs:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_dest_addresses</td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "  <td class=label>Source Ports:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_source_ports</td>\n";
	print "  <td class=label>Destination Ports:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_dest_ports</td>\n";
	print "  </tr>\n";

	print "  <tr>\n";
	print "  <td class=label>Source I/Fs:&nbsp&nbsp</td>\n";

	if ($form_sif_names ne "") {
		if ($form_device_name ne "") {
		        $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Devices";
		} elsif ($form_exporter ne "") {
		        $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Exporters";
		}
	
		open (NAMED,"<$interfaces_file");
		chomp (@interfaces = <NAMED>);
		close (NAMED);
	
		foreach $interface (@interfaces) {
		        if (($interface eq "") || (substr($interface,0,1) eq "#")) { next; }
		        ($device,$interface_index,$interface_name) = split(/:/,$interface);
		        if (($device eq $form_device_name) || ($device eq $form_exporter)) {
		                if ($interface_index eq $form_sif_names) {
					$sif_name_out = $interface_name;
				}
			}
		}
		print "  <td class=value>$sif_name_out</td>\n";
	} else {
		print "  <td class=value>$form_source_ifs</td>\n";
	}

	print "  <td class=label>Destination I/Fs:&nbsp&nbsp</td>\n";
	if ($form_dif_names ne "") {

		if ($form_device_name ne "") {
		        $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Devices";
		} elsif ($form_exporter ne "") {
		        $interfaces_file = "$cgi_bin_directory/NamedInterfaces_Exporters";
		}
	
		open (NAMED,"<$interfaces_file");
		chomp (@interfaces = <NAMED>);
		close (NAMED);
	
		foreach $interface (@interfaces) {
		        if (($interface eq "") || (substr($interface,0,1) eq "#")) { next; }
		        ($device,$interface_index,$interface_name) = split(/:/,$interface);
		        if (($device eq $form_device_name) || ($device eq $form_exporter)) {
		                if ($interface_index eq $form_dif_names) {
					$dif_name_out = $interface_name;
				}
			}
		}
		print "  <td class=value>$dif_name_out</td>\n";
	} else {
		print "  <td class=value>$form_dest_ifs</td>\n";
	}
	print "  </tr>\n";

	print "  <tr>\n";
	print "  <td class=label>Source AS:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_source_ases</td>\n";
	print "  <td class=label>Destination AS:&nbsp&nbsp</td>\n";
	print "  <td class=value>$form_dest_ases</td>\n";
	print "  </tr>\n";

	if (($form_nexthop_ips ne "") || ($form_protocols ne "")) {
		print "  <tr>\n";
		print "  <td class=label>NextHop IPs:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_nexthop_ips</td>\n";
		print "  <td class=label>Protocols:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_protocols</td>\n";
		print "  </tr>\n";
	}

	if (($form_tos_fields ne "") || ($form_tcp_flags ne "")) {
		print "  <tr>\n";
		print "  <td class=label>TOS Field:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_tos_fields</td>\n";
		print "  <td class=label>TCP Flags:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_tcp_flags</td>\n";
		print "  </tr>\n";
	}

	if ($called_by =~ "FlowGrapher") {

		print "  <tr>\n";
		print "  <td class=label>Detail Lines:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_detail_lines</td>\n";
		print "  <td class=label>Graph Width:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_graph_multiplier</td>\n";
		print "  </tr>\n";
	}

	if ($called_by =~ "FlowViewer") {

		print "  <tr>\n";
		print "  <td class=label>Cutoff Lines:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_cutoff_lines</td>\n";
		print "  <td class=label>Cutoff Octets:&nbsp&nbsp</td>\n";
		print "  <td class=value>$form_cutoff_octets</td>\n";
		print "  </tr>\n";
	}

	if (($called_by =~ "FlowViewer") || ($called_by =~ "FlowGrapher")) {

		if ($form_flow_select == 1) { $flow_select_out = "Any Part in Specified Time Span"; }
		if ($form_flow_select == 2) { $flow_select_out = "End Time in Specified Time Span"; }
		if ($form_flow_select == 3) { $flow_select_out = "Start Time in Specified Time Span"; }
		if ($form_flow_select == 4) { $flow_select_out = "Entirely in Specified Time Span"; }

		print "  <tr>\n";
		print "  <td class=label>Include If:&nbsp&nbsp</td>\n";
		print "  <td class=value>$flow_select_out</td>\n";
	}

	if ($form_IPFIX) {

		if ($form_silk_rootdir ne "")   { $selection_out  = "--data-rootdir=$form_silk_rootdir "; }
		if ($form_silk_class ne "")     { $selection_out .= "--class=$form_silk_class "; }
		if ($form_silk_flowtype ne "")  { $selection_out .= "--flowtype=$form_silk_flowtype "; }
		if ($form_silk_type ne "")      { $selection_out .= "--type=$form_silk_type "; }
		if ($form_silk_sensors ne "")   { $selection_out .= "--sensors=$form_silk_sensors "; }
		if ($form_silk_switches ne "")  { $selection_out .= "$form_silk_switches "; }

		print "  <td class=label>SiLK Selection:&nbsp&nbsp</td>\n";
		if ($called_by =~ "FlowMonitor") { 
			print "  <td class=value>$selection_out</td>\n";
		} else {
			print "  <td class=value>$selection_out</td>\n";
			print "  </tr>\n";
		}
	}

	if ($called_by =~ "FlowMonitor") {

		$monitor_type_out = $form_monitor_type;
		if ($form_monitor_type eq "") { $monitor_type_out = "Bits/Second"; }
		if ($form_monitor_type eq "Individual") { $monitor_type_out = "Bits/Second"; }
		if ($form_monitor_type =~ "bps") { $monitor_type_out = "Bits/Second"; }
		if ($form_monitor_type =~ "pps") { $monitor_type_out = "Packets/Second"; }
		if (($form_monitor_type eq "fpsi") || ($form_monitor_type eq "Individual-fps")) { $monitor_type_out = "Flows Initiated/Second"; }
		if (($form_monitor_type eq "fpsa") || ($form_monitor_type =~ /fps-prorated/)) { $monitor_type_out = "Flows Active/Second"; }
		if ($form_IPFIX) {
			print "  <td class=label>Monitor Type:&nbsp&nbsp</td>\n";
			print "  <td class=value>$monitor_type_out</td>\n";
		} else {
			print "  <tr>\n";
			print "  <td class=label>Monitor Type:&nbsp&nbsp</td>\n";
			print "  <td class=value>$monitor_type_out</td>\n";
		}
		print "  </tr>\n";
	} else {
		if (($form_graph_type eq "bpsa") || ($form_graph_type eq "ppsa") || ($form_graph_type eq "fpsia") || ($form_graph_type eq "fpsaa")) {
			print "  <td class=label>Peak Period Obs:&nbsp&nbsp</td>\n";
			print "  <td class=value>$analyze_peak_width</td>\n";
		}
	}

	if (($called_by =~ "FlowMonitor") && ($form_general_comment ne "")) {

		print "  <tr>\n";
		print "  <td class=label>Comments:&nbsp&nbsp</td>\n";
		print "  <td class=value colspan=3>$form_general_comment</td>\n";
		print "  </tr>\n";
	}

	if (($form_sampling_multiplier > 1) && (!(($stat_report == 99) && ($IPFIX)))) {
		print "  <tr>\n";
		print "  <td class=label>Note:&nbsp&nbsp</td>\n";
		if (($print_report > 0) && ($print_report <= 10)) {
			print "  <td class=value colspan=3>The sampling multiplier option is not available for this report</td>\n";
		} else {
			print "  <td class=value colspan=3>*all values have been multiplied by the Sampling Multiplier: $form_sampling_multiplier</td>\n";
		}
		print "  </tr>\n";
	}

	if ((($form_print_report >= 12) && ($form_print_report <= 17)) && (($form_source_addresses eq "") && ($form_dest_addresses eq ""))) {
		print "  <tr>\n";
		print "  <td class=label>Note:&nbsp&nbsp</td>\n";
		print "  <td class=value colspan=3>You may change the mask using the Source or Dest IP: fields (e.g., /24)</td>\n";
		print "  </tr>\n";
	}

	print "  </table>\n";
}

sub load_filtering_parameters {

	($called_by,$filter_hash) = @_;

	if ($filter_hash eq "") {

		if ($called_by eq "FlowViewer")  { $filter_hash = "FV_"; }
		if ($called_by eq "FlowGrapher") { $filter_hash = "FG_"; }
		if ($called_by eq "FlowMonitor") { $filter_hash = "FM_"; }

	} else {

	        $filter_source = substr($filter_hash,0,2);
	        $filter_link   = substr($filter_hash,3,255);
		if ($filter_link =~ /^/) { 
			if (substr($filter_link,0,1) eq "^") { 
				$new_device = substr($filter_link,1,255);
				$filter_link = "";
			} else {
				($filter_filename,$new_device) = split(/\^/,$filter_link);
			}
			
			if (substr($new_device,0,3) eq "DDD") { $new_device   = substr($new_device,3,255); $new_exporter = ""; }
			if (substr($new_device,0,3) eq "EEE") { $new_exporter = substr($new_device,3,255); $new_device   = ""; }
			$filter_hash = $filter_source ."_". $filter_filename;
		}

	        if  ($filter_source eq "FV") { $filter_source_file = "$work_directory/$filter_filename"; }
	        if  ($filter_source eq "FG") { $filter_source_file = "$work_directory/$filter_filename"; }
	        if (($filter_source eq "FM") || (filter_source eq "FT")) { $filter_source_file = "$work_directory/$filter_filename"; }
	        if  ($filter_source eq "PV") { $filter_source_file = "$work_directory/$filter_filename"; }
	        if  ($filter_source eq "FL") { $filter_source_file = "$save_directory/$filter_filename.svf"; }
	        if  ($filter_source eq "SV") { 
			if (($filter_hash =~ /FlowMonitor/) || ($filter_hash =~ /FlowTracker/)) {
				$MT_saved_directory = substr($filter_link,0,25);
				$flowmonitor = substr($filter_link,26,255);
				if ($flowmonitor =~ /^/) { ($flowmonitor,$new_device_extra) = split(/\^/,$flowmonitor); }
		                if (-e "$filter_directory/$flowmonitor.grp") { $filter_suffix = ".grp"; }
		                if (-e "$filter_directory/$flowmonitor.fil") { $filter_suffix = ".fil"; }
				$filter_filename = $MT_saved_directory ."/". $flowmonitor . $filter_suffix;
			}
			$filter_source_file = "$save_directory/$filter_filename";
		}
	        if (($filter_source eq "MT") || ($filter_source eq "TR")) { 
			if (-e "$filter_directory/$filter_filename.archive") { $filter_filename .= ".archive"; }
			if (-e "$filter_directory/$filter_filename.grp") { $filter_filename .= ".grp"; }
			if (-e "$filter_directory/$filter_filename.fil") { $filter_filename .= ".fil"; }
			$filter_source_file = "$filter_directory/$filter_filename";
		}
	}

print DEBUG "filter_hash: $filter_hash  filter_source: $filter_source  filter_source_file: $filter_source_file\n";
        open(FILTER,"<$filter_source_file");
        while (<FILTER>) {
		chop;

		if ((($filter_source eq "MT") || ($filter_source eq "TR")) || (($filter_source eq "SV") && (($filter_hash =~ /FlowMonitor/) || ($filter_hash =~ /FlowTracker/)) )) {
                        $key = substr($_,0,8);
                        if ($key eq " input: ") {
                                ($input,$field,$field_value) = split(/: /);
	                        if ($field eq "device_name")         { $form_device_name = $field_value; }
	                        if ($field eq "Description")         { $form_Description = $field_value; }
	                        if ($field eq "create_time")         { $form_create_time = $field_value; }
	                        if ($field eq "start_date")          { $form_start_date = $field_value; }
	                        if ($field eq "start_time")          { $form_start_time = $field_value; }
	                        if ($field eq "end_date")            { $form_end_date = $field_value; }
	                        if ($field eq "end_time")            { $form_end_time = $field_value; }
	                        if ($field eq "source_addresses")    { $form_source_addresses = $field_value; }
	                        if ($field eq "source_ports")        { $form_source_ports = $field_value; }
	                        if ($field eq "source_ifs")          { $form_source_ifs = $field_value; }
	                        if ($field eq "sif_names")           { $form_sif_names = $field_value; }
	                        if ($field eq "source_ases")         { $form_source_ases = $field_value; }
	                        if ($field eq "dest_addresses")      { $form_dest_addresses = $field_value; }
	                        if ($field eq "dest_ports")          { $form_dest_ports = $field_value; }
	                        if ($field eq "dest_ifs")            { $form_dest_ifs = $field_value; }
	                        if ($field eq "dif_names")           { $form_dif_names = $field_value; }
	                        if ($field eq "dest_ases")           { $form_dest_ases = $field_value; }
	                        if ($field eq "protocols")           { $form_protocols = $field_value; }
	                        if ($field eq "tcp_flags")           { $form_tcp_flags = $field_value; }
	                        if ($field eq "tos_fields")          { $form_tos_fields = $field_value; }
	                        if ($field eq "exporter")            { $form_exporter = $field_value; }
	                        if ($field eq "nexthop_ips")         { $form_nexthop_ips = $field_value; }
	                        if(($field eq "monitor_type") || ($field eq "tracking_type")) { if ($field_value eq "Individual") { $form_monitor_type = "bps"; }
								       elsif ($field_value eq "Individual-bps")          { $form_monitor_type = "bps"; }
								       elsif ($field_value eq "Individual-bps-prorated") { $form_monitor_type = "bps"; }
								       elsif ($field_value eq "Individual-pps")          { $form_monitor_type = "pps"; }
								       elsif ($field_value eq "Individual-pps-prorated") { $form_monitor_type = "pps"; }
								       elsif ($field_value eq "Individual-fps")          { $form_monitor_type = "fpsi"; }
								       elsif ($field_value eq "Individual-fps-prorated") { $form_monitor_type = "fpsa"; }
								       else { $form_monitor_type = $field_value; }}
	                        if(($field eq "monitor_label") || ($field eq "tracking_label")) { $form_monitor_label = $field_value; }
	                        if ($field eq "general_comment")     { $form_general_comment = $field_value; }
				if ($field eq "alert_threshold")     { $form_alert_threshold = $field_value; }
				if ($field eq "alert_frequency")     { $form_alert_frequency = $field_value; }
				if ($field eq "alert_destination")   { $form_alert_destination = $field_value; }
				if ($field eq "sampling_multiplier") { $form_sampling_multiplier = $field_value; }
				if ($field eq "IPFIX")               { $form_IPFIX = $field_value; }
				if ($field eq "silk_field")          { $form_silk_field = $field_value; }
				if ($field eq "silk_other")          { $form_silk_other = $field_value; }
				if ($field eq "silk_rootdir")        { $form_silk_rootdir = $field_value; }
				if ($field eq "silk_class")          { $form_silk_class = $field_value; }
				if ($field eq "silk_flowtype")       { $form_silk_flowtype = $field_value; }
				if ($field eq "silk_type")           { $form_silk_type = $field_value; }
				if ($field eq "silk_sensors")        { $form_silk_sensors = $field_value; }
				if ($field eq "silk_switches")       { $form_silk_switches = $field_value; }
			}

		} else {

	                ($field,$field_value) = split(/: /);
	                if (/BEGIN FILTERING/) { $found_parameters = 1; next; }
	                if ($found_parameters) {
	                        if (/END FILTERING/) { last; }
	                        if ($field eq "filter_title")        { $filter_title = $field_value; }
	                        if ($field eq "device_name")         { $form_device_name = $field_value; }
	                        if ($field eq "start_date")          { $form_start_date = $field_value; }
	                        if ($field eq "start_time")          { $form_start_time = $field_value; }
	                        if ($field eq "end_date")            { $form_end_date = $field_value; }
	                        if ($field eq "end_time")            { $form_end_time = $field_value; }
	                        if ($field eq "source_addresses")    { $form_source_addresses = $field_value; }
	                        if ($field eq "source_ports")        { $form_source_ports = $field_value; }
	                        if ($field eq "source_ifs")          { $form_source_ifs = $field_value; }
	                        if ($field eq "sif_names")           { $form_sif_names = $field_value; }
	                        if ($field eq "source_ases")         { $form_source_ases = $field_value; }
	                        if ($field eq "dest_addresses")      { $form_dest_addresses = $field_value; }
	                        if ($field eq "dest_ports")          { $form_dest_ports = $field_value; }
	                        if ($field eq "dest_ifs")            { $form_dest_ifs = $field_value; }
	                        if ($field eq "dif_names")           { $form_dif_names = $field_value; }
	                        if ($field eq "dest_ases")           { $form_dest_ases = $field_value; }
	                        if ($field eq "protocols")           { $form_protocols = $field_value; }
	                        if ($field eq "tcp_flags")           { $form_tcp_flags = $field_value; }
	                        if ($field eq "tos_fields")          { $form_tos_fields = $field_value; }
	                        if ($field eq "exporter")            { $form_exporter = $field_value; }
	                        if ($field eq "nexthop_ips")         { $form_nexthop_ips = $field_value; }
	                        if(($field eq "monitor_type") || ($field eq "tracking_type")) { if ($field_value eq "Individual") { $form_monitor_type = "bps"; }
								       elsif ($field_value eq "Individual-bps")          { $form_monitor_type = "bps"; }
								       elsif ($field_value eq "Individual-bps-prorated") { $form_monitor_type = "bps"; }
								       elsif ($field_value eq "Individual-pps")          { $form_monitor_type = "pps"; }
								       elsif ($field_value eq "Individual-pps-prorated") { $form_monitor_type = "pps"; }
								       elsif ($field_value eq "Individual-fps")          { $form_monitor_type = "fpsi"; }
								       elsif ($field_value eq "Individual-fps-prorated") { $form_monitor_type = "fpsa"; }
								       else { $form_monitor_type = $field_value; }}
	                        if(($field eq "monitor_label") || ($field eq "tracking_label")) { $form_monitor_label = $field_value; }
	                        if(($field eq "monitor_status") || ($field eq "tracking_status"))    { $form_monitor_status = $field_value; }
	                        if ($field eq "general_comment")     { $form_general_comment = $field_value; }
	                        if ($field eq "sampling_multiplier") { $form_sampling_multiplier = $field_value; }
				if ($field eq "stat_report")         { $form_stat_report = $field_value; }
				if ($field eq "print_report")        { $form_print_report = $field_value; }
				if ($field eq "flow_select")         { $form_flow_select = $field_value; }
				if ($field eq "sort_field")          { $form_sort_field = $field_value; }
				if ($field eq "pie_charts")          { $form_pie_charts= $field_value; }
				if ($field eq "flow_analysis")       { $form_flow_analysis= $field_value; }
				if ($field eq "cutoff_lines")        { $form_cutoff_lines = $field_value; }
				if ($field eq "cutoff_octets")       { $form_cutoff_octets = $field_value; }
				if ($field eq "unit_conversion")     { $form_unit_conversion = $field_value; }
				if ($field eq "detail_lines")        { $form_detail_lines = $field_value; }
				if ($field eq "bucket_size")         { $form_bucket_size = $field_value; }
				if ($field eq "resolve_addresses")   { $form_resolve_addresses = $field_value; }
				if ($field eq "graph_multiplier")    { $form_graph_multiplier = $field_value; }
				if ($field eq "stats_method")        { $form_stats_method = $field_value; }
		                if ($field eq "graph_type")          { if    ($field_value eq "Bits")      { $form_graph_type = "bps";  }
								       elsif ($field_value eq "Bits_P")    { $form_graph_type = "bps";  }
								       elsif ($field_value eq "Packets")   { $form_graph_type = "pps";  }
								       elsif ($field_value eq "Packets_P") { $form_graph_type = "pps";  }
								       elsif ($field_value eq "Flows")     { $form_graph_type = "fpsi"; }
								       elsif ($field_value eq "Flows_I")   { $form_graph_type = "fpsi"; }
								       elsif ($field_value eq "Flows_P")   { $form_graph_type = "fpsa"; }
								       else  {$form_graph_type = $field_value; } }
				if ($field eq "IPFIX")               { $form_IPFIX = $field_value; }
				if ($field eq "silk_field")          { $form_silk_field = $field_value; }
				if ($field eq "silk_other")          { $form_silk_other = $field_value; }
				if ($field eq "silk_rootdir")        { $form_silk_rootdir = $field_value; }
				if ($field eq "silk_class")          { $form_silk_class = $field_value; }
				if ($field eq "silk_flowtype")       { $form_silk_flowtype = $field_value; }
				if ($field eq "silk_type")           { $form_silk_type = $field_value; }
				if ($field eq "silk_sensors")        { $form_silk_sensors = $field_value; }
				if ($field eq "silk_switches")       { $form_silk_switches = $field_value; }
	                }
		}
        }
	close(FILTER);
}

sub get_monitor_title {

	my ($filter_filename,$suffix) = @_;
	
	$check_file = "$filter_directory/$filter_filename.fil";
	if (-e $check_file) { $filter_source_file = "$filter_directory/$filter_filename.fil"; }
	$check_file = "$filter_directory/$filter_filename.grp";
	if (-e $check_file) { $filter_source_file = "$filter_directory/$filter_filename.grp"; }
	$check_file = "$filter_directory/$filter_filename.archive";
	if (-e $check_file) { $filter_source_file = "$filter_directory/$filter_filename.archive"; }

        open(FILTER,"<$filter_source_file");
        while (<FILTER>) {
		chop;
                $key = substr($_,0,8);
                if ($key eq " input: ") {
                        ($input,$field,$field_value) = split(/: /);
	                if (($field eq "monitor_label") || ($field eq "tracking_label")) { 
				$monitor_title = $field_value; 
				last;
			}
		}
	}
	close(FILTER);

	return $monitor_title;
}

sub start_saved_file {

	my ($saved_file) = @_;

        ($temp_mnth_s,$temp_day_s,$temp_yr_s) = split(/\//,$start_date);
        ($temp_mnth_e,$temp_day_e,$temp_yr_e) = split(/\//,$end_date);

	if ($date_format eq "DMY") { 
		$start_date_save = $temp_day_s ."/". $temp_mnth_s ."/". $temp_yr_s;
		$end_date_save   = $temp_day_e ."/". $temp_mnth_e ."/". $temp_yr_e;
	} elsif ($date_format eq "DMY2") {
		$start_date_save = $temp_day_s .".". $temp_mnth_s .".". $temp_yr_s;
		$end_date_save   = $temp_day_e .".". $temp_mnth_e .".". $temp_yr_e;
	} elsif ($date_format eq "YMD") {
		$start_date_save = $temp_yr_s ."-". $temp_mnth_s ."-". $temp_day_s;
		$end_date_save   = $temp_yr_e ."-". $temp_mnth_e ."-". $temp_day_e;
	} else {
		$start_date_save = $start_date;
		$end_date_save   = $end_date;
	}

	open (SAVED,">$saved_file");

        print SAVED "<!-- BEGIN FILTERING PARAMETERS\n";
        print SAVED "filter_hash: $filter_hash\n";
        print SAVED "filter_title: $filter_title\n";
        print SAVED "device_name: $device_name\n";
        print SAVED "start_date: $start_date_save\n";
        print SAVED "start_time: $start_time\n";
        print SAVED "end_date: $end_date_save\n";
        print SAVED "end_time: $end_time\n";
        print SAVED "source_addresses: $source_addresses\n";
        print SAVED "source_ports: $source_ports\n";
        print SAVED "source_ifs: $source_ifs\n";
        print SAVED "sif_names: $sif_names\n";
        print SAVED "source_ases: $source_ases\n";
        print SAVED "dest_addresses: $dest_addresses\n";
        print SAVED "dest_ports: $dest_ports\n";
        print SAVED "dest_ifs: $dest_ifs\n";
        print SAVED "dif_names: $dif_names\n";
        print SAVED "dest_ases: $dest_ases\n";
        print SAVED "protocols: $protocols\n";
        print SAVED "tcp_flags: $tcp_flags\n";
        print SAVED "tos_fields: $tos_fields\n";
        print SAVED "exporter: $exporter\n";
        print SAVED "nexthop_ips: $nexthop_ips\n";
        print SAVED "monitor_type: $monitor_type\n";
        print SAVED "monitor_label: $monitor_label\n";
        print SAVED "monitor_status: $monitor_status\n";
        print SAVED "general_comment: $general_comment\n";
        print SAVED "description: $description\n";
        print SAVED "sampling_multiplier: $sampling_multiplier\n";
        print SAVED "stat_report: $stat_report\n";
        print SAVED "print_report: $print_report\n";
        print SAVED "flow_select: $flow_select\n";
        print SAVED "sort_field: $sort_field\n";
        print SAVED "pie_charts: $pie_charts\n";
	print SAVED "flow_analysis: $flow_analysis\n";
        print SAVED "cutoff_lines: $cutoff_lines\n";
        print SAVED "cutoff_octets: $cutoff_octets\n";
        print SAVED "unit_conversion: $unit_conversion\n";
        print SAVED "detail_lines: $detail_lines\n";
        print SAVED "bucket_size: $bucket_size\n";
        print SAVED "resolve_addresses: $resolve_addresses\n";
        print SAVED "graph_multiplier: $graph_multiplier\n";
        print SAVED "stats_method: $stats_method\n";
        print SAVED "graph_type: $graph_type\n";
        print SAVED "alert_threshold: $alert_threshold\n";
        print SAVED "alert_frequency: $alert_frequency\n";
        print SAVED "alert_destination: $alert_destination\n";
        print SAVED "IPFIX: $IPFIX\n";
        print SAVED "silk_rootdir: $silk_rootdir\n";
        print SAVED "silk_class: $silk_class\n";
        print SAVED "silk_flowtype: $silk_flowtype\n";
        print SAVED "silk_type: $silk_type\n";
        print SAVED "silk_sensors: $silk_sensors\n";
        print SAVED "silk_switches: $silk_switches\n";
        print SAVED "<END FILTERING PARAMETERS -->\n";
	
	close(SAVED);
}
	
return 1;
