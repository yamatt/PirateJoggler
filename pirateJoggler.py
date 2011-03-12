import os
from flask import Flask, request, render_template, jsonify, send_file, session
#from flask import request
#from flask import render_template
from werkzeug import secure_filename
from optparse import OptionParser
from filemanager import FileManager
try:
    import json    #python2.6
except ImportError:
    import simplejson as json #python2.5

app = Flask(__name__)

def load_config (path):
	file = open(path, 'r')
	config_data = file.read()
	return json.loads(config_data)

def file_allowed (filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in config['allowed_extensions']


### web ui ###
@app.route('/', methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def index(path="/"):
	if len(request.args) > 1:
		if filemanager.is_file(path):
			if len(request.args) == 0:
				return send_file(os.path.join(config['path'],path))
			elif len(request.args) == 1:
				if 'info' in request.args:
					return jsonify(path=path, filemanager.get_file_info(path))
				
		if filemanager.is_directory(path):
			if len(request.args) == 0:
				folders = filemanager.get_directory_folders(path, False)
				files = filemanager.get_directory_files(path, False)
				return render_template('layout.html', path=path, folders=folders, files=files)
			elif len(request.args) == 1:
				if 'info' in request.args:
					return jsonify(files=filemanager.get_directory_files, folders=filemanager.get_directory_folders)
		else:
			return render_template('layout.html', message="Path not found. If you would like to create it, upload a file."), 404
	else:
		return render_template('error.html', error="Invalid number of arguments"), 501

@app.route('/', methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def upload(path="/"):
	file = request.files['file']
	if file and file_allowed(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(config['path'], filename)) # needs to make directories
		filemanager.add_file(filename)
		return jsonify(success=True, message=filename)
	else:
		return jsonify(success=False, message="No file in 'file' or file extension is not on the approved list")

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--config", dest="config_path", help="File to read configuration settings from.")
	(options, args) = parser.parse_args()
	config = load_config(options.config_path);
	filemanager = FileManager(config['path'], config['database'])
	app.run(host='0.0.0.0', port=config['port'], debug=config['debug'])
