from flask import Flask, render_template, request, redirect, url_for, g, jsonify
from datetime import datetime, date, timedelta
import sqlite3
import sys
import os

# --- Bloco de código CORRIGIDO para resolver os caminhos ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Aponta para as pastas corretas, usando a função que criamos
template_folder = resource_path('templates')
static_folder = resource_path('static')

app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# --- Context Processor para injetar o ano atual em todos os templates ---
@app.context_processor
def inject_year():
    """Injeta o ano atual em todos os templates para o rodapé."""
    return {'current_year': datetime.now().year}

DATABASE = 'clinica.db'

# --- Configuração do Banco de Dados ---

def init_db():
    db = get_db()
    # Executa o script de criação de tabelas
    with app.open_resource('init_db.py', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

# Esta função será chamada para inicializar o DB
@app.cli.command('init-db')
def init_db_command():
    """Limpa os dados existentes e cria novas tabelas."""
    init_db()
    print('Banco de dados inicializado.')

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

# --- Filtro customizado para formatar moeda (BRL) ---
@app.template_filter('brl')
def format_currency(value):
    if value is None:
        value = 0.0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Filtro customizado para formatar data e hora (DD/MM/YYYY às HH:MM) ---
@app.template_filter('format_datetime')
def format_datetime_filter(value):
    if value:
        try:
            # Converte a string (YYYY-MM-DDTHH:MM) para um objeto datetime
            dt_obj = datetime.fromisoformat(value)
            # Formata para o padrão brasileiro
            return dt_obj.strftime('%d/%m/%Y às %H:%M')
        except ValueError:
            return value
    return ''

# --- Filtro customizado para formatar data (DD/MM/YYYY) ---
@app.template_filter('format_date')
def format_date_filter(value):
    if value:
        try:
            # Converte a string de data (YYYY-MM-DD) para um objeto de data
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            # Formata para o padrão brasileiro
            return date_obj.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return value
    return ''

# --- ROTAS PRINCIPAIS E DASHBOARD ---
@app.route('/')
def home():
    db = get_db()
    total_pacientes = db.execute('SELECT COUNT(id) FROM pacientes').fetchone()[0] or 0
    mes_atual = date.today().strftime('%Y-%m')
    novos_pacientes_mes = db.execute("SELECT COUNT(id) FROM pacientes WHERE strftime('%Y-%m', data_cadastro) = ?", (mes_atual,)).fetchone()[0] or 0
    agora = datetime.now().strftime('%Y-%m-%dT%H:%M')
    proximos_agendamentos = db.execute("""
        SELECT a.data_hora, p.nome as paciente_nome FROM agendamentos a 
        JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.data_hora >= ? ORDER BY a.data_hora ASC LIMIT 5
    """, (agora,)).fetchall()
    agendamentos_formatados = [dict(ag, data_hora_formatada=datetime.fromisoformat(ag['data_hora']).strftime('%d/%m às %H:%M')) for ag in proximos_agendamentos]
    return render_template('home.html', total_pacientes=total_pacientes, novos_pacientes_mes=novos_pacientes_mes, proximos_agendamentos=agendamentos_formatados)

# --- ROTAS DE PACIENTES ---
@app.route('/pacientes')
def listar_pacientes():
    db = get_db()
    search_query = request.args.get('q', '')
    
    base_query = 'SELECT p.*, pl.nome as plano_nome, pl.numero_sessoes FROM pacientes p LEFT JOIN planos pl ON p.plano_id = pl.id'
    
    if search_query:
        pacientes_rows = db.execute(f"{base_query} WHERE p.nome LIKE ? ORDER BY p.nome", ('%' + search_query + '%',)).fetchall()
    else:
        pacientes_rows = db.execute(f"{base_query} ORDER BY p.nome").fetchall()

    # --- NOVA LÓGICA PARA O ALERTA ---
    pacientes_com_alerta = []
    for paciente in pacientes_rows:
        paciente_dict = dict(paciente) # Converte a linha do DB para um dicionário
        paciente_dict['alerta_sessoes'] = False # Define o padrão como falso

        # Verifica se o paciente tem um plano com número de sessões definido
        if paciente_dict['plano_id'] and paciente_dict['numero_sessoes']:
            sessoes_realizadas_row = db.execute(
                'SELECT COUNT(id) FROM sessoes WHERE paciente_id = ?', 
                (paciente_dict['id'],)
            ).fetchone()
            sessoes_realizadas = sessoes_realizadas_row[0] if sessoes_realizadas_row else 0
            
            total_sessoes_plano = paciente_dict['numero_sessoes']
            sessoes_restantes = total_sessoes_plano - sessoes_realizadas

            # A Regra: Alerta se faltarem 2 ou menos sessões (e o plano não estiver concluído)
            if 0 <= sessoes_restantes <= 2 and sessoes_realizadas < total_sessoes_plano:
                paciente_dict['alerta_sessoes'] = True
        
        pacientes_com_alerta.append(paciente_dict)
    # --- FIM DA NOVA LÓGICA ---

    return render_template('pacientes.html', pacientes=pacientes_com_alerta, search_query=search_query)

@app.route('/cadastrar-paciente', methods=['GET', 'POST'])
def cadastrar_paciente():
    db = get_db()
    if request.method == 'POST':
        plano_id = request.form.get('plano_id')
        if not plano_id:
            plano_id = None
        db.execute('INSERT INTO pacientes (nome, data_nascimento, email, telefone, endereco, plano_id) VALUES (?, ?, ?, ?, ?, ?)',
                   (request.form['nome'], request.form['data_nascimento'], request.form['email'], request.form['telefone'], request.form['endereco'], plano_id))
        db.commit()
        return redirect(url_for('listar_pacientes'))
    
    planos = db.execute('SELECT * FROM planos ORDER BY nome').fetchall()
    return render_template('index.html', planos=planos)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    db = get_db()
    if request.method == 'POST':
        plano_id = request.form.get('plano_id')
        if not plano_id:
            plano_id = None
        db.execute('UPDATE pacientes SET nome=?, data_nascimento=?, email=?, telefone=?, endereco=?, plano_id=? WHERE id = ?',
                   (request.form['nome'], request.form['data_nascimento'], request.form['email'], request.form['telefone'], request.form['endereco'], plano_id, id))
        db.commit()
        return redirect(url_for('listar_pacientes'))

    paciente = db.execute('SELECT * FROM pacientes WHERE id = ?', (id,)).fetchone()
    planos = db.execute('SELECT * FROM planos ORDER BY nome').fetchall()
    return render_template('editar_paciente.html', paciente=paciente, planos=planos)

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar_paciente(id):
    db = get_db()
    db.execute('DELETE FROM pacientes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('listar_pacientes'))

@app.route('/paciente/<int:id>')
def ver_paciente(id):
    db = get_db()
    paciente_query = "SELECT p.*, pl.nome as plano_nome, pl.numero_sessoes, pl.valor_total FROM pacientes p LEFT JOIN planos pl ON p.plano_id = pl.id WHERE p.id = ?"
    paciente = db.execute(paciente_query, (id,)).fetchone()
    if not paciente:
        return "Paciente não encontrado", 404
    
    sessoes = db.execute("SELECT * FROM sessoes WHERE paciente_id = ? AND status_pagamento != 'Pago (Adiantado)' ORDER BY data_sessao DESC", (id,)).fetchall()

    # --- LÓGICA FINANCEIRA ---
    pagamentos_em_sessao = db.execute("SELECT SUM(valor) FROM sessoes WHERE paciente_id = ? AND status_pagamento LIKE 'Pago%'", (id,)).fetchone()[0] or 0.0
    pagamentos_avulsos = db.execute("SELECT SUM(valor) FROM pagamentos WHERE paciente_id = ?", (id,)).fetchone()[0] or 0.0
    total_pago = pagamentos_em_sessao + pagamentos_avulsos
    
    valor_plano = paciente['valor_total'] or 0.0
    pendente = valor_plano - total_pago

    # --- LÓGICA DE HISTÓRICO ATUALIZADA ---
    agora = datetime.now().strftime('%Y-%m-%dT%H:%M')
    agendamentos_futuros = db.execute("SELECT * FROM agendamentos WHERE paciente_id = ? AND data_hora >= ? AND status = 'Marcado' ORDER BY data_hora ASC", (id, agora)).fetchall()
    historico_pagamentos = db.execute("SELECT * FROM pagamentos WHERE paciente_id = ? ORDER BY data_pagamento DESC", (id,)).fetchall()

    return render_template('paciente_detail.html', 
                           paciente=paciente, 
                           sessoes=sessoes, 
                           total_pago=total_pago, 
                           pendente=pendente,
                           agendamentos=agendamentos_futuros,
                           historico_pagamentos=historico_pagamentos)

@app.route('/agendamento/realizado/<int:agendamento_id>', methods=['POST'])
def marcar_agendamento_realizado(agendamento_id):
    db = get_db()
    
    # Primeiro, busca o paciente_id para poder redirecionar de volta
    paciente_id = db.execute('SELECT paciente_id FROM agendamentos WHERE id = ?', (agendamento_id,)).fetchone()['paciente_id']
    
    if paciente_id:
        # Atualiza o status do agendamento para 'Realizado'
        db.execute("UPDATE agendamentos SET status = 'Realizado' WHERE id = ?", (agendamento_id,))
        db.commit()
        return redirect(url_for('ver_paciente', id=paciente_id))
    
    # Se algo der errado, redireciona para a home
    return redirect(url_for('home'))

@app.route('/paciente/<int:id>/relatorio')
def relatorio_paciente(id):
    db = get_db()
    paciente_query = "SELECT p.*, pl.nome as plano_nome, pl.numero_sessoes, pl.valor_total FROM pacientes p LEFT JOIN planos pl ON p.plano_id = pl.id WHERE p.id = ?"
    paciente = db.execute(paciente_query, (id,)).fetchone()
    if not paciente:
        return "Paciente não encontrado", 404
    sessoes = db.execute('SELECT * FROM sessoes WHERE paciente_id = ? ORDER BY data_sessao ASC', (id,)).fetchall()
    total_pago = db.execute("SELECT SUM(valor) FROM sessoes WHERE paciente_id = ? AND status_pagamento LIKE 'Pago%'", (id,)).fetchone()[0] or 0.0
    return render_template('relatorio_paciente.html', paciente=paciente, sessoes=sessoes, total_pago=total_pago)

# --- ROTA PARA FINALIZAR SESSÃO E CONECTAR COM AGENDAMENTO ---
@app.route('/finalizar-sessao/<int:agendamento_id>', methods=['GET', 'POST'])
def finalizar_sessao(agendamento_id):
    db = get_db()
    
    agendamento_info = db.execute("""
        SELECT a.id, a.data_hora, p.id as paciente_id, p.nome
        FROM agendamentos a JOIN pacientes p ON a.paciente_id = p.id
        WHERE a.id = ?
    """, (agendamento_id,)).fetchone()

    if not agendamento_info:
        return "Agendamento não encontrado", 404
    paciente_id = agendamento_info['paciente_id']
    if request.method == 'POST':
        valor_pago = request.form.get('valor')
        if not valor_pago:
            valor_pago = None
        else:
            valor_pago = float(valor_pago)
            
        db.execute('INSERT INTO sessoes (paciente_id, data_sessao, anotacoes, valor, status_pagamento) VALUES (?, ?, ?, ?, ?)',
                   (paciente_id, request.form['data_sessao'], request.form['anotacoes'], valor_pago, request.form['status_pagamento']))
        db.execute("UPDATE agendamentos SET status = 'Realizado' WHERE id = ?", (agendamento_id,))
        db.commit()

        return redirect(url_for('ver_paciente', id=paciente_id))

    # --- CÁLCULO FINANCEIRO ---

    pagamentos_em_sessao = db.execute("SELECT SUM(valor) FROM sessoes WHERE paciente_id = ? AND status_pagamento LIKE 'Pago%'", (paciente_id,)).fetchone()[0] or 0.0

    pagamentos_avulsos = db.execute("SELECT SUM(valor) FROM pagamentos WHERE paciente_id = ?", (paciente_id,)).fetchone()[0] or 0.0

    total_pago = pagamentos_em_sessao + pagamentos_avulsos

    plano_valor = db.execute("SELECT pl.valor_total FROM pacientes p JOIN planos pl ON p.plano_id = pl.id WHERE p.id = ?", (paciente_id,)).fetchone()
    valor_total_plano = plano_valor['valor_total'] if plano_valor else 0.0
    pendente = valor_total_plano - total_pago

    agendamento_dict = dict(agendamento_info)
    agendamento_dict['data_hora'] = agendamento_info['data_hora'] 

    return render_template('finalizar_sessao.html', 
                           agendamento=agendamento_dict, 
                           paciente={'id': paciente_id, 'nome': agendamento_info['nome']},
                           pendente=pendente)

# --- ROTA PARA ADICIONAR PAGAMENTO AVULSO ---
@app.route('/paciente/<int:paciente_id>/pagar', methods=['POST'])
def adicionar_pagamento_avulso(paciente_id):
    db = get_db()
    valor_pago = request.form.get('valor')
    
    if valor_pago:
        # Insere na nova tabela 'pagamentos'
        db.execute("""
            INSERT INTO pagamentos (paciente_id, data_pagamento, valor, anotacoes) 
            VALUES (?, ?, ?, ?)
        """, (
            paciente_id,
            date.today().strftime('%Y-%m-%d'),
            float(valor_pago),
            'Pagamento avulso/adiantado.'
        ))
        db.commit()
        
    return redirect(url_for('ver_paciente', id=paciente_id))

@app.route('/sessao/deletar/<int:id>', methods=['POST'])
def deletar_sessao(id):
    db = get_db()
    sessao = db.execute('SELECT paciente_id FROM sessoes WHERE id = ?', (id,)).fetchone()
    if sessao:
        db.execute('DELETE FROM sessoes WHERE id = ?', (id,))
        db.commit()
        return redirect(url_for('ver_paciente', id=sessao['paciente_id']))
    return redirect(url_for('home'))

# --- ROTAS FINANCEIRAS ---
@app.route('/ganhos')
def ganhos():
    db = get_db()
    
    ganho_sessoes = db.execute("SELECT SUM(valor) FROM sessoes WHERE status_pagamento LIKE 'Pago%'").fetchone()[0] or 0.0
    ganho_avulsos = db.execute("SELECT SUM(valor) FROM pagamentos").fetchone()[0] or 0.0
    ganho_total = ganho_sessoes + ganho_avulsos

    mes_atual = date.today().strftime('%Y-%m')
    ganho_mes_sessoes = db.execute("SELECT SUM(valor) FROM sessoes WHERE status_pagamento LIKE 'Pago%' AND strftime('%Y-%m', data_sessao) = ?", (mes_atual,)).fetchone()[0] or 0.0
    ganho_mes_avulsos = db.execute("SELECT SUM(valor) FROM pagamentos WHERE strftime('%Y-%m', data_pagamento) = ?", (mes_atual,)).fetchone()[0] or 0.0
    ganho_mes = ganho_mes_sessoes + ganho_mes_avulsos

    total_planos = db.execute("SELECT SUM(pl.valor_total) FROM pacientes p JOIN planos pl ON p.plano_id = pl.id").fetchone()[0] or 0.0
    total_pendente = total_planos - ganho_total

    pagamentos_sessoes = db.execute("""
        SELECT s.data_sessao as data, p.nome as paciente_nome, s.valor, 'Pagamento em Sessão' as tipo
        FROM sessoes s JOIN pacientes p ON s.paciente_id = p.id
        WHERE s.status_pagamento LIKE 'Pago%' AND s.valor IS NOT NULL
    """).fetchall()

    pagamentos_avulsos_hist = db.execute("""
        SELECT pg.data_pagamento as data, p.nome as paciente_nome, pg.valor, pg.anotacoes as tipo
        FROM pagamentos pg JOIN pacientes p ON pg.paciente_id = p.id
    """).fetchall()
    
    historico_pagamentos = [dict(p) for p in pagamentos_sessoes] + [dict(p) for p in pagamentos_avulsos_hist]
    
    try:
        historico_pagamentos.sort(key=lambda x: datetime.strptime(x['data'], '%Y-%m-%d'), reverse=True)
    except (ValueError, TypeError):
        pass

    return render_template('ganhos.html', 
                           ganho_total=ganho_total, 
                           ganho_mes=ganho_mes, 
                           total_pendente=total_pendente,
                           historico=historico_pagamentos)

# --- ROTAS DE AGENDAMENTO E CALENDÁRIO ---
@app.route('/agendamentos')
def ver_agendamentos():
    db = get_db()
    query = "SELECT a.id, a.data_hora, a.status, p.id as paciente_id, p.nome as paciente_nome FROM agendamentos a JOIN pacientes p ON a.paciente_id = p.id ORDER BY a.data_hora"
    agendamentos = db.execute(query).fetchall()
    agendamentos_formatados = [dict(ag, data_hora_formatada=datetime.fromisoformat(ag['data_hora']).strftime('%d/%m/%Y às %H:%M')) for ag in agendamentos]
    return render_template('agendamentos.html', agendamentos=agendamentos_formatados)

@app.route('/agendar', methods=['GET', 'POST'])
def agendar_consulta():
    db = get_db()
    if request.method == 'POST':
        db.execute('INSERT INTO agendamentos (paciente_id, data_hora, status) VALUES (?, ?, ?)', (request.form['paciente_id'], request.form['data_hora'], 'Marcado'))
        db.commit()
        return redirect(url_for('ver_agendamentos'))
    pacientes = db.execute('SELECT id, nome FROM pacientes ORDER BY nome').fetchall()
    return render_template('agendar.html', pacientes=pacientes)

@app.route('/agendamento/atualizar_status/<int:id>', methods=['POST'])
def atualizar_status_agendamento(id):
    db = get_db()
    db.execute('UPDATE agendamentos SET status = ? WHERE id = ?', (request.form['status'], id))
    db.commit()
    return redirect(url_for('ver_agendamentos'))


# --- ROTA DE AGENDAMENTO RECORRENTE ---
@app.route('/agendamento-recorrente', methods=['GET', 'POST'])
def agendamento_recorrente():
    db = get_db()
    
    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        dias_semana_str = request.form.getlist('dias_semana')
        hora_inicio = request.form['hora_inicio']
        data_inicio_str = request.form['data_inicio']
        
        if not dias_semana_str:
            # Adicionar uma mensagem de erro se nenhum dia for selecionado
            return "Erro: Nenhum dia da semana foi selecionado.", 400

        dias_semana_int = [int(dia) for dia in dias_semana_str]
        
        plano = db.execute(
            'SELECT pl.numero_sessoes FROM pacientes p JOIN planos pl ON p.plano_id = pl.id WHERE p.id = ?',
            (paciente_id,)
        ).fetchone()
        
        if not plano:
            return "Erro: Paciente não tem um plano válido.", 400
            
        sessoes_a_agendar = plano['numero_sessoes']
        sessoes_agendadas = 0
        data_atual = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        
        while sessoes_agendadas < sessoes_a_agendar:
            if data_atual.weekday() in dias_semana_int:
                # Cria a data e hora completa do agendamento
                data_hora_agendamento = datetime.combine(
                    data_atual.date(), 
                    datetime.strptime(hora_inicio, '%H:%M').time()
                )
                
                # Insere no banco de dados
                db.execute('INSERT INTO agendamentos (paciente_id, data_hora, status) VALUES (?, ?, ?)', 
                           (paciente_id, data_hora_agendamento.strftime('%Y-%m-%dT%H:%M'), 'Marcado'))
                
                sessoes_agendadas += 1
            
            # Avança para o próximo dia
            data_atual += timedelta(days=1)
            
        db.commit()
        return redirect(url_for('ver_agendamentos'))

    # Lógica para o GET (carregar o formulário)
    pacientes_com_plano = db.execute("""
        SELECT p.id, p.nome, pl.nome as plano_nome, pl.numero_sessoes 
        FROM pacientes p 
        JOIN planos pl ON p.plano_id = pl.id 
        ORDER BY p.nome
    """).fetchall()
    return render_template('agendamento_recorrente.html', pacientes=pacientes_com_plano)

# --- ROTAS DE API PARA O CALENDÁRIO ---

@app.route('/calendario')
def calendario():
    return render_template('calendario.html')

@app.route('/api/agendamentos')
def api_agendamentos():
    db = get_db()
    query = "SELECT a.id as id, a.data_hora as start, p.nome as title, p.id as paciente_id, a.status FROM agendamentos a JOIN pacientes p ON a.paciente_id = p.id"
    eventos = db.execute(query).fetchall()
    eventos_formatados = []
    for evento in eventos:
        evento_dict = dict(evento)
        evento_dict['url'] = url_for('ver_paciente', id=evento['paciente_id'])
        if evento['status'] == 'Realizado':
            evento_dict['color'] = "#10D020" 
        elif evento['status'] == 'Cancelado':
            evento_dict['color'] = "#e90909"
        else: # Marcado
            evento_dict['color'] = "#D8C7C3"
        eventos_formatados.append(evento_dict)
    return jsonify(eventos_formatados)

@app.route('/api/agendamento/mover', methods=['POST'])
def api_mover_agendamento():
    dados = request.json
    novo_inicio = dados.get('start')
    agendamento_id = dados.get('id')
    if not novo_inicio or not agendamento_id:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400
    try:
        db = get_db()
        db.execute('UPDATE agendamentos SET data_hora = ? WHERE id = ?', (novo_inicio, agendamento_id))
        db.commit()
        return jsonify({'status': 'sucesso', 'mensagem': 'Agendamento atualizado.'})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': 'Falha ao atualizar o banco de dados.'}), 500

# --- ROTA PLANOS ----
@app.route('/planos')
def ver_planos():
    db = get_db()
    planos = db.execute('SELECT * FROM planos ORDER BY valor_total').fetchall()
    return render_template('planos.html', planos=planos)

# --- ROTA DE GERENCIAMENTO DE PLANOS ---
@app.route('/gerenciar-planos')
def gerenciar_planos():
    db = get_db()
    planos = db.execute('SELECT * FROM planos ORDER BY nome').fetchall()
    return render_template('gerenciar_planos.html', planos=planos)

@app.route('/plano/adicionar', methods=['GET', 'POST'])
def adicionar_plano():
    if request.method == 'POST':
        db = get_db()
        db.execute('INSERT INTO planos (nome, numero_sessoes, valor_total, descricao) VALUES (?, ?, ?, ?)',
                   (request.form['nome'], request.form['numero_sessoes'], request.form['valor_total'], request.form['descricao']))
        db.commit()
        return redirect(url_for('gerenciar_planos'))
    return render_template('form_plano.html')

@app.route('/plano/editar/<int:id>', methods=['GET', 'POST'])
def editar_plano(id):
    db = get_db()
    if request.method == 'POST':
        db.execute('UPDATE planos SET nome=?, numero_sessoes=?, valor_total=?, descricao=? WHERE id=?',
                   (request.form['nome'], request.form['numero_sessoes'], request.form['valor_total'], request.form['descricao'], id))
        db.commit()
        return redirect(url_for('gerenciar_planos'))
    
    plano = db.execute('SELECT * FROM planos WHERE id = ?', (id,)).fetchone()
    return render_template('form_plano.html', plano=plano)

@app.route('/plano/deletar/<int:id>', methods=['POST'])
def deletar_plano(id):
    db = get_db()
    # Opcional: Verificar se o plano não está em uso antes de deletar
    db.execute('DELETE FROM planos WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('gerenciar_planos'))


# --- ROTA DE SUPORTE ---
@app.route('/suporte')
def suporte():
    return render_template('suporte.html')