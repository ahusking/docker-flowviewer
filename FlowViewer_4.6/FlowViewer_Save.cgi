#! /usr/bin/perl
#
#  Purpose:
#  FlowViewer_Save.cgi controls the moving of a temporary copy of the
#  FlowViewer and FlowGrapher HTML files and the FlowGrapher graph image 
#  file to either the '$save_directory' specified in FV_Configuratoin.pm
#
#  Description:
#
#  Input arguments (received from the form):
#  Name                 Description
#  -----------------------------------------------------------------------
#  action               Name or Save filter or report
#  operand              Filter hash which is the name of the temp file 
#
#  Modification history:
#  Author       Date            Vers.   Description
#  -----------------------------------------------------------------------
#  J. Loiacono  07/04/2005      1.0     Original version.
#  J. Loiacono  01/01/2006      1.0     Updated for FlowGrapher
#  J. Loiacono  12/25/2006      3.1     [No changes to this module]
#  J. Loiacono  12/07/2007      3.3     Now handles saved filters
#  J. Loiacono  03/17/2011      3.4     Added capability to name Reports
#                                       Sorted reports by most recent
#  J. Loiacono  05/08/2012      4.0     Major upgrade for IPFIX/v9 using SiLK.
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
 
if ($debug_viewer eq "Y") { open (DEBUG,">>$work_directory/DEBUG_SAVE"); }

$query_string = $ENV{'QUERY_STRING'};
$query_string =~ s/%([0-9A-Fa-f]{2})/chr(hex($1))/ge;
($active_dashboard,$action,$operand) = split(/\^/,$query_string);

if ($debug_viewer eq "Y") { print DEBUG "active_dashboard: $active_dashboard   action: $action  operand: $operand\n"; }

if ($action eq "") { $action = "save_filter"; }

