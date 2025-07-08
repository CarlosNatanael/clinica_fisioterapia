import sqlite3

conn = sqlite3.connect('clinica.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT NOT NULL,
        endereco TEXT,
        plano_saude TEXT
    )
''')

conn.commit()
conn.close()

print("Banco de dados e tabela criados com sucesso!")