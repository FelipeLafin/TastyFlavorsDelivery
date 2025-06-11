from datetime import datetime
import re
import sqlite3
import os
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.urandom(24)

def get_db_connection():
    connection = sqlite3.connect('entregavel.db')
    connection.row_factory = sqlite3.Row
    return connection

@app.route('/')
def menu():
    return redirect('/index')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/administrativo')
def administrativo():
    conn = get_db_connection()

    # 1) Quantidade de restaurantes e clientes cadastrado no aplicativo:
    quantidade_restaurantes = conn.execute('SELECT COUNT(*) FROM restaurante').fetchone()[0]
    quantidade_clientes = conn.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]

    # 2) Consulta da quantidade de clientes únicos por restaurante:
    clientes_por_restaurante = {}
    teste = conn.execute('SELECT id_restaurante, nome_do_restaurante FROM restaurante')
    restaurantes = teste.fetchall()
    for restaurante in restaurantes:
        id_restaurante = restaurante['id_restaurante']
        nome_restaurante = restaurante['nome_do_restaurante']
        clientes_unicos = conn.execute('''
                SELECT COUNT(DISTINCT nome_cliente) 
                FROM pedidos 
                WHERE id_restaurante = ?
            ''', (id_restaurante,)).fetchone()[0]
        clientes_por_restaurante[nome_restaurante] = clientes_unicos

    # 3) Consulta do ticket médio por restaurante:
    ticket_medio_por_restaurante = {}
    for restaurante in restaurantes:
        id_restaurante = restaurante['id_restaurante']
        nome_restaurante = restaurante['nome_do_restaurante']
        ticket_medio = conn.execute('''
                SELECT AVG(total) 
                FROM pedidos 
                WHERE id_restaurante = ?
            ''', (id_restaurante,)).fetchone()[0]
        ticket_medio_por_restaurante[nome_restaurante] = ticket_medio or 0.0

    # 5) Consulta da quantidade de pedidos por mês pra cada restaurante:
    pedidos_por_mes = {}
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
             "Novembro", "Dezembro"]
    for restaurante in restaurantes:
        id_restaurante = restaurante['id_restaurante']
        pedidos_por_mes_restaurante = {}
        for x, mes in enumerate(meses):
            procurar = conn.execute('''
                    SELECT COUNT(*) 
                    FROM pedidos 
                    WHERE id_restaurante = ? 
                    AND strftime('%m', data_pedido) = ?
                ''', (id_restaurante, str(x + 1)))
            pedidos_por_mes_restaurante[mes] = procurar.fetchone()[0]
        pedidos_por_mes[restaurante['nome_do_restaurante']] = pedidos_por_mes_restaurante

    conn.close()

    return render_template(
        'administrativo.html',
        quantidade_restaurantes=quantidade_restaurantes,
        quantidade_clientes=quantidade_clientes,
        clientes_por_restaurante=clientes_por_restaurante,
        ticket_medio_por_restaurante=ticket_medio_por_restaurante,
        meses=meses,
        pedidos_por_mes=pedidos_por_mes,
    )

