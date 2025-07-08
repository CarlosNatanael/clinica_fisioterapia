from flask import Flask, render_template, request, redirect, url_for, g, jsonify
from datetime import datetime, date
import sqlite3
import sys
import os

# --- Bloco de código para resolver os caminhos para o PyInstaller ---
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

# --- Context Processor para injetar o ano atual em todos os templates ---
@app.context_processor
def inject_year():
    """Injeta o ano atual em todos os templates para o rodapé."""
    return {'current_year': datetime.now().year}

DATABASE = 'clinica.db'

# --- Configuração do Banco de Dados ---
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
    base_query = 'SELECT p.*, pl.nome as plano_nome FROM pacientes p LEFT JOIN planos pl ON p.plano_id = pl.id'
    if search_query:
        pacientes = db.execute(f"{base_query} WHERE p.nome LIKE ? ORDER BY p.nome", ('%' + search_query + '%',)).fetchall()
    else:
        pacientes = db.execute(f"{base_query} ORDER BY p.nome").fetchall()
    return render_template('pacientes.html', pacientes=pacientes, search_query=search_query)

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
    sessoes = db.execute('SELECT * FROM sessoes WHERE paciente_id = ? ORDER BY data_sessao DESC', (id,)).fetchall()
    total_pago = db.execute("SELECT SUM(valor) FROM sessoes WHERE paciente_id = ? AND status_pagamento LIKE 'Pago%'", (id,)).fetchone()[0] or 0.0
    valor_plano = paciente['valor_total'] or 0.0
    pendente = valor_plano - total_pago
    return render_template('paciente_detail.html', paciente=paciente, sessoes=sessoes, total_pago=total_pago, pendente=pendente)

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

# --- ROTAS DE SESSÕES ---
@app.route('/sessao/adicionar', methods=['POST'])
def adicionar_sessao():
    paciente_id = request.form['paciente_id']
    valor_pago = request.form.get('valor')
    if not valor_pago:
        valor_pago = None
    else:
        valor_pago = float(valor_pago)
    db = get_db()
    db.execute('INSERT INTO sessoes (paciente_id, data_sessao, anotacoes, valor, status_pagamento) VALUES (?, ?, ?, ?, ?)',
               (paciente_id, request.form['data_sessao'], request.form['anotacoes'], valor_pago, request.form['status_pagamento']))
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
    ganho_total = db.execute("SELECT SUM(valor) FROM sessoes WHERE status_pagamento LIKE 'Pago%'").fetchone()[0] or 0.0
    mes_atual = date.today().strftime('%Y-%m')
    ganho_mes = db.execute("SELECT SUM(valor) FROM sessoes WHERE status_pagamento LIKE 'Pago%' AND strftime('%Y-%m', data_sessao) = ?", (mes_atual,)).fetchone()[0] or 0.0
    total_planos = db.execute("SELECT SUM(pl.valor_total) FROM pacientes p JOIN planos pl ON p.plano_id = pl.id").fetchone()[0] or 0.0
    total_pendente = total_planos - ganho_total
    return render_template('ganhos.html', ganho_total=ganho_total, ganho_mes=ganho_mes, total_pendente=total_pendente)

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

@app.route('/calendario')
def calendario():
    return render_template('calendario.html')

# --- ROTAS DE API PARA O CALENDÁRIO ---
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
            evento_dict['color'] = '#844C4C' 
        elif evento['status'] == 'Cancelado':
            evento_dict['color'] = '#a36d6d'
        else: # Marcado
            evento_dict['color'] = '#D1A79D'
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

# --- ROTA DE SUPORTE ---
@app.route('/suporte')
def suporte():
    return render_template('suporte.html')

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0", debug=True)