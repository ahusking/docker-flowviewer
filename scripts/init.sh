#!/bin/bash
service apache2 start &
service apache2 restart &
service FlowTracker start &
service FlowTracker restart &


#command="/bin/bash /opt/scripts/CreateHostDirs.sh"
#job="0 * * * * $command"
#cat <(fgrep -i -v "$command" <(crontab -l)) <(echo "$job") | crontab -
sleep infinity
