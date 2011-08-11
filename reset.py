import os
from optparse import OptionParser
try:
    import json    #python2.6
except ImportError:
    import simplejson as json #python2.5

def load_config (path):
	file = open(path, 'r')
	config_data = file.read()
	return json.loads(config_data)

def delete_dir_contents (path):
	for file in os.listdir(path):
		file_path = os.path.join(path, file)
		delete_file(file_path)

def delete_file (path):
	try:
		if os.path.isfile(path):
			os.unlink(path)
	except Exception, e:
		print e

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--config", dest="config_path", help="File to read configuration settings from.")
	(options, args) = parser.parse_args()
	config = load_config(options.config_path);
	#delete database
	delete_file(config['database'])
	#delete saved files
	delete_dir_contents(config['files'])
