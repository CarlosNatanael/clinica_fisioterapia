import sqlite3

conn = sqlite3.connect('clinica.db')
cursor = conn.cursor()

# --- NOVA TABELA: Planos de Tratamento ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS planos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        numero_sessoes INTEGER NOT NULL,
        valor_total REAL NOT NULL
    )
''')

# --- Tabela de Pacientes ATUALIZADA ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        data_nascimento TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT NOT NULL,
        endereco TEXT,
        plano_id INTEGER,
        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plano_id) REFERENCES planos (id)
    )
''')

# --- Tabela de Sessões ATUALIZADA ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_sessao TEXT NOT NULL,
        anotacoes TEXT NOT NULL,
        valor REAL,
        status_pagamento TEXT DEFAULT 'Pendente',
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    )
''')

# --- Tabela de Agendamentos (sem alterações) ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_hora TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    )
''')

# Inserir alguns planos padrão para começar
cursor.execute("SELECT COUNT(id) FROM planos")
if cursor.fetchone()[0] == 0:
    planos_iniciais = [
        ('Sessão Avulsa', 1, 150.00),
        ('Plano 5 Sessões', 5, 700.00),
        ('Plano 10 Sessões', 10, 1300.00),
        ('Avaliação Inicial', 1, 200.00)
    ]
    cursor.executemany('INSERT INTO planos (nome, numero_sessoes, valor_total) VALUES (?, ?, ?)', planos_iniciais)
    print("Planos de tratamento iniciais cadastrados.")

conn.commit()
conn.close()

print("Banco de dados e tabelas recriados com a nova estrutura financeira!")