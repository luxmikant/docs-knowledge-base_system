# Config package

try:
	import pymysql

	pymysql.install_as_MySQLdb()
except Exception:
	# SQLite-only environments can run without PyMySQL.
	pass
