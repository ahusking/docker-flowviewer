FROM ahusking/ubuntu-base
MAINTAINER Andrew Husking (andrew@husking.id.au)

RUN echo ServerName `hostname` >> /etc/apache2/apache2.conf
RUN  a2enmod cgi
RUN printf '\n%s\n  %s\n  %s\n  %s\n %s\n' '<Directory /usr/lib/cgi-bin>' 'Options Indexes FollowSymLinks'  'AllowOverride None' 'Require all granted' '</Directory>' >> /etc/apache2/apache2.conf

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
RUN ln -s /usr/lib/cgi-bin/FlowViewer/FlowViewer.pdf /var/www/html/FlowViewer/FlowViewer.pdf

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

RUN echo '<HTML><HEAD><meta http-equiv="refresh" content="0; url=cgi-bin/FlowViewer/FV.cgi" /></HEAD></HTML>' > /var/www/html/index.html

COPY scripts/FlowTracker /etc/init.d/FlowTracker
RUN chmod a+x /etc/init.d/FlowTracker
RUN update-rc.d FlowTracker defaults 30
RUN update-rc.d apache2 defaults
RUN mkdir -p /opt/scripts/
COPY scripts/init.sh /opt/scripts/init.sh
COPY scripts/CreateHostDirs.sh /opt/scripts/CreateHostDirs.sh

#crontab to clean files

EXPOSE 80
EXPOSE 9996
volume /data
CMD /bin/bash /opt/scripts/init.sh

