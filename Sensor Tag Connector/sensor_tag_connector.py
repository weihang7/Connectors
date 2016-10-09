import struct
import math
import sys,getopt
import pexpect
import time
import binascii
import time
import threading

from json_setting import JsonSetting
from buildingdepot_helper import BuildingDepotHelper

lock = threading.RLock()


#Lists containing the handles of the sensors to switch them on and to
#read the response from them

sensors = ['Temperature',
		 'Humidity',
		 'Lux',
		 'Pressure',
		 'Accelerometer X',
		 'Accelerometer Y',
		 'Accelerometer Z',
		 'Gyrometer X',
		 'Gyrometer Y',
		 'Gyrometer Z',
		 'Magnetomitor X',
		 'Magnetomitor Y',
		 'Magnetomitor Z',
	]

sensor_handles = ['0x24', # IR Temperature Sensor
					'0x2C', # Humidity Sensor
					'0x44', # Light Sensor
					'0x34', # Pressure Sensor
					'0x3C', # Accelerometer,Gyrometer and Compass
					]

sensor_handle_responses = ['0x0021', # IR Temperature Sensor
						'0x0029', # Humidity Sensor
						'0x0041', # Light Sensor
						'0x0031', # Pressure Sensor
						'0x0039', # Accelerometer,Gyrometer and Compass'''
						]

sensor_handle_notifications = ['0x22', # IR Temperature Sensor
						'0x2A', # Humidity Sensor
						'0x42', # Light Sensor
						'0x32', # Pressure Sensor
						'0x3A', # Accelerometer,Gyrometer and Compass'''
						]
sensor_handle_sampling_periods = ['0x0026', #IR Temperature Sensor
						'0x002E', # Humidity Sensor
						'0x0026', # Light Sensor
						'0x0036', # Pressure Sensor
						'0x003E', # Motion Sensor
						]

sensor_data_buffer = [[],[],[],[],[],[],[],[],[],[],[],[],[],[]]

class DataStoreThread(threading.Thread):
	'''Uploads bufferd sensor data periodically

	The main loop in the main funciton stores sensor data received via BLE into
	sensor_data_buffer. This thread upload the buffered data to Building Depot
	periodically using its REST API (wrapped in GiottoHelper class).
	'''
	def __init__(self, data_upload_delay):
		'''Initialize class and set upload period
	
		Args:
			data_upload_period: A number of seconds to be waited between data uploads
		'''
		super(DataStoreThread, self).__init__()

		global sensor_data_buffer
		sensor_data_buffer = []
		for i in range(len(sensors)+1):
			sensor_data_buffer.append([])

		self.data_upload_delay = 1
		self.stop_event = threading.Event()
		self.last_executed = 0

		connector_setting = JsonSetting('./connector_setting.json')
		self.sensor_uuids = connector_setting.get('sensor_uuids')
		self.bd_helper = BuildingDepotHelper('./buildingdepot_setting.json')

	def run(self):
		'''Starts data upload loop'''

		global sensor_data_buffer
		print "Sampling started"

		while not self.stop_event.is_set():
			time.sleep(self.data_upload_delay)
			lock.acquire()
			try:
				temp = sensor_data_buffer
				sensor_data_buffer = []
				for i in range(len(sensors)+1):
					#change made
					sensor_data_buffer.append([])
				print sensor_data_buffer;
			finally:
				lock.release()

			data_array = []

			for i in range(len(temp)):
				sensor = {}
				sensor['sensor_id'] = self.sensor_uuids[i]
				sensor['samples'] = temp[i]
				sensor['value_type'] = ''
				data_array.append(sensor)
			print(data_array);
			result = self.bd_helper.post_data_array(data_array)
			print result
			
		print "Sampling finished"

	def stop(self):
		'''stops data upload loop'''
		self.stop_event.set()

