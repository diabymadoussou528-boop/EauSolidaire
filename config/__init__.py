"""
Initialisation du projet Django EauSolidaire.
Permet l'utilisation de PyMySQL comme pilote MySQL compatible avec Windows / WampServer
si mysqlclient n'est pas compilé pour la version courante de Python.
"""
try:
    import pymysql
    pymysql.version_info = (2, 2, 7, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
