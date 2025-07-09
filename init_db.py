import sqlite3

conn = sqlite3.connect('clinica.db')
cursor = conn.cursor()

# ... (código das tabelas planos, pacientes, sessoes, agendamentos) ...
cursor.execute('''
    CREATE TABLE IF NOT EXISTS planos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        numero_sessoes INTEGER NOT NULL,
        valor_total REAL NOT NULL,
        descricao TEXT
    )
''')
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
cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_hora TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    )
''')

# --- NOVA TABELA EXCLUSIVA PARA PAGAMENTOS ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER NOT NULL,
        data_pagamento TEXT NOT NULL,
        valor REAL NOT NULL,
        anotacoes TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes (id) ON DELETE CASCADE
    )
''')

# ... (código para inserir os planos iniciais) ...
cursor.execute("SELECT COUNT(id) FROM planos")
if cursor.fetchone()[0] == 0:
    planos_iniciais = [
        ('Avaliação Inicial', 1, 130.00, 'Sessão única para avaliação completa.'),
        ('Sessão Avulsa', 1, 110.00, 'Sessão individual de fisioterapia.'),
        ('Plano Mensal - 1x/semana', 4, 400.00, 'Pacote com 4 sessões, ideal para frequência semanal.'),
        ('Plano Mensal - 2x/semana', 8, 760.00, 'Pacote com 8 sessões, ideal para frequência de duas vezes na semana.')
    ]
    cursor.executemany('INSERT INTO planos (nome, numero_sessoes, valor_total, descricao) VALUES (?, ?, ?, ?)', planos_iniciais)
    print("Planos de tratamento iniciais cadastrados.")


conn.commit()
conn.close()

print("Banco de dados e tabelas recriados com a nova estrutura financeira!")