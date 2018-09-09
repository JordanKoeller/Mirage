from abc import ABC, abstractmethod, abstractproperty
import json

class FileManager(ABC):

	def __init__(self):
		self._filename = ''
		self._file = None

	def open(self,filename):
		self._filename = filename
		self._file = "exists"

	@abstractmethod
	def write(self,data):
		pass

	@abstractmethod
	def read(self):
		pass

	def close(self):
		if self._file:
			self._file.close()
		else:
			raise EnvironmentError("Cannot close a file that was never opened")

	@abstractproperty
	def extension(self):
		pass

class JsonFileManager(FileManager):

	def __init__(self,class_object,extension):
		self._class_object = class_object
		self._extension = extension

	@property
	def class_object(self):
		return self._class_object
	
	def open(self,filename):
		self._filename = filename
		self._file = None

	def read(self):
		self._file = open(self._filename,'rb')
		ending = self.find_end(self._file,self._file.tell())
		bites = self._file.read(ending)
		decoder = json.JSONDecoder()
		string = str(bites,'utf-8', errors = 'ignore')
		js, ind = decoder.raw_decode(string)
		return self.class_object.from_json(js)

	def write(self,obj:'Jsonable'):
		self._file = open(self._filename,'ab')
		js = obj.json
		formatted = self.format_json(js)
		self._file.write(bytes(formatted,'utf-8'))
		self._file.write(b'\x93')

	def find_end(self,file,start_point,end_char=b'\x93'):
		flag = True
		buf_sz = int(1e6)
		last_pt = file.tell()
		while flag:
			tmp = file.read(buf_sz)
			if end_char in tmp:
				flag = False
				ind = tmp.index(end_char)
				file.seek(start_point)
				last_pt = last_pt + ind
			elif len(tmp) == 0:
				file.seek(start_point)
				flag = False
				return last_pt
			else:
				last_pt = file.tell()
				file.seek(start_point)
		return last_pt

	def format_json(self,js):
		ret = json.dumps(js,indent=2)
		return ret

	@property
	def extension(self):
		return self._extension


def SimulationFileManager():
	from mirage.parameters import Simulation
	return JsonFileManager(Simulation)


def ParametersFileManager():
	from mirage.parameters import Parameters
	return JsonFileManager(Parameters)

