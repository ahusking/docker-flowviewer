FROM ubuntu:latest
MAINTAINER Andrew Husking (andrew@husking.id.au)
RUN apt-get update
RUN apt-get -y -q install curl apache2 libgd-graph-perl rrdtool dnsutils flow-tools wget

RUN wget -O /usr/local/src/FlowViewer_4.6.tar 'https://downloads.sourceforge.net/project/flowviewer/FlowViewer_4.6.tar?r=&ts=1494489766&use_mirror=nchc'
RUN tar xvf /usr/local/src/FlowViewer_4.6.tar -C /usr/local/src
RUN mv /usr/local/src/FlowViewer_4.6 /usr/lib/cgi-bin
RUN  a2enmod cgi
RUN service apache2 restart

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2

RUN chown -R root:www-data /var/www
RUN chmod u+rwx,g+rx,o+rx /var/www

RUN chown -R root:www-data /usr/lib/cgi-bin
RUN chmod u+rwx,g+rx,o+rx /usr/lib/cgi-bin

EXPOSE 80

#ENTRYPOINT ["ping 127.0.0.1"]
#CMD ["-D", "FOREGROUND"]
#ENTRYPOINT ["/usr/sbin/apache2"]
