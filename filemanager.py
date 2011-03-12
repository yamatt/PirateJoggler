import sys
import os
import hashlib
import re
from simplekeydb import SimpleKeyDB
from optparse import OptionParser

class FileManager:
	def __init__ (self, base_path, db_file):
		self.db = SimpleKeyDB(db_file)
		self.base_path = base_path

	def add_file (self, path):
		self.db.add_key(os.path.basename(path), self.get_file_info(path))

	def add_files (self, paths):
		fileInfo = {}
		for path in paths:
			self.db.add_key(os.path.basename(path), self.get_file_info(path), False)
		self.db.save()

	def get_file_info (self, path):
		return self.db.get_key (path)

	def get_files_info (self, paths):
		returnFiles = {}
		for path in paths:
			returnFiles[path] = self.get_file_info(path)
		return returnFiles

	# get files in a directory
	def get_directory_files (self, path, recursive=True):
		returnFiles = []
		db = self.db.dump()

		for id in db:
			if recursive:
				if db[id]['directory'][:len(path)] == path:
					returnFiles.append(db[id])
			else:
				if db[id]['directory'] == path:
					returnFiles.append(db[id])
		return returnFiles

	# get subdirectories
	def get_directory_folders (self, path, recursive=True):
		returnFolders = []
		db = self.db.dump()

		if recursive:
			regex_path = re.compile("^" + path + "/")
		else:
			regex_path = re.compile("^" + path + "/{2}")

		for id in db:
			if bool(regex_path.match(db[id]['directory'])):
				if db[id]['directory'] not in returnFolders:
					returnFolders.append(db[id]['directory'])
		return returnFolders

	def delete_file (self, path):
		self.db.delete_key(path)

	def delete_directory (self, path):
		files = self.get_directory (path)
		self.db.delete_keys (files.keys())

	def get_directory_info (self, path, recursive=True):
		files = self.get_directory(path, recursive)
		size = 0

		count = len(files)
		for file in files:
			size += file['size']

		return count, size

	def get_file_info (self, path):
		fullpath = os.path.join(self.base_path, path)
		fileInfo = { \
			'file_name': os.path.basename(path), \
			'directory': os.path.dirname(path), \
			'created': os.path.getctime(fullpath), \
			'size': os.path.getsize(fullpath), \
			'safe': False, \
			'sha1': self.get_file_sha1 (fullpath), \
			'md5': self.get_file_md5 (fullpath) \
		}

		return fileInfo

	def get_file_sha1 (self, fullpath):
		file = open(fullpath, 'rb')
		sha1 = hashlib.sha1()
		sha1.update(file.read())
		file.close()
		return sha1.hexdigest()

	def get_file_md5 (self, fullpath):
		file = open(fullpath, 'rb')
		md5 = hashlib.md5()
		md5.update(file.read())
		file.close()
		return md5.hexdigest()

	def is_file (self, path):
		db = self.db.dump()
		return path in db

	def is_directory (self, path):
		db = self.db.dump()
		for file in db:
			if file['directory'] == path:
				return True
		return False

	def safe_path (self, path):
		r = re.compile('\.+[\\\/]+')
		return bool(r.search(path))

if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-d", "--dbfile", dest="db_file", help="Path to database file.")
	parser.add_option("-b", "--basepath", dest="base_path", help="Directory the module works from.")
	(options, args) = parser.parse_args()