@app.route('/entrar', methods=['GET', 'POST'])
def entrar():
    if request.method == 'POST':
        tipo_usuario = request.form.get('tipo')
        if tipo_usuario == 'cliente':
            return redirect('/login/cliente')
        
        elif tipo_usuario == 'restaurante':
            return redirect('/login/restaurante')
        else:
            error = 'Selecione um tipo de usuário válido.'
            return render_template('selecionar_tipo_login.html', error=error)
    return render_template('selecionar_tipo_login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        tipo_usuario = request.form.get('tipo')
        if tipo_usuario == 'cliente':
            return redirect('/cadastro/cliente')
        
        elif tipo_usuario == 'restaurante':
            return redirect('/cadastro/restaurante')
        else:
            error = 'Selecione um tipo de usuário válido.'
            return render_template('selecionar_tipo_cadastro.html', error=error)
    return render_template('selecionar_tipo_cadastro.html')

@app.route('/login/cliente', methods=['GET', 'POST'])
def login_cliente():
    session.clear()
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        conn = get_db_connection()
        consulta = conn.execute('SELECT id_cliente, email, senha, nome, sobrenome FROM clientes WHERE email = ? AND senha = ?',
                                (email, senha))
        resultado = consulta.fetchone()
        conn.close()
        if resultado:
            session['nome_completo'] = f"{resultado['nome']} {resultado['sobrenome']}"
            if session['nome_completo']:
                return True
        else:
            return False
    return render_template('login_cliente.html')

@app.route('/login/restaurante', methods=['GET', 'POST'])
def login_restaurante():
    session.clear()
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        conn = get_db_connection()
        consulta = conn.execute('SELECT id_restaurante, email, senha, nome_do_restaurante FROM restaurante WHERE email = ? AND senha = ?',
                                (email, senha))
        resultado = consulta.fetchone()
        conn.close()
        if resultado:
            session['nome_do_restaurante'] = resultado['nome_do_restaurante']
            session['email_restaurante'] = resultado['email']
            if session['nome_do_restaurante']:
                return redirect('/painel')
        else:
            return False
    return render_template('login_rest.html')
        
@app.route('/cadastro/restaurante', methods=['GET', 'POST'])
def cadastro_restaurante():
    if request.method == 'POST':
        nome = request.form['nome_do_restaurante']
        email = request.form['email']
        senha = request.form['senha']

        if not email or not senha:
            error = 'Email e senha são obrigatórios.'

            return render_template('cadastro_rest.html', error=error)
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = 'Email inválido.'
            return render_template('cadastro_rest.html', error=error)
        
        if nome == '':
            error = 'Nome do restaurante é obrigatório.'
            return render_template('cadastro_rest.html', error=error)
        
        conn = get_db_connection()
        existe_nome = conn.cursor()
        existe_nome.execute('SELECT nome_do_restaurante FROM restaurante WHERE nome_do_restaurante = ?', (nome,))
        if existe_nome.fetchone():
            conn.close()
            error = 'Nome do restaurante já está em uso.'
            return render_template('cadastro_rest.html', error=error)
        else:
            ultimo_login = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO restaurante (nome_do_restaurante, email, senha, ultimo_login)
                VALUES (?, ?, ?, ?)
            ''', (nome, email, senha, ultimo_login))
            conn.commit()
            conn.close()

            return redirect('/index')
    return render_template('cadastro_rest.html')

@app.route('/cadastro/cliente', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        sobrenome = request.form['sobrenome']
        email = request.form['email']
        senha = request.form['senha']

        if not nome or not sobrenome:
            error = 'Nome e sobrenome são obrigatórios.'
            return render_template('cadastro_cliente.html', error=error)
        elif not re.match(r"^[a-zA-Z\s]+$", nome) or not re.match(r"^[a-zA-Z\s]+$", sobrenome):

            error = 'Nome e sobrenome devem conter apenas letras.'
            return render_template('cadastro_cliente.html', error=error)
        
        elif len(nome) < 3 or len(sobrenome) < 3:
            error = 'Nome e sobrenome devem ter pelo menos 3 caracteres.'
            return render_template('cadastro_cliente.html', error=error)
        
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            error = 'Email inválido.'
            return render_template('cadastro_cliente.html', error=error)
        
        elif not re.match(r"^[a-zA-Z0-9@#$%^&+=]{6,}$", senha):
            error = 'Senha deve ter pelo menos 6 caracteres e pode conter letras, números e símbolos especiais.'
            return render_template('cadastro_cliente.html', error=error)
        
        elif not email or not senha:
            error = 'Email e senha são obrigatórios.'
            return render_template('cadastro_cliente.html', error=error)
        
        else:
            ultimo_login = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            cursor = get_db_connection()
            cursor = cursor.cursor()
            cursor.execute('''
                INSERT INTO clientes (nome, sobrenome, email, senha, ultimo_login)
                VALUES (?, ?, ?, ?, ?)
                ''', (nome, sobrenome, email, senha, ultimo_login))
            cursor.commit()
            cursor.close()
            return redirect('/index')
    return render_template('cadastro_cliente.html')

@app.route('/relatorio')
def relatorio_do_dia():
    if 'id_restaurante' not in session:
        return redirect('/')

    id_restaurante = session['id_restaurante']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT nome_cliente, AVG(total) as media_gasto
        FROM pedidos WHERE id_restaurante = ?
        GROUP BY nome_cliente
    ''', (id_restaurante,))
    media_gasto = cursor.fetchall()

    cursor.execute('''
        SELECT nome_cliente, total FROM pedidos
        WHERE id_restaurante = ?
        ORDER BY total DESC LIMIT 1
    ''', (id_restaurante,))
    maior_compra = cursor.fetchone()

    cursor.execute('''
        SELECT nome_cliente, SUM(quantidade_itens) as quantidade_total
        FROM pedidos WHERE id_restaurante = ?
        GROUP BY nome_cliente
        ORDER BY quantidade_total DESC LIMIT 1
    ''', (id_restaurante,))
    maior_pedido = cursor.fetchone()

    cursor.execute('''
        SELECT MAX(comissao_restaurante) as maior_comissao, MIN(comissao_restaurante) as menor_comissao
        FROM restaurante
    ''')
    comissoes = cursor.fetchone()

    cursor.execute('''
        SELECT nome_produto, SUM(quantidade_itens) as total_vendido
        FROM pedidos WHERE id_restaurante = ?
        GROUP BY nome_produto
        ORDER BY total_vendido DESC LIMIT 1
    ''', (id_restaurante,))
    item_mais_pedido = cursor.fetchone()

    cursor.execute('''
        SELECT status, COUNT(*) as quantidade
        FROM pedidos WHERE id_restaurante = ?
        GROUP BY status
    ''', (id_restaurante,))
    pedidos_por_status = cursor.fetchall()

    cursor.execute('''
        SELECT strftime('%w', data_pedido) as dia_da_semana, COUNT(*) as quantidade
        FROM pedidos WHERE id_restaurante = ?
        GROUP BY dia_da_semana
    ''', (id_restaurante,))
    pedidos_por_dia = cursor.fetchall()

    conn.close()

    return render_template('relatorio.html', media_gasto=media_gasto,
                           maior_compra=maior_compra, maior_pedido=maior_pedido,
                           comissoes=comissoes, item_mais_pedido=item_mais_pedido,
                           pedidos_por_status=pedidos_por_status, pedidos_por_dia=pedidos_por_dia)

