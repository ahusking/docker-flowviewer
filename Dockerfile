FROM ubuntu:latest
MAINTAINER Andrew Husking (andrew@husking.id.au)
RUN apt-get update
RUN apt-get -y -q install curl apache2 libgd-graph-perl rrdtool dnsutils flow-tools wget vim

#RUN wget -O /usr/local/src/FlowViewer_4.6.tar 'https://downloads.sourceforge.net/project/flowviewer/FlowViewer_4.6.tar?r=&ts=1494489766&use_mirror=nchc'
#RUN tar xvf /usr/local/src/FlowViewer_4.6.tar -C /usr/local/src
#RUN mv /usr/local/src/FlowViewer_4.6 /usr/lib/cgi-bin
RUN  a2enmod cgi
RUN printf '\n%s\n  %s\n  %s\n  %s\n %s\n' '<Directory /usr/lib/cgi-bin>' 'Options Indexes FollowSymLinks'  'AllowOverride None' 'Require all granted' '</Directory>' >> /etc/apache2/apache2.conf
RUN service apache2 restart

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV TZ=Australia/Canberra

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY FlowViewer_4.6/ /usr/lib/cgi-bin/FlowViewer/
RUN mkdir -p /var/www/html/FlowViewer
RUN mkdir -p /var/www/html/FlowGrapher
RUN mkdir -p /var/www/html/FlowTracker
RUN mkdir -p /var/www/html/FlowMonitor

RUN ln -s /usr/lib/cgi-bin/ /var/www/cgi-bin
RUN ln -s /usr/lib/cgi-bin/FlowViewer/FlowViewer.css /var/www/html/FlowViewer/FlowViewer.css
RUN ln -s /usr/lib/cgi-bin/FlowViewer/FV_button.png /var/www/html/FlowViewer/FV_button.png
RUN ln -s /usr/lib/cgi-bin/FlowViewer/FG_button.png /var/www/html/FlowViewer/FG_button.png
RUN ln -s /usr/lib/cgi-bin/FlowViewer/FM_button.png /var/www/html/FlowViewer/FM_button.png

#RUN mkdir -p /var/www/cgi-bin/FlowViewer
RUN mkdir -p /var/www/cgi-bin/FlowGrapher
RUN mkdir -p /var/www/cgi-bin/FlowTracker
RUN mkdir -p /var/www/cgi-bin/FlowMonitor

RUN mkdir -p /var/www/cgi-bin/FlowViewer_Files
RUN mkdir -p /var/www/cgi-bin/FlowGrapher_Files
RUN mkdir -p /var/www/cgi-bin/FlowTracker_Files
RUN mkdir -p /var/www/cgi-bin/FlowMonitor_Files

RUN mkdir -p /var/www/cgi-bin/FlowViewer/Flow_Working

RUN chown -R root:www-data /var/www
RUN chmod u+rwx,g+rx,o+rx /var/www

RUN chown -R root:www-data /usr/lib/cgi-bin
RUN chmod u+rwx,g+rx,o+rx /usr/lib/cgi-bin
RUN mv /etc/flow-tools/flow-capture.conf /etc/flow-tools/flow-capture.conf.orig

COPY scripts/FlowTracker /etc/init.d/FlowTracker
RUN chmod a+x /etc/init.d/FlowTracker
RUN update-rc.d FlowTracker defaults 30


#crontab to clean files
#script to startup everything on container running, start/restart services
#script to read in the flow-capture conf and create the directories



EXPOSE 80
EXPOSE 9996

#ENTRYPOINT ["ping 127.0.0.1"]
#CMD ["-D", "FOREGROUND"]
#ENTRYPOINT ["/usr/sbin/apache2"]


#startup
#docker exec -it docker-flowviewer
#service apache2 restart
#mkdir -p /data/flows/HUM-EDUGW-FW01
#service flow-capture restart

