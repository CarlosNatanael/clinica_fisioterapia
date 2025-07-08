from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3

app = Flask (__name__)


# --- Configuração do Banco de Dados ---

DATABASE = 'clinica.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Rotas da Aplicação ---

pacientes = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    nome = request.form['nome']
    data_nascimento = request.form['data_nascimento']
    email = request.form['email']
    telefone = request.form['telefone']
    endereco = request.form['endereco']
    plano_saude = request.form['plano_saude']

    db = get_db()
    db.execute(
        'INSERT INTO pacientes (nome, data_nascimento, email, telefone, endereco, plano_saude) VALUES (?, ?, ?, ?, ?, ?)',
        (nome, data_nascimento, email, telefone, endereco, plano_saude)
    )
    db.commit()
    return redirect(url_for('listar_pacientes'))

@app.route('/pacientes')
def listar_pacientes():
    db = get_db()
    cursor = db.execute('SELECT * FROM pacientes ORDER BY nome')
    pacientes = cursor.fetchall()
    return render_template('pacientes.html', pacientes=pacientes)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_paciente(id):
    db = get_db()
    
    if request.method == 'POST':
        # Processa a atualização dos dados
        nome = request.form['nome']
        data_nascimento = request.form['data_nascimento']
        email = request.form['email']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        plano_saude = request.form['plano_saude']
        
        db.execute(
            'UPDATE pacientes SET nome = ?, data_nascimento = ?, email = ?, telefone = ?, endereco = ?, plano_saude = ? WHERE id = ?',
            (nome, data_nascimento, email, telefone, endereco, plano_saude, id)
        )
        db.commit()
        return redirect(url_for('listar_pacientes'))

    # Se o método for GET, exibe o formulário preenchido
    cursor = db.execute('SELECT * FROM pacientes WHERE id = ?', (id,))
    paciente = cursor.fetchone()
    
    if paciente is None:
        # Se não encontrar o paciente, pode redirecionar ou mostrar erro 404
        return redirect(url_for('listar_pacientes'))
        
    return render_template('editar_paciente.html', paciente=paciente)

@app.route('/deletar/<int:id>', methods=['POST'])
def deletar_paciente(id):
    db = get_db()
    db.execute('DELETE FROM pacientes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('listar_pacientes'))

if __name__ == '__main__':
    app.run(port=5000, host="0.0.0.0", debug=True)