if ($action eq "name_report") {

	$filter_hash = $operand;

        $filter_source = substr($filter_hash,0,2);
        $filter_link   = substr($filter_hash,3,255);
        if ($filter_link =~ /^/) {
                if (substr($filter_link,0,1) eq "^") {
                        $new_device = substr($filter_link,1,255);
                        $filter_link = "";
                } else {
                        ($filter_filename,$new_device) = split(/\^/,$filter_link);
                }

                if (substr($new_device,0,3) eq "DDD") { $new_device   = substr($new_device,3,255); }
                if (substr($new_device,0,3) eq "EEE") { $new_exporter = substr($new_device,3,255); }
                $filter_hash = $filter_source ."_". $filter_filename;
        }

	if    ($filter_hash =~ "Viewer") { 
		$called_by = "FlowViewer"; }
	elsif ($filter_hash =~ "Grapher") { 
		$called_by = "FlowGrapher"; }
	elsif (substr($filter_hash,0,3) = "MT_") { 
		$monitor_save_directory = substr($filter_hash,3,255);
		$MT_suffix = &get_suffix;
		$filter_hash = "MT_FlowMonitor_save_" . $MT_suffix ."_".  $monitor_save_directory;
		$called_by = "FlowMonitor";
	}

	if (!-e $save_directory) { 
	      
		&create_UI_top($active_dashboard);
		&create_UI_service($called_by,"service_top",$active_dashboard,$filter_hash);
		print " <div id=content_wide>\n";

		print "<center>\n";
	        print "<br><br>"; 
	        print "Attempting to create a directory to hold Saved Reports:<br><br>";
		print "<b><i>$save_directory ...</b></i><br><br>"; 

	        mkdir($save_directory,$html_dir_perms) || die "cannot mkdir $save_directory: $!"; 
	        chmod $html_dir_perms, $save_directory; 
	      
	        print "The directory for saving FlowViewer and FlowGrapher reports has been created:<br><br>"; 
	        print "<b><i>$save_directory</i></b><br><br>"; 
	        print "Please ensure this directory has adequate permissions for<br>";
	        print "your web server process owner (e.g., 'apache') to write into it.<br>";
		print "</center>\n";

		$created_directory = 1;
	}

        if (!$created_directory) { 
		&create_UI_top($active_dashboard);
		&create_UI_service($called_by,"service_top",$active_dashboard,$filter_hash);
		print " <div id=content_wide>\n";
	}

	$button_text = "Save Report";
	print "  <center>\n";
	print "  <form action=$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^save_report^$filter_hash method=POST>\n";
	print "  <br><br><br>\n";
	print "  Report Name (Maximum 80 characters)\n";
	print "  <br><br>\n";
	print "  <span class=input_center>\n";
	print "  <input type=text style=\"clear: both\; width: 30em;\" name=report_name value=\"$report_name\">\n";
	print "  </span>\n";
	print "  <br><br><br>\n";
	print "  <input class=buttonc type=submit value=\"Save the Report\">\n";
	print "  <br><br><br>\n";
	print "  </form>\n";
	print "  </table>";

	print "  </center>\n";
	print " </div>\n";
	&create_UI_service($called_by,"service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page($called_by);
}
 
if ($action eq "save_report") {

	$filter_source = substr($operand,0,2);
	$save_filename = substr($operand,3,255);

	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
	@pairs = split(/&/, $buffer);
	foreach $pair (@pairs) {
	    ($name, $value) = split(/=/, $pair);
	    $value =~ tr/+/ /;
	    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
	    $FORM{$name} = $value;
	}
	 
	$report_name = $FORM{report_name};
	$report_name = substr($report_name,0,80);
	
	if ($debug_viewer eq "Y") { print DEBUG "FVS save_filename: $save_filename   report_name: $report_name\n"; }

	# Copy the temporary saved file to the Save Directory inserting the report title

	if ($save_filename =~ /Monitor/) {

		$MT_saved_directory = $save_directory ."/". substr($save_filename,0,25);	
		$flowmonitor = substr($save_filename,26,255);	
	        mkdir($MT_saved_directory,$html_dir_perms) || die "cannot mkdir $MT_saved_directory: $!"; 
	        chmod $html_dir_perms, $MT_saved_directory; 

	} else {
		if ($filter_source eq "SV") {
			open (TEMP,"<$save_directory/$save_filename");
			$new_suffix = &get_suffix;
			if ($save_filename =~ "Viewer") { 
				$old_piechart = $save_filename .".png";
				$save_filename = "FlowViewer_save_$new_suffix";
				$new_piechart = $save_filename .".png";
			} elsif ($save_filename =~ "Grapher") { 
				$old_graphname = $save_filename .".png";
				$save_filename = "FlowGrapher_save_$new_suffix";
				$new_graphname = $save_filename .".png";
			}
		} else {
			open (TEMP,"<$work_directory/$save_filename");
		}
		$create_time = time;
		open (SAVE,">$save_directory/$save_filename");
		while (<TEMP>) {
	                if (/BEGIN FILTERING/) { 
				$description_line = 1; 
				print SAVE $_;
				next; 
			} elsif ($description_line) {
				if (/Description/) {
					print SAVE "Description: $report_name\n";
					print SAVE "create_time: $create_time\n";
				} else {
					print SAVE "Description: $report_name\n";
					print SAVE "create_time: $create_time\n";
					print SAVE $_;
				}
				$description_line = 0;
			} else {
				print SAVE $_;
			}
		}
		close TEMP;
		close SAVE;
	}

	# If this is a FlowGrapher save, move the graph image to the saved directory

	if ($save_filename =~ /Grapher/) {

		$cgi_link = "$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=SV_$save_filename";
		if ($filter_source eq "SV") {
			$copy_command = "cp $save_directory/$old_graphname $save_directory/$new_graphname";
		} else {
			$save_graphname = $save_filename .".png";
			$copy_command = "cp $graphs_directory/$save_graphname $save_directory/$save_graphname";
		}
		system($copy_command);

	} elsif ($save_filename =~ /Viewer/) {

		$cgi_link = "$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=SV_$save_filename";
		if ($filter_source eq "SV") {
			$copy_command = "cp $save_directory/$old_piechart $save_directory/$new_piechart";
		} else {
			$save_piechart = $save_filename .".png";
			$copy_command = "cp $graphs_directory/$save_piechart $save_directory/$save_piechart";
		}
		system($copy_command);

	} elsif ($save_filename =~ /Monitor/) {

		$cgi_link = "$cgi_bin_short/FlowMonitor_Replay.cgi?$active_dashboard^filter_hash=SV_$save_filename";
		$flowmonitor_directory = $monitor_directory ."/". $flowmonitor ."/*";
		$copy_command = "cp $flowmonitor_directory $MT_saved_directory";
		system($copy_command);

                if (-e "$filter_directory/$flowmonitor.grp") { $filter_suffix = ".grp"; }
                if (-e "$filter_directory/$flowmonitor.fil") { $filter_suffix = ".fil"; }

		$monitor_filter = $filter_directory ."/". $flowmonitor . $filter_suffix;
		$copy_command = "cp $monitor_filter $MT_saved_directory";
		system($copy_command);

		$MT_saved_filter = $MT_saved_directory ."/". $flowmonitor . $filter_suffix;
		$create_time = time;
		open(MT_SAVED,">>$MT_saved_filter");
		print MT_SAVED " input: Description: $report_name\n";
		print MT_SAVED " input: create_time: $create_time\n";
		close(MT_SAVED);
	}

	print "Content-type:text/html\n\n";
	print "<head>";
	print "<META HTTP-EQUIV=Refresh CONTENT=\"0; URL=$cgi_link\">";
	print "</head>";
	print "<body bgcolor=$bg_color>";
	print "<title>Save FlowViewer or FlowGrapher</title>";
}

if ($action eq "name_filter") {

	$filter_hash = $operand;

        $filter_source = substr($filter_hash,0,2);
        $filter_link   = substr($filter_hash,3,255);
        if ($filter_link =~ /^/) {
                if (substr($filter_link,0,1) eq "^") {
                        $new_device = substr($filter_link,1,255);
                        $filter_link = "";
                } else {
                        ($filter_filename,$new_device) = split(/\^/,$filter_link);
                }

                if (substr($new_device,0,3) eq "DDD") { $new_device   = substr($new_device,3,255); }
                if (substr($new_device,0,3) eq "EEE") { $new_exporter = substr($new_device,3,255); }
                $filter_hash = $filter_source ."_". $filter_filename;
        }

	if ($filter_source eq "FV") { $called_by = "FlowViewer"; }
	if ($filter_source eq "FG") { $called_by = "FlowGrapher"; }
	if ($filter_source eq "MT") { 
		$called_by = "FlowMonitor";
                if (-e "$filter_directory/$filter_link.grp") { 
			&create_UI_top($active_dashboard);
			&create_UI_service($called_by,"service_top",$active_dashboard,$filter_hash);
			print " <div id=content_wide>\n";
		        print "  <br>";
		        print "  Cannot create a Filter for a Group\n";
		        print " </div>\n";
		        &create_UI_service("FlowMonitor","service_bottom",$active_dashboard,$filter_hash);
		        &finish_the_page("FlowMonitor");
		        exit;
		}
	}

	if (!-e $save_directory) { 
	      
		&create_UI_top($active_dashboard);
		&create_UI_service($called_by,"service_top",$active_dashboard,$filter_hash);
		print " <div id=content_wide>\n";

		print "<center>\n";
	        print "<pre><b>\n\n"; 
	        print "      Attempting to create a directory to hold Saved Filters: $save_directory ...\n\n"; 

	        mkdir($save_directory,$html_dir_perms) || die "cannot mkdir $save_directory: $!"; 
	        chmod $html_dir_perms, $save_directory; 
	      
	        print "      The directory for saving FlowViewer and FlowGrapher filters has been created:\n\n"; 
	        print "      <i>$save_directory</i>\n\n"; 
	        print "      Please ensure this directory has adequate permissions for your web server process\n";
	        print "      owner (e.g., 'apache') to write into it.\n";
	        print "</pre></b>";
		print "</center>\n";

		$created_directory = 1;
	}

        if (!$created_directory) { 
		&create_UI_top($active_dashboard);
		&create_UI_service($called_by,"service_top",$active_dashboard,$filter_hash);
		print " <div id=content_wide>\n";
	}

	$button_text = "Save Filter";
	print "  <center>\n";
	print "  <form action=$cgi_bin_short/FlowViewer_Save.cgi?$active_dashboard^save_filter^$filter_hash method=POST>\n";
	print "  <br><br><br>\n";
	print "  Filter Name (Maximum 80 characters)\n";
	print "  <br><br>\n";
	print "  <span class=input_center>\n";
	print "  <input type=text style=\"clear: both\; width: 30em;\" name=filter_name value=\"$filter_name\">\n";
	print "  </span>\n";
	print "  <br><br><br>\n";
	print "  <input class=buttonc type=submit value=\"Save the Filter\">\n";
	print "  <br><br><br>\n";
	print "  </form>\n";
	print "  </table>";
	print "  </center>\n";

	print " </div>\n";
	&create_UI_service($called_by,"service_bottom",$active_dashboard,$filter_hash);
	&finish_the_page($called_by);
}

if ($action eq "save_filter") {

	$filter_source = substr($operand,0,2);
	$save_filename = substr($operand,3,255);

	read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
	@pairs = split(/&/, $buffer);
	foreach $pair (@pairs) {
	    ($name, $value) = split(/=/, $pair);
	    $value =~ tr/+/ /;
	    $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C",hex($1))/eg;
	    $FORM{$name} = $value;
	}
	 
	$filter_name = $FORM{filter_name};
	$filter_name = substr($filter_name,0,80);
	
	if ($debug_viewer eq "Y") { print DEBUG "FVS save_filename: $save_filename   filter_name: $filter_name  filter_source: $filter_source\n"; }

	$filter_label = $filter_name;
	$filter_label =~ s/^\s+//;
	$filter_label =~ s/\s+$//;
	$filter_label =~ s/\&/-/g;
	$filter_label =~ s/\//-/g;
	$filter_label =~ s/\(/-/g;
	$filter_label =~ s/\)/-/g;
	$filter_label =~ s/\./-/g;
	$filter_label =~ s/\s+/_/g;
	$filter_label =~ tr/[A-Z]/[a-z]/;

	if ($filter_source eq "SV") {
		$saved_filename = "$save_directory/$save_filename";
	} elsif ($filter_source eq "MT") {
		$saved_filename = "$filter_directory/$save_filename";
		$flowmonitor_fil     = $saved_filename .".fil";
		$flowmonitor_archive = $saved_filename .".archive";
                if (-e "$flowmonitor_fil")     { $saved_filename = $flowmonitor_fil }
                if (-e "$flowmonitor_archive") { $saved_filename = $flowmonitor_archive }
	} else {
		$saved_filename = "$work_directory/$save_filename";
	}

	open (FILTER,">$save_directory/$filter_label.svf");
	open (TEMP,"<$saved_filename");

	if ($filter_source eq "MT") {
		print FILTER "<!-- BEGIN FILTERING PARAMETERS\n";
		print FILTER "filter_title: $filter_name\n";
		while (<TEMP>) {
	                if (/input:/) { 
				if (/revision:/) { next; }
				if (/last_notified:/) { next; }
				($input_label,$filter_line) = split(/input: /);
				print FILTER $filter_line;
			}
		}
		print FILTER "<END FILTERING PARAMETERS -->\n";
	} else {
		while (<TEMP>) {
	                if (/filter_title/) { 
				print FILTER "filter_title: $filter_name\n";
				next; 
	                } elsif (/start_date/) { 
				print FILTER "start_date:\n";
				next; 
	                } elsif (/start_time/) { 
				print FILTER "start_time:\n";
				next; 
	                } elsif (/end_date/) { 
				print FILTER "end_date:\n";
				next; 
	                } elsif (/end_time/) { 
				print FILTER "end_time:\n";
				next; 
			} elsif (/END FILTERING/) {
				print FILTER $_;
				last;
			} else {
				print FILTER $_;
			}
		}
	}
	close TEMP;
	close FILTER;

	if ($save_filename =~ "Viewer") {
		if ($filter_source eq "SV") {
			$cgi_link = "$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=SF_$save_filename";
		} else {
			$cgi_link = "$cgi_bin_short/FlowViewer_Replay.cgi?$active_dashboard^filter_hash=FL_$save_filename";
		}
	} elsif ($save_filename =~ "Grapher") {
		if ($filter_source eq "SV") {
			$cgi_link = "$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=SF_$save_filename";
		} else {
			$cgi_link = "$cgi_bin_short/FlowGrapher_Replay.cgi?$active_dashboard^filter_hash=FL_$save_filename";
		}
	} elsif ($filter_source eq "MT") {
		$cgi_link = "$cgi_bin_short/FlowMonitor_Display.cgi?$active_dashboard^filter_hash=MT_$save_filename";
	}

	print "Content-type:text/html\n\n";
	print "<head>";
	print "<META HTTP-EQUIV=Refresh CONTENT=\"0; URL=$cgi_link\">";
	print "</head>";
	print "<body bgcolor=$bg_color>";
	print "<title>Save FlowViewer or FlowGrapher Filter</title>";
}
