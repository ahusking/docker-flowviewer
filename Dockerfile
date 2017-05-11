FROM ubuntu:latest
MAINTAINER Andrew Husking
RUN apt-get update
RUN apt-get -y -q install curl apache2 libgd-graph-perl rrdtool dnsutils flow-tools wget

RUN wget -O /usr/local/src/FlowViewer_4.6.tar 'https://downloads.sourceforge.net/project/flowviewer/FlowViewer_4.6.tar?r=&ts=1494489766&use_mirror=nchc'
RUN tar xvf /usr/local/src/FlowViewer_4.6.tar -C /usr/local/src
RUN mv /usr/local/src/FlowViewer_4.6 /usr/lib/cgi-bin
RUN service apache2 start

EXPOSE 80

#ENTRYPOINT ["ping 127.0.0.1"]
#CMD ["-D", "FOREGROUND"]
#ENTRYPOINT ["/usr/sbin/apache2"]