#Driving the gatttool via pexpect to connect to the SensorTag
def connect_to_tag(mac_address):
	'''Connects to a SensorTag

	Uses pexpect to connect to a SensorTag with a given MAC address with gatttool.

	Args:
		mac_address: A MAC address of a SensorTag

	Returns:
		pexpect spawn instance used to send/receive messages with a SensorTag
	'''
	gatt_interface = pexpect.spawn('gatttool -b '+mac_address+' --interactive')
	gatt_interface.expect('\[LE\]')
	gatt_interface.sendline('connect')
	print "connected"
	return gatt_interface

def turn_on_sensors(gatt_interface):
	'''Turns on all sensors on a SensorTag

	Sends commands to turn on sensors on a SensorTag. There are cases where sensors
	are not turned on appropriately. Thus, after sending these commands, we have to
	check whehter sensors are returning non-zero values.

	Args:
		gatt_interface: pexpect instance communicating with a SensorTag
	'''
	for handle in sensor_handles:
		if handle == '0x3C':
			cmd = 'char-write-cmd ' + handle + ' 7f:7f'
		else:
			cmd = 'char-write-cmd ' + handle + ' 01'
		gatt_interface.sendline(cmd)
		gatt_interface.expect('\[LE\]')


def set_notifications(gatt_interface, is_enabled):
	'''Sets notifications from a SensorTag

	Enables/disables notification from a SensorTag. When enables, whenever a new sensor
	reading is obtained in SensorTag, the new reading is sent to the gatt_interface
	from the SensorTag.

	Args:
		gatt_interface: pexpect instance communicating with a SensorTag	
	'''
	for handle in sensor_handle_notifications:
		if is_enabled == 1:
			cmd = 'char-write-cmd '+handle+' 01:00'
		else:
			cmd = 'char-write-cmd '+handle+' 00:00'
		gatt_interface.sendline(cmd)
		gatt_interface.expect('\[LE\]')


def calculate_int_value(value_list, offset):
	'''Extracts int value from hex'''
	hexStr = binascii.unhexlify(valueList[offset]+value_list[offset+1])
	int_value = struct.unpack('>h',hexStr)
	return int(int_value[0])


def calculate_unsigned_int_value(value_list,offset):
	'''Extract unsigned int from hex'''
	int_value = (int(value_list[offset+1],16)<<(8))+(int(value_list[offset],16))
	return int_value


def calculate_signed_int_value(value_list,offset):
	'''Extracts signed int from hex'''
	hexStr = binascii.unhexlify(value_list[offset]+value_list[offset+1])
	int_value = struct.unpack('<h',hexStr)
	return int(int_value[0])


def convert_temperature(temperature):
	'''Calcualtes temperature value from hex'''
	val = calculate_unsigned_int_value(temperature,2)/128.0
	return val


def convert_humidity(humidity):
	'''Calcualtes humidity value from hex'''
	h = calculate_unsigned_int_value(humidity,2)
	h = h - (h%4)
	h = ((-6.0) + 125.0 * (h/ 65535.0))
	return h


def convert_lux(lux):
	'''Calcualtes LUX value from hex'''
	level = calculate_unsigned_int_value(lux,0)
	mantissa = level & 0x0FFF
	exponent = (level >> 12) & 0xFF
	magnitude = pow(2.0, exponent)
	output = (mantissa * magnitude)
	val = output / 100
	return val


def convert_pressure(pressure):
	'''Calcualtes pressure value from hex'''
	level = calculate_unsigned_int_value(pressure,3)
	mantissa = level & 0x0FFF
	exponent = (level >> 12) & 0xFF
	magnitude = pow(2.0, exponent)
	output = (mantissa * magnitude)
	val = output / 100
	return val


def convert_agc(agc):
	'''Calcualtes acceleration, gyro, and magnetomitor values from hex'''
	values = []
	values.append(calculate_signed_int_value(agc,0) / 128.)
	values.append(calculate_signed_int_value(agc,2) / 128.)
	values.append(calculate_signed_int_value(agc,4) / 128.)
	values.append(calculate_signed_int_value(agc,6) / 4096.)
	values.append(calculate_signed_int_value(agc,8) / 4096.)
	values.append(calculate_signed_int_value(agc,10)/ 4096.)
	values.append(calculate_signed_int_value(agc,12)/ (32768. / 4912.))
	values.append(calculate_signed_int_value(agc,14)/ (32768. / 4912.))
	values.append(calculate_signed_int_value(agc,16)/ (32768. / 4912.))

	return values


