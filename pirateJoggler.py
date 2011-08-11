import os
from flask import Flask, request, render_template, jsonify, send_file, session
#from flask import request
#from flask import render_template
from werkzeug import secure_filename
from optparse import OptionParser
from filemanager import FileManager
from subprocess import Popen
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

def split_path (path):
	path_arr = path.split("/")
	path_combined = "/"
	path_list = []
	for part in path_arr:
		if not part == "":
			path_combined = os.path.join(path_combined, part) + "/"
			path_list.append({'label': part, 'path': path_combined})
	return path_list

def play_file (path):
	Popen(config['media_player'] % path, shell=True)

### web ui ###
@app.route('/', methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def index(path=""):
	path = "/" + path.encode()
	if path.endswith('/'):
		path_walk = split_path(path)
		# the path is a directory
		if filemanager.is_directory(path):
			folders = filemanager.get_directory_folders(path, False)
			files = filemanager.get_directory_files(path, False)
			if 'info' in request.args:
				return jsonify(path=path, folders=folders, files=files)
			elif 'login' in request.args and request.args.get('login') == config['adminpassword']:
				session['admin'] = True
				return render_template('layout.html', path=path, folders=folders, files=files, message="You are logged in")
			elif 'logoff' in request.args:
				session['admin'] = False
				return render_template('layout.html', path=path, folders=folders, files=files, message="You are now logged off")
			elif 'isadmin' in request.args:
				return jsonify(is_admin=bool(session.get('admin')))
			elif 'delete' in request.args:
				pass
				# get list of files with this path
				# delete files
				# remove keys
			else:
				return render_template('layout.html', path=path_walk, folders=folders, files=files)
		elif filemanager.safe_path(path):
			return render_template('layout.html', path=path_walk, message="Path not found. If you would like to create it, upload a file."), 404
		else:
			return render_template('layout.html', path="Error", message="Illegal path"), 501
	else:
		# the path is a file
		if filemanager.is_file(path):
			file_info = filemanager.get_file_info(path)
			if 'info' in request.args:
				return jsonify(filemanager.get_file_info(path))
			elif 'play' in request.args:
				# run command to play
				file_path = os.path.join(config['files'], filemanager.get_file_info(path)['unique_name'])
				play_file(file_path)
				return jsonify(success=True)
			elif 'safe' in request.args:
				if bool(session.get('admin')):
					filemanager.toggle_file_safe(path)
					return jsonify(success=True)
				else:
					return jsonify(success=False, message="You are not authorised")
			elif 'delete' in request.args:
				if bool(session.get('admin')):
					fileinfo = filemanager.get_file(path)
					filepath = os.join(config['files'], fileinfo['unique_name'])
					print "Deleting file: " + filepath
					filemanager.delete_file(path)
					os.remove(filepath)
					return jsonify(success=True)
				else:
					return jsonify(success=False, message="You are not authorised")
			else:
				return send_file(os.path.join(config['files'], file_info['unique_name']), None, True, file_info['file_name'])
		elif filemanager.safe_path(path):
			return render_template('layout.html', message="File not found.", path=path), 404
		else:
			return render_template('layout.html', message="Invalid number of arguments"), 501

	if 'password' in request.args:
		if request.args['password'] == config['adminpassword']:
			session['admin'] = True
		
@app.route('/', methods=['POST'])
@app.route('/<path:virtual_path>', methods=['POST'])
def upload(virtual_path=""):
	file = request.files['file']
	virtual_path = "/" + virtual_path
	# has a file, it has a valid extension has a valid and safe directory path and path does not conflcit with an existing file and is not already a saved file
	if file and file_allowed(file.filename) and virtual_path.endswith('/') and filemanager.safe_path(virtual_path) and not filemanager.dir_file_conflict(virtual_path) and not filemanager.is_file(virtual_path):
		file_name = secure_filename(file.filename)
		unique_filename = filemanager.unique_filename(file_name)
		actual_file_location = os.path.join(config['files'], unique_filename)
		virtual_file_location = os.path.join(virtual_path, file_name).encode()
		print ("Saved file to: %s for path %s" % (actual_file_location, virtual_file_location))
		file.save(actual_file_location)
		filemanager.add_processed_file(virtual_file_location, filemanager.get_file_details (unique_filename, virtual_file_location))
		return jsonify(success=True, message=unique_filename)
	else:
		return jsonify(success=False, message="No file in 'file' or file extension/path is not allowed.")

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-c", "--config", dest="config_path", help="File to read configuration settings from.")
	(options, args) = parser.parse_args()
	config = load_config(options.config_path);
	filemanager = FileManager(config['files'], config['database'])
	app.secret_key = config['sessionhash']
	app.run(host='0.0.0.0', port=config['port'], debug=config['debug'])
