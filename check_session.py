import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()

# Vérifier table sessions
cursor.execute("SHOW TABLES LIKE 'django_session'")
result = cursor.fetchone()
print('Table django_session existe:', result is not None)

if result:
    cursor.execute('SELECT COUNT(*) FROM django_session')
    print('Sessions en base:', cursor.fetchone()[0])

# Vérifier les migrations appliquées
cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]
print('\nTables existantes:', tables)
