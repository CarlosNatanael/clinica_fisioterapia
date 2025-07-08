import sqlite3

conn = sqlite3.connect('clinica.db')
cursor = conn.cursor()

# Tabela de pacientes (sem alterações)
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

# NOVA TABELA para o histórico de sessões
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_sessao TEXT NOT NULL,
        anotacoes TEXT NOT NULL,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    )
''')

# Tabela placeholder para agendamentos futuros
cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_hora TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    )
''')

conn.commit()
conn.close()

print("Banco de dados e tabelas recriados com sucesso!")