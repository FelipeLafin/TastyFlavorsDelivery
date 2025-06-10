import sqlite3
from datetime import datetime
from colorist import ColorRGB
import re

import time
class DB:

    def __init__(self, entregavel):
        self.entregavel = entregavel
        self.connection = sqlite3.connect(entregavel)
        self.__atualizar_tabelas()
    def __str__(self):
        return str(self)
    def __atualizar_tabelas(self):
        cur = self.connection.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS restaurante (
            id_restaurante INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_do_restaurante TEXT NOT NULL,
            comissao_restaurante INTEGER NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL,
            ultimo_login DATETIME
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            comissao INTEGER NOT NULL,
            id_restaurante INTEGER NOT NULL,
            FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_restaurante)
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL,
            ultimo_login DATETIME
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
            id_restaurante INTEGER NOT NULL,
            nome_cliente INTEGER NOT NULL,
            nome_produto TEXT NOT NULL,
            total REAL NOT NULL,
            acoes TEXT,
            status TEXT NOT NULL,
            quantidade_itens INTEGER NOT NULL,
            data_pedido DATETIME NOT NULL,
            FOREIGN KEY (quantidade_itens) REFERENCES carrinho(quantidade),
            FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_restaurante),
            FOREIGN KEY (nome_cliente) REFERENCES clientes(nome_completo)
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_restaurante INTEGER,
            nome_do_restaurante TEXT NOT NULL,
            nome_do_produto TEXT NOT NULL,
            valor REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            data_hora DATETIME,
            total REAL,
            FOREIGN KEY (id_restaurante) REFERENCES restaurante(id_restaurante),
            FOREIGN KEY (id_usuario) REFERENCES clientes(id_usuario),
            FOREIGN KEY (nome_do_produto, valor, quantidade) REFERENCES carrinho(nome_do_produto, valor, quantidade)
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS carrinho (
            id_cliente INTEGER,
            id_produto INTEGER NOT NULL,
            nome_do_produto TEXT NOT NULL,
            valor REAL NOT NULL,
            quantidade INTEGER NOT NULL,
            FOREIGN KEY (id_cliente) REFERENCES clientes(id_usuario)
        );
        ''')

        self.connection.commit()
        self.percentual_atual = 0

    # -----------------------------------------------------------------------------------------
    #         Métodos relacionados ao cliente e a manipulação de seu Banco de Dados
    # -----------------------------------------------------------------------------------------

    def get_cliente(self, email):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM clientes WHERE email = ?''', (email,))
        record = cur.fetchone()
        if record is None:
            return None
        cliente_logado = Usuario_cliente(id_usuario=record[0], nome_completo=record[1], email=record[2],
                                         senha=record[3], ultimo_login=record[4])
        return cliente_logado

    def delete_account(self, email: str):
        cur = self.connection.cursor()
        cur.execute('''DELETE FROM restaurante WHERE email = ?''', (email,))
        self.connection.commit()

    def ja_existe_email_ou_nao_cliente(self, email):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM clientes WHERE email = ?''', (email,))
        emails_existentes = cur.fetchone()
        if emails_existentes is None:
            return None
        else:
            return True

    def ja_existe_nome_completo_ou_nao(self, nome_completo):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM clientes WHERE nome_completo = ?''', (nome_completo,))
        existe_nome_ou_nao = cur.fetchone()
        if existe_nome_ou_nao is None:
            return None
        else:
            return True

    def buscar_ultimo_login_cliente(self, email):
        cur = self.connection.cursor()
        cur.execute('''SELECT ultimo_login FROM clientes WHERE email = ?''', (email,))
        ultimo_login_cliente = cur.fetchone()
        if ultimo_login_cliente:
            return ultimo_login_cliente[0]
        return None

    def cadastrar_novo_cliente(self, cliente: Usuario_cliente):
        cur = self.connection.cursor()
        cur.execute(
            '''INSERT INTO clientes (nome_completo, email, senha, ultimo_login) VALUES (?, ?, ?, ?)''',
            (cliente.nome_completo, cliente.email, cliente.senha, cliente.ultimo_login))
        self.connection.commit()

    def login_cliente(self, email, senha):
        consulta = 'SELECT email, senha FROM clientes WHERE email = ? AND senha = ?'
        logado = self.connection.execute(consulta, (email, senha))
        if logado.fetchone() is None:
            return False
        else:
            self.update_ultimo_login_cliente(email, datetime.now())
            return True

    def update_ultimo_login_cliente(self, email, ultimo_login):
        cur = self.connection.cursor()
        cur.execute('''UPDATE clientes SET ultimo_login = ? WHERE email = ?''', (ultimo_login, email))
        self.connection.commit()

    def listar_restaurantes(self):
        Utils.clear_screen()
        cur = self.connection.cursor()
        # Busca o restaurante com a maior comissão
        cur.execute('''SELECT * FROM restaurante ORDER BY comissao_restaurante DESC LIMIT 1''')
        primeiro = cur.fetchone()  # Usa fetchone() para pegar apenas um resultado
        self.connection.commit()
        cur = self.connection.cursor()
        # Busca todos os restaurantes, ordenando pela comissao
        cur.execute('''SELECT * FROM restaurante ORDER BY comissao_restaurante DESC''')
        restaurantes = cur.fetchall()
        self.connection.commit()
        # Configuração para exibição
        ouro = " 🌟🏆"
        lista_restaurantes = []
        # Exibindo o restaurante com a maior comissão
        if primeiro:
            top = Restaurante(id_restaurante=primeiro[0], nome_do_restaurante=primeiro[1],
                              comissao_restaurante=primeiro[2], email=None, senha=None, ultimo_login=None)
            restaurante1 = f"{top.nome_do_restaurante}{ouro}"
            lista_restaurantes.append(restaurante1)
            print(" ")
            print(" " + ("_" * 47) + " ")
            print(f"¦ {'TOP 1 : ':<5} {restaurante1:<35}¦")
            print("¦" + ("_" * 5) + "_" + ("_" * 41) + "¦")
            print(f"¦{' ID ':<5}¦{' Restaurantes ':<41}¦")
            print("¦" + ("-" * 5) + "¦" + ("-" * 41) + "¦")

        # Exibindo os outros restaurantes ordenados da maior comissao para a menor (OBS: tentei ao maximo arrumar a ordem dos IDS sem afetar o banco, mas n consegui)
        for restaurante in restaurantes:
            rest = Restaurante(id_restaurante=restaurante[0], nome_do_restaurante=restaurante[1],
                               comissao_restaurante=restaurante[2], email=None, senha=None, ultimo_login=None)
            lista_restaurantes.append(rest)
            if rest.comissao_restaurante == top.comissao_restaurante:
                top_rest = f"{rest.nome_do_restaurante}{ouro}"
                print(f"¦ {rest.id_restaurante:<3} ¦ {top_rest: <38}¦")
            else:
                print(f"¦ {rest.id_restaurante:<3} ¦ {rest.nome_do_restaurante:<39} ¦")

            print("¦" + ("_" * 5) + "¦" + ("_" * 41) + "¦")
        if len(lista_restaurantes) == 0:
            return False
        return lista_restaurantes

    def obter_itens_carrinho(self, usuario: Usuario_cliente):
        cur = self.connection.cursor()
        cur.execute('''SELECT id_produto, nome_do_produto, valor, quantidade FROM carrinho''', (usuario.id_usuario,))
        itens = cur.fetchall()
        cur.close()
        return itens

    def buscar_nome_restaurante(self, id_restaurante):
        cur = self.connection.cursor()
        cur.execute('''SELECT nome_do_restaurante FROM restaurante WHERE id_restaurante = ?''', (id_restaurante,))
        nome_do_restaurante = cur.fetchone()
        if nome_do_restaurante:
            return nome_do_restaurante[0]  # Retorna o nome do restaurante
        return None  # Retorna None se não encontrar

    def listar_produtos_ID(self, id_restaurante):
        cur = self.connection.cursor()
        cur.execute('''SELECT id_produto, nome, preco FROM produtos WHERE id_restaurante = ?''', (id_restaurante,))
        produtos = cur.fetchall()
        if not produtos:
            print("Este restaurante não possui produtos cadastrados🫤.")
            resposta_valida = False
            resposta = input('\nPressione "Enter/Return" para continuar: ')
            while resposta_valida == False:
                if resposta == '':
                    resposta_valida = True
                    return  # retorna ao menu principal
                else:
                    resposta = input('Pressione "Enter/Return" para continuar: ')
            return []
        else:
            print("")
            print(" " + ("_" * 77) + " ")
            print(f"¦{' ID ':<5}¦{' Nome ':<40}¦{' Preço ':<30}¦")
            print("¦" + ("-" * 5) + "¦" + ("-" * 40) + "¦" + ("-" * 30) + "¦")
        produtos_lista = []
        for produto in produtos:
            produtos_lista.append(produto)
            print(f"¦ {produto[0]:<3} ¦ {produto[1]:<38} ¦ R${produto[2]:<26.2f} ¦")

        print("¦" + ("_" * 5) + "¦" + ("_" * 40) + "¦" + ("_" * 30) + "¦")
        return produtos_lista

    def busca_id(self, acesso):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM restaurante WHERE id_restaurante = ?''', (acesso,))
        busca_id = cur.fetchone()
        if busca_id:
            return busca_id[0]  # Retorna o ID do restaurante
        return busca_id

    def consultar_produto_por_id(self, id_produto):
        cur = self.connection.cursor()
        try:
            cur.execute('''SELECT * FROM produtos WHERE id_produto = ?''', (id_produto,))
            return cur.fetchone()
        except ValueError:
            print(f"Erro ao consultar produto")
            return None
        finally:
            cur.close()

    def adicionar_ou_atualizar_item(self, id_produto, nome_do_produto, valor, usuario: Usuario_cliente):
        cur = self.connection.cursor()
        quantidade = int(input("Digite a quantidade desejada ou 0 para remover todos os itens do carrinho: "))

        if quantidade == 0:
            # Remove o item do carrinho se a quantidade for zero
            cur.execute('DELETE FROM carrinho WHERE id_produto = ? AND id_cliente = ?',
                        (id_produto, usuario.id_usuario))
            print(f"Produto com ID {id_produto} removido do carrinho.")
        elif quantidade > 0:
            # Verifica se o item já existe no carrinho
            cur.execute('SELECT quantidade FROM carrinho WHERE id_produto = ? AND id_cliente = ?',
                        (id_produto, usuario.id_usuario))
            qtd_atualizada = cur.fetchone()
            if qtd_atualizada:
                # Atualiza a quantidade do produto existente no carrinho
                nova_quantidade = qtd_atualizada[0] + quantidade  # Incrementa a quantidade existente
                cur.execute('UPDATE carrinho SET quantidade = ? WHERE id_produto = ? AND id_cliente = ?',
                            (nova_quantidade, id_produto, usuario.id_usuario))
                print("Quantidade do produto atualizada com sucesso!")
                time.sleep(1.5)
                return True
            else:
                # Adiciona o produto ao carrinho se não existir
                cur.execute(
                    'INSERT INTO carrinho (id_cliente, id_produto, nome_do_produto, valor, quantidade) VALUES (?, ?, ?, ?, ?)',
                    (usuario.id_usuario, id_produto, nome_do_produto, valor, quantidade))
                print("Produto adicionado com sucesso!")
                time.sleep(1.5)
                return True
        else:
            print("Digite uma quantidade válida.")
        self.connection.commit()

    def resetar_itens(self):
        cur = self.connection.cursor()
        try:
            cur.execute('''DELETE FROM carrinho''')
            self.connection.commit()
            print("Todos os itens foram removidos do carrinho.")
            time.sleep(1.5)
        except sqlite3.Error as e:
            print(f"Erro ao resetar o carrinho: {e}")
            time.sleep(1.5)
        finally:
            cur.close()

    def buscar_usuario(self, id_usuario):
        cur = self.connection.cursor()
        try:
            cur.execute(
                '''SELECT id_usuario, nome_completo, email, senha, ultimo_login FROM clientes WHERE id_usuario = ?''',
                (id_usuario,))
            resultado = cur.fetchone()
            if resultado:
                id_usuario, nome_completo, email, senha, ultimo_login = resultado
                return Usuario_cliente(id_usuario, nome_completo, email, senha, ultimo_login)
            else:
                return None
        finally:
            cur.close()

    def listar_total(self, usuario: Usuario_cliente):
        cur = self.connection.cursor()
        cur.execute('''SELECT SUM(valor * quantidade) FROM carrinho''', (usuario.id_usuario,))
        total = cur.fetchone()
        cur.close()
        return total

    def listar_itens(self, usuario: Usuario_cliente):
        cur = self.connection.cursor()
        cur.execute(
            '''SELECT id_cliente, id_produto, nome_do_produto, valor, quantidade FROM carrinho WHERE id_cliente = ?''',
            (usuario.id_usuario,))
        itens = cur.fetchall()
        totalP = 0
        print("")
        if not itens:
            print("Nenhum item no carrinho")
            return 0
        else:
            print("Itens no carrinho:")
            print("." + ("-" * 83) + ".")
            for item in itens:
                id_cliente, id_produto, nome_do_produto, valor, quantidade = item
                totalP1 = quantidade * valor
                totalP += totalP1
                if valor >= 10:
                    print(
                        f"| Item: {nome_do_produto:<20} | ID: {id_produto: <3} | Quantidade: {quantidade:<13} | Preço: R${valor:<2.2f} |")
                else:
                    print(
                        f"| Item: {nome_do_produto:<20} | ID: {id_produto: <3} | Quantidade: {quantidade:<13} | Preço: R${valor:<5.2f} |")

            print("|" + ("-" * 83) + "|")
            print(f"| Total: R${totalP:<72.2f} |")
            print("'" + ("_" * 83) + "'")
        return totalP

    def pedido_concluido(self, usuario: Usuario_cliente, nome_do_restaurante, id_restaurante):
        Utils.clear_screen()
        cur = self.connection.cursor()
        try:
            cur.execute(
                '''SELECT id_cliente, id_produto, nome_do_produto, valor, quantidade FROM carrinho WHERE id_cliente = ?''',
                (usuario.id_usuario,))
            itens = cur.fetchall()
            totalP = 0
            print("")
            if not itens:
                print("Nenhum item no carrinho")
                return 0
            else:
                print("> Pedido Concluído <\n")
                contornoRGB = ColorRGB(255, 255, 0)
                vermelho = ColorRGB(255, 0, 0)
                Ciano = ColorRGB(0, 255, 255)
                verde = ColorRGB(8, 229, 0)

                canto_colorido = f"{contornoRGB}¦{contornoRGB.OFF}"
                linha_colorida = f"{contornoRGB}_{contornoRGB.OFF}"
                canto = f"{contornoRGB}'{contornoRGB.OFF}"
                separador = f"{contornoRGB}-{contornoRGB.OFF}"
                ID = f"{vermelho}{' ID ':<5}{vermelho.OFF}"
                Nome = f"{Ciano}{' Produto ':<40}{Ciano.OFF}"
                QTD = f"{' Quantidade ':<30}"
                Preco = f"{verde}{' Preço ':<31}{verde.OFF}"

                print(" " + (linha_colorida * 109) + " ")
                print(
                    f"{canto_colorido}{ID}{canto_colorido}{Nome}{canto_colorido}{QTD}{canto_colorido}{Preco}{canto_colorido}")
                print(f"{canto_colorido}" + (separador * 5) + f"{canto_colorido}" + (
                            separador * 40) + f"{canto_colorido}" + (separador * 30) + f"{canto_colorido}" + (
                                  separador * 31) + f"{canto_colorido}")

                for item in itens:
                    id_cliente, id_produto, nome_do_produto, valor, quantidade = item
                    totalP1 = quantidade * valor
                    totalP += totalP1
                    novo_totalP = float(totalP)
                    formata = "{0:2f}"
                    total_formatado = formata.format(novo_totalP)
                    linha = f"{canto_colorido} {id_produto:<3} {canto_colorido} {nome_do_produto:<38} {canto_colorido} R${valor:<26.2f} {canto_colorido} {quantidade:<29} {canto_colorido}"
                    print(linha)
                if totalP == 0:
                    print("Não há itens no carrinho para concluir o pedido.")
                    return
                print(
                    canto_colorido + (linha_colorida * 5) + canto_colorido + (linha_colorida * 40) + canto_colorido + (
                                linha_colorida * 30) + canto_colorido + (linha_colorida * 31) + canto_colorido)
                print(f"{canto_colorido} Valor total da compra: R${totalP:<82.2f} {canto_colorido}")
                print(f"{canto}" + (linha_colorida * 109) + f"{canto}")

            data_hora = datetime.now()
            for item in itens:
                _, id_produto, nome_do_produto, valor, quantidade = item
                cur.execute('''INSERT INTO compras (id_usuario, id_restaurante, nome_do_restaurante, nome_do_produto, valor, quantidade, data_hora, total)VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',(usuario.id_usuario, id_restaurante, nome_do_restaurante, nome_do_produto, valor, quantidade,data_hora, totalP))
                status = "CRIADO"
                quantidade_itens = quantidade
                cur.execute('''INSERT INTO pedidos (nome_cliente, nome_produto, total, status, quantidade_itens, data_pedido, id_restaurante) VALUES(?, ?, ?, ?, ?, ?, ?)''',(usuario.nome_completo, nome_do_produto, total_formatado, status, quantidade_itens, data_hora, id_restaurante))
                cur.execute('''DELETE FROM carrinho WHERE id_cliente = ?''', (usuario.id_usuario,))
            self.connection.commit()

            # Exibir compras anteriores com o nome do restaurante
            print("\nCompras anteriores:\n")
            cur.execute(
                '''SELECT r.nome_do_restaurante, c.data_hora, c.nome_do_produto, c.valor, c.quantidade
                   FROM compras c 
                   LEFT JOIN restaurante r ON c.id_restaurante = r.id_restaurante
                   WHERE c.id_usuario = ? 
                   ORDER BY c.data_hora DESC''',
                (usuario.id_usuario,))
            compras_anteriores = cur.fetchall()
            if compras_anteriores:

                for nome_restaurante, data_hora, nome_do_produto, valor, quantidade in compras_anteriores:
                    print(
                        f"\nRestaurante: {nome_restaurante}, Data/Hora: {data_hora}, Produto: {nome_do_produto}, Valor: R${valor:.2f}, Quantidade: {quantidade}")
            else:
                print("Nenhuma compra anterior registrada.")

            resposta = input('\nPressione "Enter/Return" para continuar: ')
            while True:
                if resposta == '':
                    break
                else:
                    resposta = input('Pressione "Enter/Return" para continuar: ')

        finally:
            cur.close()

    # -------------------------------------------------------------------------------------------
    #         Métodos relacionados ao restaurante e a manipulação de seu Banco de Dados
    # -------------------------------------------------------------------------------------------


    def get_user(self, email: str):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM restaurante WHERE email = ?''', (email,))
        record = cur.fetchone()
        if record is None:
            return None
        login_usuario = Restaurante(id_restaurante=record[0], nome_do_restaurante=record[1],
                                    comissao_restaurante=record[2], email=record[3], senha=record[4],
                                    ultimo_login=record[5])
        return login_usuario

    def delete_user(self, email: str):
        cur = self.connection.cursor()
        cur.execute('''DELETE FROM restaurante WHERE email = ?''', (email,))
        self.connection.commit()

    def cadastrar_novo_restaurante(self, usuario: Restaurante):
        cur = self.connection.cursor()
        cur.execute(
            '''INSERT INTO restaurante (nome_do_restaurante, comissao_restaurante, email, senha, ultimo_login) VALUES (?, ?, ?, ?, ?)''',
            (usuario.nome_do_restaurante, usuario.comissao_restaurante, usuario.email, usuario.senha,
             usuario.ultimo_login))
        self.connection.commit()

    def buscar_ultimo_login_restaurante(self, email):
        cur = self.connection.cursor()
        cur.execute('''SELECT ultimo_login FROM restaurante WHERE email = ?''', (email,))
        ultimo_login = cur.fetchone()
        if ultimo_login:
            return ultimo_login[0]
        return None

    def update_ultimo_login_restaurante(self, email, ultimo_login):
        cur = self.connection.cursor()
        cur.execute('''UPDATE restaurante SET ultimo_login = ? WHERE email = ?''', (ultimo_login, email))
        self.connection.commit()

    def login_restaurante(self, email, senha):
        cur = self.connection.cursor()
        consulta = 'SELECT email, senha FROM restaurante WHERE email = ? AND senha = ?'
        logado = cur.execute(consulta, (email, senha))
        resultado = logado.fetchone()
        if resultado is None:
            return False
        else:
            self.update_ultimo_login_restaurante(email, datetime.now())
            return True
    def consultando_restaurantes_existentes(self, email, senha):
        consultando_restaurantes_no_banco = 'SELECT * FROM restaurante WHERE email= ? AND senha = ?'
        restaurantes_existentes = self.connection.execute(consultando_restaurantes_no_banco, (email, senha))
        return restaurantes_existentes.fetchone()

    def ja_existe_email_ou_nao_restaurante(self, email):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM restaurante WHERE email = ?''', (email,))
        emails_existentes = cur.fetchone()
        if emails_existentes is None:
            return None
        else:
            return True

    def ja_existe_restaurante_ou_nao(self, nome_do_restaurante):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM restaurante WHERE nome_do_restaurante = ?''', (nome_do_restaurante,))
        existe_restaurante_ou_nao = cur.fetchone()
        if existe_restaurante_ou_nao is None:
            return None
        else:
            return True

    def cadastrar_novo_produto(self, produto: Produto):
        cur = self.connection.cursor()
        cur.execute(
            ''' INSERT INTO produtos (nome, preco, quantidade, comissao, id_restaurante) VALUES (?, ?, ?, ?, ?) ''',
            (produto.nome, produto.preco, produto.quantidade, produto.comissao, produto.id_restaurante))
        self.connection.commit()

    def verificar_se_tem_produto(self, nome):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM produtos WHERE nome = ?''', (nome,))
        id_produto = cur.fetchone()
        if id_produto is None:
            print(f"Produto '{nome}' adicionado com sucesso!")
            return None
        else:
            print(f"O produto '{nome}' já está cadastrado.")
            return id_produto

    def deletar_produto(self, id_produto):
        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM produtos WHERE id_produto = ?''', (id_produto,))
        produto = cur.fetchone()
        if produto:
            cur.execute('''DELETE FROM produtos WHERE id_produto = ?''', (id_produto,))
            self.connection.commit()
            print(f"Produto com ID {id_produto} apagado com sucesso! ✅")
            time.sleep(1)
        else:
            print(f"Produto com ID {id_produto} não encontrado ❌")
            time.sleep(1)
        cur.close()

    def listar_produtos(self, usuario_restaurante: Restaurante):

        # Deixei a tabela mais elegante usando cores RGB (Arthur me falou q era possível colocar então eu fui atrás)
        contornoRGB = ColorRGB(255, 255, 0)
        vermelho = ColorRGB(255, 0, 0)
        Ciano = ColorRGB(0, 255, 255)
        verde = ColorRGB(8, 229, 0)

        canto_colorido = f"{contornoRGB}¦{contornoRGB.OFF}"
        linha_colorida = f"{contornoRGB}_{contornoRGB.OFF}"
        separador = f"{contornoRGB}-{contornoRGB.OFF}"
        ID = f"{vermelho}{' ID ':<5}{vermelho.OFF}"
        Nome = f"{Ciano}{' Nome ':<40}{Ciano.OFF}"
        Preco = f"{verde}{' Preco ':<30}{verde.OFF}"
        QTD = f"{' QTD ':<31}"

        cur = self.connection.cursor()
        cur.execute('''SELECT * FROM produtos WHERE id_restaurante = ?''', (usuario_restaurante.id_restaurante,))
        produtos = cur.fetchall()

        if not produtos:
            print("Nenhum produto cadastrado.")
            return []
        Utils.clear_screen()
        print("\n> Lista de Produtos <")
        print(" " + (linha_colorida * 109) + " ")
        print(f"{canto_colorido}{ID}{canto_colorido}{Nome}{canto_colorido}{Preco}{canto_colorido}{QTD}{canto_colorido}")
        print(f"{canto_colorido}" + (separador * 5) + f"{canto_colorido}" + (separador * 40) + f"{canto_colorido}" + (
                    separador * 30) + f"{canto_colorido}" + (separador * 31) + f"{canto_colorido}")

        lista_produtos = []
        total_preco = 0
        total_quantidade = 0
        for produto in produtos:
            prod = Produto(produto[0], produto[1], preco=produto[2], quantidade=produto[3],
                           comissao=usuario_restaurante.comissao_restaurante, id_restaurante=produto[5])
            total_preco += prod.preco
            total_quantidade += prod.quantidade
            lista_produtos.append(prod)
            linha_Produtos = f"{canto_colorido} {prod.id_produto:<3} {canto_colorido} {prod.nome:<38} {canto_colorido} R${prod.preco:<26.2f} {canto_colorido} {prod.quantidade:<29} {canto_colorido}"
            print(linha_Produtos)
        print(canto_colorido + (linha_colorida * 5) + canto_colorido + (linha_colorida * 40) + canto_colorido + (
                    linha_colorida * 30) + canto_colorido + (linha_colorida * 31) + canto_colorido)
        self.connection.commit()

        cur = self.connection.cursor()
        cur.execute('''SELECT comissao_restaurante FROM restaurante WHERE id_restaurante = ?''',
                    (usuario_restaurante.id_restaurante,))
        comissao_atualmente_cadastrada = cur.fetchone()
        if comissao_atualmente_cadastrada:
            if comissao_atualmente_cadastrada[0] >= 10:
                print(
                    f"{canto_colorido} Comissão cadastrada: {comissao_atualmente_cadastrada[0]}% {" ":<19} {canto_colorido} Total: R${total_preco:<19.2f} {canto_colorido} Quantidade Total: {total_quantidade:<11} {canto_colorido}")
            else:
                print(
                    f"{canto_colorido} Comissão cadastrada: {comissao_atualmente_cadastrada[0]}% {" ":<20} {canto_colorido} Total: R${total_preco:<19.2f} {canto_colorido} Quantidade Total: {total_quantidade:<11} {canto_colorido}")
        print(f"{canto_colorido}" + (linha_colorida * 46) + f"{canto_colorido}" + (
                    linha_colorida * 30) + f"{canto_colorido}" + (linha_colorida * 31) + f"{canto_colorido}")
        return lista_produtos

    def adicionar_produto_input(self, usuario: Restaurante):
        Utils.clear_screen()
        print("> Cadastrar produto <")
        print("")

        requisitos_completos = False
        while not requisitos_completos:
            nome = input("Digite o nome do produto: ")
            while not re.search(r'[A-Za-z ]', nome):
                nome = input("Digite o nome do produto sem o acento e sem número: ")
            if len(nome) < 5:
                print("O nome do produto deve conter pelo menos 5 caracteres.")
                continue

            if not nome.replace(" ", "").isalpha():
                print("O nome do produto deve conter apenas letras e espaços (sem números ou símbolos).")
                continue

            preco_valido = False
            while preco_valido != True:
                preco = input("Digite o preço do produto: ")
                try:
                    preco_float = float(preco)
                    if preco_float >= 0:
                        qtd_valida = False
                        while qtd_valida != True:
                            quantidade = input("Digite a quantidade: ")
                            if quantidade.isnumeric():
                                quantidade = int(quantidade)
                                if quantidade >= 0:
                                    preco_valido = True
                                    requisitos_completos = True
                                    qtd_valida = True
                                    comissao = usuario.comissao_restaurante
                                    id_restaurante = usuario.id_restaurante
                                    self.cadastrar_novo_produto(
                                        Produto(None, nome, preco_float, quantidade, comissao, id_restaurante))
                                else:
                                    print("A quantidade deve ser maior ou igual a zero")
                            else:
                                print("Informe um numero positivo e inteiro")
                    else:
                        print("O preço do produto deve ser maior que zero.")
                except ValueError:
                    print("Por favor, insira um valor numérico válido para o preço.")

    def maior_comissao_atual(self):
        cur = self.connection.cursor()
        maior_comissao_ordenada = 'SELECT comissao_restaurante FROM restaurante ORDER BY comissao_restaurante DESC LIMIT 1'
        cur.execute(maior_comissao_ordenada)
        maior_comissao_atual = cur.fetchone()
        if maior_comissao_atual is None:
            print("")
            return 0
        else:
            return maior_comissao_atual[0]

    def consultando_comissoes_existentes(self, comissao):
        cur = self.connection.cursor()
        cur.execute('''SELECT comissao_restaurante FROM restaurante WHERE comissao_restaurante= ?''', (comissao,))
        comissoes_existentes = cur.fetchone()
        return comissoes_existentes

    def comissao_alterada(self, nova_comissao, id_restaurante):
        cur = self.connection.cursor()
        cur.execute('''UPDATE restaurante SET comissao_restaurante = ? WHERE id_restaurante = ?''',
                    (nova_comissao, id_restaurante))
        self.connection.commit()
        return True

    def alterar_comissao(self, usuario: Restaurante):
        while True:
            Utils.clear_screen()
            print("> Alterar comissão <")
            print("")
            cur = self.connection.cursor()
            cur.execute('''SELECT comissao_restaurante FROM restaurante WHERE id_restaurante = ?''',
                        (usuario.id_restaurante,))
            comissao_atualmente_cadastrada = cur.fetchone()

            if comissao_atualmente_cadastrada:
                print(f"Comissão atual do restaurante é: {comissao_atualmente_cadastrada[0]}%")
                nova_comissao = input(
                    'Digite a nova comissão em número inteiro seguido de "%", maior ou igual a zero (ex: 10%): ')

                if nova_comissao.endswith('%'):
                    try:
                        comissao = int(nova_comissao[:-1])  # Remover o '%' e converter para inteiro
                        if 0 <= comissao <= 100:
                            if self.comissao_alterada(comissao, usuario.id_restaurante):
                                print(f"Comissão foi atualizada para {comissao}%!")
                                time.sleep(2)
                                break
                        else:
                            print("\nErro! A comissão deve estar entre 0% e 100%.")
                            time.sleep(1)
                    except ValueError:
                        print("\nErro! Insira um número inteiro válido seguido de '%'.")
                        time.sleep(1)
                else:
                    print("\nErro! O valor deve terminar com '%' e não pode conter letras!")
                    time.sleep(2)