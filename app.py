import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g
from datetime import datetime, date

app = Flask(__name__)
DATABASE = 'clinica.db'

# --- Conexão com o Banco de Dados (sem alterações) ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Rotas da Aplicação ---

@app.route('/')
def home():
    """Dashboard com estatísticas dinâmicas."""
    db = get_db()
    
    # 1. Total de pacientes
    total_pacientes = db.execute('SELECT COUNT(id) FROM pacientes').fetchone()[0]
    
    # 2. Novos pacientes no mês atual
    mes_atual = date.today().strftime('%Y-%m')
    novos_pacientes_mes = db.execute(
        "SELECT COUNT(id) FROM pacientes WHERE strftime('%Y-%m', data_cadastro) = ?", (mes_atual,)
    ).fetchone()[0]

    # 3. Próximos 5 agendamentos
    agora = datetime.now().strftime('%Y-%m-%dT%H:%M')
    proximos_agendamentos = db.execute("""
        SELECT a.data_hora, p.nome as paciente_nome
        FROM agendamentos a
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.data_hora >= ?
        ORDER BY a.data_hora ASC
        LIMIT 5
    """, (agora,)).fetchall()
    
    agendamentos_formatados = []
    for ag in proximos_agendamentos:
        agendamento_dict = dict(ag)
        agendamento_dict['data_hora_formatada'] = datetime.fromisoformat(ag['data_hora']).strftime('%d/%m às %H:%M')
        agendamentos_formatados.append(agendamento_dict)

    return render_template(
        'home.html', 
        total_pacientes=total_pacientes, 
        novos_pacientes_mes=novos_pacientes_mes,
        proximos_agendamentos=agendamentos_formatados
    )

@app.route('/pacientes')
def listar_pacientes():
    """Lista de pacientes com funcionalidade de busca."""
    db = get_db()
    search_query = request.args.get('q', '') # Pega o termo de busca da URL, ou string vazia
    
    if search_query:
        # Se houver busca, filtra pelo nome
        pacientes = db.execute(
            "SELECT * FROM pacientes WHERE nome LIKE ? ORDER BY nome", 
            ('%' + search_query + '%',)
        ).fetchall()
    else:
        # Senão, lista todos
        pacientes = db.execute('SELECT * FROM pacientes ORDER BY nome').fetchall()
        
    return render_template('pacientes.html', pacientes=pacientes, search_query=search_query)

@app.route('/sessao/marcar_pago/<int:id>', methods=['POST'])
def marcar_sessao_paga(id):
    """NOVA ROTA: Atualiza o status de pagamento de uma sessão."""
    db = get_db()
    sessao = db.execute('SELECT paciente_id FROM sessoes WHERE id = ?', (id,)).fetchone()
    if sessao:
        db.execute("UPDATE sessoes SET status_pagamento = 'Pago' WHERE id = ?", (id,))
        db.commit()
        return redirect(url_for('ver_paciente', id=sessao['paciente_id']))
    return redirect(url_for('home'))

# (O resto do seu código de pacientes, agendamentos, etc., continua aqui, sem alterações)
@app.route('/cadastrar-paciente', methods=['GET', 'POST'])
def cadastrar_paciente():
    """Exibe e processa o formulário de cadastro de novos pacientes."""
    if request.method == 'POST':
        nome = request.form['nome']
        # ... (pegue todos os outros campos do formulário)
        endereco = request.form['endereco']
        plano_saude = request.form['plano_saude']
        
        db = get_db()
        db.execute(
            'INSERT INTO pacientes (nome, data_nascimento, email, telefone, endereco, plano_saude) VALUES (?, ?, ?, ?, ?, ?)',
            (nome, request.form['data_nascimento'], request.form['email'], request.form['telefone'], endereco, plano_saude)
        )
        db.commit()
        return redirect(url_for('listar_pacientes'))
    
    # Se for GET, apenas mostra o formulário (antiga página index.html)
    return render_template('index.html')

