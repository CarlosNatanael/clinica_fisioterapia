from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask (__name__)
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

# --- Rotas da Aplicação ---

@app.route('/')
def home():
    """NOVA ROTA: Exibe a página inicial/dashboard."""
    return render_template('home.html')

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

@app.route('/pacientes')
def listar_pacientes():
    """Busca e exibe a lista de todos os pacientes."""
    db = get_db()
    pacientes = db.execute('SELECT * FROM pacientes ORDER BY nome').fetchall()
    return render_template('pacientes.html', pacientes=pacientes)

@app.route('/paciente/<int:id>')
def ver_paciente(id):
    """NOVA ROTA: Exibe os detalhes de um paciente e seu histórico de sessões."""
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
    """NOVA ROTA: Adiciona uma nova anotação de sessão para um paciente."""
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
    """NOVA ROTA: Placeholder para a funcionalidade de agendamentos."""
    return render_template('agendamentos.html')


# As rotas de editar e deletar continuam as mesmas
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    # (O código desta função permanece o mesmo da versão anterior)
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
    # (O código desta função permanece o mesmo da versão anterior)
    db = get_db()
    db.execute('DELETE FROM pacientes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('listar_pacientes'))

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0", debug=True)