@app.route('/atualizar_status', methods=['POST'])
def atualizar_status():
    id_pedido = request.form['id_pedido']
    acao = request.form['acao']

    conn = get_db_connection()
    cursor = conn.cursor()

    if acao == "RECUSAR":
        cursor.execute('DELETE FROM pedidos WHERE id_pedido = ?', (id_pedido,))
    else:
        novo_status = None
        if acao == "ACEITAR":
            novo_status = "EM PREPARO"
        elif acao == "SAIU PARA ENTREGA":
            novo_status = "SAIU PARA ENTREGA"
        elif acao == "ENTREGUE":
            novo_status = "ENTREGUE"
        if novo_status:
            cursor.execute('UPDATE pedidos SET status = ? WHERE id_pedido = ?', (novo_status, id_pedido))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'nome_do_restaurante' in session:
        session.pop('nome_do_restaurante', None)
        session.pop('email_restaurante', None)
        return redirect('/')
    return render_template('index.html')


@app.route('/painel', methods=['GET', 'POST'])
def painel():
    if 'nome_do_restaurante' in session:
        conn = sqlite3.connect("entregavel.db")
        cursor = conn.cursor()

        # Buscar produtos de restaurante com destaque
        cursor.execute("""
        SELECT nome, preco, imagem
        FROM produtos
    """)
        produtos_recomendados = cursor.fetchall()
        return render_template("paginaInicial.html", recomendados=produtos_recomendados)
    return redirect('/login_rest')
    