@app.route('/paciente/<int:id>')
def ver_paciente(id):
    """Exibe os detalhes de um paciente e seu histórico de sessões."""
    db = get_db()
    paciente = db.execute('SELECT * FROM pacientes WHERE id = ?', (id,)).fetchone()
    
    if paciente is None:
        return "Paciente não encontrado", 404
        
    sessoes = db.execute(
        'SELECT * FROM sessoes WHERE paciente_id = ? ORDER BY data_sessao DESC', (id,)
    ).fetchall()
    
    return render_template('paciente_detail.html', paciente=paciente, sessoes=sessoes)

@app.route('/paciente/<int:id>/adicionar_sessao', methods=['POST'])
def adicionar_sessao(id):
    """Adiciona uma nova anotação de sessão para um paciente."""
    data_sessao = request.form['data_sessao']
    anotacoes = request.form['anotacoes']
    
    db = get_db()
    db.execute(
        'INSERT INTO sessoes (paciente_id, data_sessao, anotacoes) VALUES (?, ?, ?)',
        (id, data_sessao, anotacoes)
    )
    db.commit()
    
    return redirect(url_for('ver_paciente', id=id))
    
@app.route('/agendamentos')
def ver_agendamentos():
    """Busca e exibe todos os agendamentos, ordenados por data."""
    db = get_db()
    # Usamos um JOIN para buscar o nome do paciente junto com os dados do agendamento
    query = """
        SELECT agendamentos.id, agendamentos.data_hora, agendamentos.status, pacientes.nome as paciente_nome
        FROM agendamentos
        JOIN pacientes ON agendamentos.paciente_id = pacientes.id
        ORDER BY agendamentos.data_hora
    """
    agendamentos = db.execute(query).fetchall()
    
    # Converte a string de data/hora para um formato mais legível
    agendamentos_formatados = []
    for ag in agendamentos:
        agendamento_dict = dict(ag) # Converte a Row para um dicionário
        # Formata a data para Dia/Mês/Ano às Horas:Minutos
        agendamento_dict['data_hora_formatada'] = datetime.fromisoformat(ag['data_hora']).strftime('%d/%m/%Y às %H:%M')
        agendamentos_formatados.append(agendamento_dict)

    return render_template('agendamentos.html', agendamentos=agendamentos_formatados)

@app.route('/agendar', methods=['GET', 'POST'])
def agendar_consulta():
    """Exibe o formulário para agendar e processa o agendamento."""
    db = get_db()

    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        data_hora = request.form['data_hora']
        status = 'Marcado' # Status inicial padrão
        
        db.execute(
            'INSERT INTO agendamentos (paciente_id, data_hora, status) VALUES (?, ?, ?)',
            (paciente_id, data_hora, status)
        )
        db.commit()
        return redirect(url_for('ver_agendamentos'))

    # Se for GET, busca todos os pacientes para preencher o <select>
    pacientes = db.execute('SELECT id, nome FROM pacientes ORDER BY nome').fetchall()
    return render_template('agendar.html', pacientes=pacientes)


@app.route('/agendamento/cancelar/<int:id>', methods=['POST'])
def cancelar_agendamento(id):
    """Cancela (deleta) um agendamento."""
    db = get_db()
    db.execute('DELETE FROM agendamentos WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('ver_agendamentos'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    db = get_db()
    if request.method == 'POST':
        db.execute(
            'UPDATE pacientes SET nome = ?, data_nascimento = ?, email = ?, telefone = ?, endereco = ?, plano_saude = ? WHERE id = ?',
            (request.form['nome'], request.form['data_nascimento'], request.form['email'], request.form['telefone'], request.form['endereco'], request.form['plano_saude'], id)
        )
        db.commit()
        return redirect(url_for('listar_pacientes'))
    paciente = db.execute('SELECT * FROM pacientes WHERE id = ?', (id,)).fetchone()
    return render_template('editar_paciente.html', paciente=paciente)

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar_paciente(id):
    db = get_db()
    db.execute('DELETE FROM pacientes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('listar_pacientes'))

@app.route('/suporte')
def suporte():
    """NOVA ROTA: Exibe a página de suporte."""
    return render_template('suporte.html')

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0", debug=True)