# Set a sampling rate to all sensors
def set_sampling_rate(gatt_interface, sampling_rate):
	'''Configures sampling rates for sensors on a SensorTag

	Configures sampling rates. If a specified sampling rate is higher than
	one that can be configured on a SensorTag, set the highest sampling rate
	intead. Motion sensor can be configured as low as 0.1 sec. Other sensors
	can be as low as 0.3 sec. If you need a higher sampling rates, you need to
	modify code on a SensorTag. 

	Args:
		gatt_interface: pexpect instance communicating with a SensorTag
		sampling_rate: A sampling rate in sec
	'''
	val = sampling_rate * 100

	for handle in sensor_handle_sampling_periods:
		# check minimal sampling
		if handle == '0x0026' or handle == '0x002E' or handle == '0x003E':
			val = 100 * max(0.3, sampling_rate)
		else:
			val = 100 * max(0.1, sampling_rate)

		valString = hex(int(val))[2:]
		if len(valString) == 1:
			valString = '0' + valString

		cmd = 'char-write-cmd ' + handle + " " + valString
		gatt_interface.sendline(cmd)
		gatt_interface.expect('\[LE\]')


#Get the data from the sensor corresponding to that specific handle
def get_data(gatt_interface, handle):
	'''Read sensor data for a given handle from a SensorTag

	Sends a command to a connected SensorTag to get a sensor reading. The
	mappting between handles and sensors is defined in sensor_handles.

	Args:
		gatt_interface: pexpect instance communicating with a SensorTag
		handle: A sensor's handle value (defined in sensor_handles)
	Returns:
		A sensor reading as a hex value
	'''
	gatt_interface.sendline('char-read-hnd '+handle)
	print "in_get_data";
	gatt_interface.expect("Characteristic value/descriptor: .* \r\n")
	dataStr = gatt_interface.after.split(": ")[1]
	print dataStr;
	return dataStr.split()

def get_all_sensor_data(gatt_interface):
	'''Gets all sensor readings

	Args:
		gatt_interface: pexpect instance communicating with a SensorTag
	Returns:
		Sensor readings in a numpy array	
	'''
	values = []

	for handle in sensor_handle_responses:
		if handle == '0x0021': #IR Temperature Sensor
			values.append(convert_temperature(get_data(gatt_interface, handle)))
		elif handle == '0x0029': #Humidity Sensor
			values.append(convert_humidity(get_data(gatt_interface, handle)))
		elif handle == '0x0041': #Light Sensor
			values.append(convert_lux(get_data(gatt_interface, handle)))
		elif handle == '0x0031': #Pressure Sensor
			values.append(convert_pressure(get_data(gatt_interface, handle)))
		elif handle == '0x0039': # Accelerometer,Gyrometer and Compass
			values.extend(convert_agc(get_data(gatt_interface, handle)))
	print values;
	return values

def are_sensor_readings_valid(gatt_interface):
	'''Checks if sensors are returning valid readings

	Fetches all sensor readings and see if they are non-zero values.

	Args:
		gatt_interface: pexpect instance communicating with a SensorTag
	Returns:
		True if all sensor readings are valid, False otherwise
	'''
	result = True
	print "in_are_sensor_readings";
	val = get_all_sensor_data(gatt_interface)

	print val

	for i in range(13):
		if val[i] == 0:
			print "Warning: " + sensors[i] + " sensor is returning 0."
			result = False

	return result

