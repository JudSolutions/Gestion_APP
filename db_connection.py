import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="Jg1395*:",
        database="Gestion_Documental_AG"
    )
