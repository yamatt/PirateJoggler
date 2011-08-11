import sys
import os
import hashlib
import re
import base64
import mimetypes
from simplekeydb.simplekeydb import SimpleKeyDB
from optparse import OptionParser

class FileManager:
	def __init__ (self, base_path, db_file):
		self.db = SimpleKeyDB(db_file)
		self.base_path = base_path

	def add_file (self, unique_filename, file_path):
		self.db.add_key(unique_filename, self.get_file_details(os.path.join(self.base_path, unique_filename), file_path))

	def add_processed_file (self, virtual_path, details):
		self.db.add_key(virtual_path, details)

	def add_files (self, filename):
		fileInfo = {}
		for unique_filename, file_path in filenames:
			self.db.add_key(unique_filename, self.get_file_details(os.path.join(self.base_path, file_path)), False)
		self.db.save()

	def get_file_info (self, filename):
		return self.db.get_key (filename)

	def get_files_info (self, filenames):
		returnFiles = {}
		for filename in filenames:
			returnFiles[filename] = self.get_file_info(filename)
		return returnFiles

	# get files in a directory
	def get_directory_files (self, path, recursive=True):
		returnFiles = []
		db = self.db.dump()
		path = os.path.dirname(path)
		for id in db:
			if recursive:
				if db[id]['directory'].startswith(path):
					returnFiles.append(db[id])
			else:
				if db[id]['directory'] == path:
					returnFiles.append(db[id])
		return returnFiles

	# get subdirectories
	def get_directory_folders (self, path, recursive=True):
		returnFolders = []
		db = self.db.dump()
		path = os.path.dirname(path)
		for id in db:
			if recursive:
				if db[id]['directory'].startswith(path):
					if db[id]['directory'] not in returnFolders:
						returnFolders.append(db[id]['directory'])
			else:
				if db[id]['directory'].startswith(path) and not db[id]['directory'] == path:
					if db[id]['directory'] not in returnFolders:
						returnFolders.append(db[id]['directory'])
		return returnFolders

	def delete_file (self, path):
		self.db.delete_key(path)

	def delete_directory (self, path):
		files = self.get_directory (path)
		self.db.delete_keys (files.keys())

	def get_directory_details (self, path, recursive=True):
		files = self.get_directory(path, recursive)
		size = 0

		count = len(files)
		for file in files:
			size += file['size']

		return count, size

	def get_file_details (self, unique_filename, file_path):
		fullpath = os.path.join(self.base_path, unique_filename)
		fileInfo = { \
			'file_name': os.path.basename(file_path), \
			'directory': os.path.dirname(file_path), \
			'unique_name': unique_filename, \
			'path': file_path, \
			'created': os.path.getctime(fullpath), \
			'size': os.path.getsize(fullpath), \
			'safe': False, \
			'hashes': self.get_hashes(fullpath), \
			'playable': self.is_playable_file(fullpath) \
		}
		return fileInfo

	def is_playable_file(self, path):
		content = mimetypes.guess_type(path)[0]
		if content is not None:
			type = content.split('/')[0]
			if type == 'audio' or type == 'video':
				return True
		return False

	def get_hashes (self, fullpath):
		file = open(fullpath, 'rb')
		hashes = {}
		file_data = file.read()
		#sha1
		sha1 = hashlib.sha1()
		sha1.update(file_data)
		#md5
		md5 = hashlib.md5()
		md5.update(file_data)
		#sha512
		sha512 = hashlib.sha512()
		sha512.update(file_data)
		
		hashes['sha1'] = sha1.hexdigest()
		hashes['md5'] = md5.hexdigest()
		hashes['sha512'] = sha512.hexdigest()
		file.close()
		return hashes

	def is_file (self, path):
		db = self.db.dump()
		return path in db

	def is_directory (self, path):
		db = self.db.dump()
		path = os.path.dirname(path)
		for file in db:
			if db[file]['directory'] == path:
				return True
		return False

	def dir_file_conflict (self, path):
		db = self.db.dump()
		path_parts = path.split("/")
		path_walk = "/"
		for part in path_parts:
			if part:
				path_walk = os.path.join(path_walk, part)
				for file in db:
					if file == path_walk:
						return True
		return False

	def toggle_file_safe (self, path):
		fileinfo = self.db.get_key (path)
		fileinfo['safe'] = not fileinfo['safe']
		self.db.add_key(path, fileinfo)

	def safe_path (self, path):
		r = re.compile('\.\.+[\\\/]+')
		return not bool(r.search(path))

	def unique_filename (self, basename):
		unique = base64.b32encode(os.urandom(5)).lower()	#generate random code
		return ".".join([unique, basename])

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--dbfile", dest="db_file", help="Path to database file.")
	parser.add_option("-b", "--basepath", dest="base_path", help="Directory the module works from.")
	(options, args) = parser.parse_args()
