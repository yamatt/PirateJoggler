import os
import shelve
from optparse import OptionParser
try:
    import json    #python2.6
except ImportError:
    import simplejson as json #python2.5

def load_config (path):
	file = open(path, 'r')
	config_data = file.read()
	return json.loads(config_data)

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--config", dest="config_path", help="File to read configuration settings from.")
	(options, args) = parser.parse_args()
	config = load_config(options.config_path);
	db = shelve.open(config['database'])
	for file in db:
		print file + ": " + str(db[file])