def save_data_to_buffer(index, value):
	'''Stores a sensor reading to buffer

	Acquires lock first to prevent the other thread to manipulate the buffer, and
	stores a sensor reading(s) in the buffer. When index == 4, value is an array
	consisting of 9 values (accelerometer, gyro, and magnetometer data). In this
	case, calculate a norm of accelerometer data and store 10 readings in the
	buffer. Value type is passed because Building Depot's REST API has value type
	as a parameter, however, it is not used in this version.

	Args:
		index: An index of sensor reading(s)
		value: A value(s)
	'''
	lock.acquire()

	try:
		t = time.time()
		if(index!=4):
			data = {}
			data['time'] = t
			data['value'] = value
			sensor_data_buffer[index].append(data)

		else:
			for i in range(9):
				data = {}
				data['time'] = t
				data['value'] = value[i]
				sensor_data_buffer[index+i].append(data)

			data = {}
			data['time'] = t
			data['value'] = math.sqrt(value[0]*value[0] + value[1]*value[1] + value[2]*value[2])

			sensor_data_buffer[index+9].append(data)

	finally:
		lock.release()

def extract_values_from_data_string(data_string):
	'''Extracts a value from data string and stores it in th buffer

	Extracts a value from data string sent from a SensorTag. Then, stores the data
	to th buffer.

	Args:
		data_string: a sensor reading(s) in a string format
	'''
	data_string = data_string.strip().split(" value: ")
	handle = data_string[0].split(' = ')[1]

	# extract a data part
	index = sensor_handle_responses.index(handle)
	data = data_string[1].split();

	if handle == '0x0021': #IR Temperature Sensor
		val = convert_temperature(data);
	elif handle == '0x0029': #Humidity Sensor
		val = convert_humidity(data);
	elif handle == '0x0041': #Light Sensor
		val = convert_lux(data)
	elif handle == '0x0031': #Pressure Sensor
		val = convert_pressure(data)
	elif handle == '0x0039': # Accelerometer,Gyrometer and Compass
		val = convert_agc(data)
	
	index = sensor_handle_responses.index(handle)
	save_data_to_buffer(index, val)


def setup_sensortag(mac_address):
	'''Initialize a SensorTag

	Connects to a SensorTag via BLE and configure sampling rates and notifications.

	Args:
		mac_address: A MAX address of a SensorTag

	Returns:
		gatt_interface: pexpect instance communicating with a SensorTag		
	'''
	print "Connecting to the SensorTag"

	gatt_interface = connect_to_tag(mac_address)
	print "Turning on sensors"

	turn_on_sensors(gatt_interface)
	time.sleep(1)

	# Make sure all sensors are working
	while not are_sensor_readings_valid(gatt_interface):
		print "Some sensors are not initialized. Turning on sensors again."

		turn_on_sensors(gatt_interface)
		time.sleep(1)

	# Configure sampling rates
	set_notifications(gatt_interface, 0)	# Disable notification first
	set_sampling_rate(gatt_interface, 0.1)

	# Turn on notificaitons
	set_notifications(gatt_interface, 1)

	print "Starting data collection"

	return gatt_interface


if __name__ == "__main__":
	'''Initializes a SensorTag and continuously collect data from it
	'''
	SAMPLING_RATE = 1
	MAX_SAMPLING_NUMBER = 10


	connector_setting = JsonSetting('./connector_setting.json')
	bd_helper = BuildingDepotHelper('./buildingdepot_setting.json')

	# Turn on and configure a SensorTag
	mac_address = connector_setting.get('sensor_tag')['mac_address']
	print mac_address;
	gattInterface = setup_sensortag(mac_address)

	# Start a thread that post sampled data to a GIoTTO server
	dataStoreThread = DataStoreThread(SAMPLING_RATE)
	dataStoreThread.start()

	try:
		while True:
			#Process each notification as it is received and convert the sensor value
			#according to the handle
			gattInterface.expect('Notification handle = .* \r\n')

			receivedString = gattInterface.after

			# split lines because multiple data can be notified at the same time
			data_strings = receivedString.strip().split("\r\n")
			for data_string in data_strings:
				if data_string[0:5] != "[LE]":	# neglect command lines
					extract_values_from_data_string(data_string)
	except KeyboardInterrupt:
		print "interrupted"
		dataStoreThread.stop()

	except:
		dataStoreThread.stop()







		
