#!/bin/sh
CMD=`ps aux | grep  python | grep -v grep -c`
echo "$CMD"
if [ "$CMD" != 7 ]
then
	echo $?
	date
	echo "Something's missing"
	Temp=`ps o cmd= | grep wemo -c`
	echo "$Temp"
	if [ "$Temp" != 2 ]
	then
	        echo "Not found wemo"
		nohup python /home/pi/Connectors/wemo/sens_wemo.py > /dev/null 2>/tmp/errwemo.log &
	fi

	Temp=`ps o cmd= | grep NEST -c`
	if [ "$Temp" != 2 ]
	then
	echo "Not found nest"
		nohup python /home/pi/Connectors/nest/NEST-CLASS.py > /dev/null 2>/tmp/errnest.log &
	fi

	Temp=`ps o cmd= | grep lifx -c`
	if [ "$Temp" != 2 ]
	then
	echo "Not found lifx"
		nohup python /home/pi/Connectors/lifx/sens_lifx.py > /dev/null 2>/tmp/errlifx.log &
	fi

	Temp=`ps o cmd= | grep mother -c`
	if [ "$Temp" != 2 ]
	then
	echo "Not found mother"
		nohup python /home/pi/Connectors/mother/sens_mother.py > /dev/null 2>/tmp/errmother.log &
	fi

	Temp=`ps o cmd= | grep netatmo -c`
	if [ "$Temp" != 2 ]
	then
	echo "Not found netatmo"
		nohup python /home/pi/Connectors/netatmo/sens_netatmo.py > /dev/null 2>/tmp/errnetatmo.log &
	fi

else
	echo "lol"
fi

