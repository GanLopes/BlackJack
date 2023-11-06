import requests
import oracledb


def separador():
    print('-' * 30)

# Função para obter uma conexão com o banco de dados Oracle
def obter_conexao():
    try:
        connection = oracledb.connect(user="RM99585", password="210305", dsn="oracle.fiap.com.br/orcl")
        return connection
    except Exception as e:
        print(f"Erro ao obter conexão: {e}")
        return None

# Função para fechar a conexão com o banco de dados
def close_connection(conn, cursor):
    try:
        if conn:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Erro ao fechar conexão: {e}")


# Função para criar a tabela de jogadores 
def criar_tabela_jogadores():
    conn = obter_conexao()
    cursor = conn.cursor()

    try:
        # Consulta SQL para verificar se a tabela já existe
        cursor.execute("SELECT count(*) FROM user_tables WHERE table_name = 'JOGADORES'")
        tabela_existe = cursor.fetchone()

        if not tabela_existe or tabela_existe[0] == 0:
            cursor.execute('''
            CREATE TABLE jogadores (
                id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                nome VARCHAR2(50),
                senha VARCHAR2(50),
                saldo NUMBER
            )
            ''')
            conn.commit()
            print("Tabela 'jogadores' criada com sucesso.")
        else:
            print("A tabela 'jogadores' já existe.")
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")

    close_connection(conn, cursor)


# Função para registrar um novo jogador
def menu():
    print(''' 
====================================
        BEM VINDO AO BLACK JACK
====================================
''')
    opcao = int(input("Escolha uma opção:\n1 - Login\n2 - Registrar\n3 - Ranking de Jogadores\n4 - Sair\nOpção: "))
    return opcao

# Função principal para jogar o jogo de Blackjack
def jogar_blackjack():
    nome_jogador = None
    saldo_jogador = None

    while True:
        try:
            opcao = menu()
            
            if opcao == 1:
                nome_jogador, saldo_jogador = fazer_login()
                if nome_jogador:
                    print(f"Bem-vindo, {nome_jogador}!")
                    break
            elif opcao == 2:
                nome = input("Nome de usuário: ")
                senha = input("Senha: ")
                registrar_jogador(nome, senha)
                print("Jogador registrado com sucesso!")
            elif opcao == 3:
                separador()
                exibir_podio()
                separador()
            elif opcao == 4:
                print("Já vai? Volte mais vezes!")
                exit()
            else:
                print("Opção inválida. Escolha novamente.")
        except Exception as e:
            print(f"Insira uma das respostas sugeridas")

    while True:  # Loop para permitir que o jogador continue jogando
        try:
            jogar_rodada(nome_jogador, saldo_jogador)
        except Exception as e:
            print(f"Erro ao jogar a rodada: {e}")

        # Verifique se o jogador ainda tem saldo
        if saldo_jogador <= 0:
            recarregar = input("Você ficou sem fichas! Deseja recarregar fichas (R) ou sair (S)? ").upper()
            if recarregar == 'R':
                saldo_jogador = 100  
            elif recarregar == 'S':
                print("Já vai? Volte mais vezes!")
                exit()
            else:
                print("Comando inválido. Escolha R para recarregar fichas ou S para sair.")

# Função para registrar um novo jogador no banco de dados
def registrar_jogador(nome, senha):
    conn = obter_conexao()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO jogadores (nome, senha, saldo) VALUES (:1, :2, :3)', (nome, senha, 100))
    except Exception as e:
        print(f"Erro ao registrar jogador: {e}")

    close_connection(conn, cursor)

# Função para fazer login de um jogador existente
def fazer_login():
    nome = input("Nome de usuário: ")
    senha = input("Senha: ")

    conn = obter_conexao()
    cursor = conn.cursor()

    cursor.execute('SELECT nome, saldo FROM jogadores WHERE nome = :1 AND senha = :2', (nome, senha))
    resultado = cursor.fetchone()

    close_connection(conn, cursor)

    if resultado:
        return resultado[0], resultado[1]
    else:
        print("Nome de usuário ou senha incorretos.")
        separador()
        return None, None

# Função para atualizar o saldo do jogador no banco de dados
def atualizar_saldo(nome, novo_saldo):
    conn = obter_conexao()
    cursor = conn.cursor()

    try:
        cursor.execute('UPDATE jogadores SET saldo = :novo_saldo WHERE nome = :nome', novo_saldo=novo_saldo, nome=nome)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao atualizar saldo")

# Resto do código do jogo

# Função para criar um novo baralho de cartas usando uma API
def criar_baralho():
    response = requests.get("https://deckofcardsapi.com/api/deck/new/shuffle/?deck_count=1")
    deck_data = response.json()
    deck_id = deck_data["deck_id"]
    return deck_id

# Função para sortear cartas do baralho
def sortear_cartas(deck_id, quantidade):
    response = requests.get(f"https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count={quantidade}")
    cards_data = response.json()
    return cards_data["cards"]

# Função para calcular o valor total de uma mão de cartas no Blackjack
def calcular_valor_mao(mao):
    valor = 0
    as_contagem = 0

    for carta in mao:
        if carta["value"] in ["KING", "QUEEN", "JACK"]:
            valor += 10
        elif carta["value"] == "ACE":
            valor += 11
            as_contagem += 1
        else:
            valor += int(carta["value"])

    while as_contagem > 0 and valor > 21:
        valor -= 10
        as_contagem -= 1

    return valor

# Função para determinar o vencedor de uma rodada de Blackjack
def determinar_vencedor(mao_jogador, mao_dealer):
    valor_jogador = calcular_valor_mao(mao_jogador)
    valor_dealer = calcular_valor_mao(mao_dealer)

    if valor_jogador > 21:
        return "Maquina"  
    elif valor_dealer > 21:
        return "Jogador"  
    elif valor_jogador > valor_dealer or valor_jogador == 21:
        return "Jogador" 
    elif valor_dealer > valor_jogador or valor_dealer == 21:
        return "Maquina"  
    else:
        return "Empate"  

# Função para que o jogador faça uma aposta
def fazer_aposta(saldo):
    while True:
        try:
            aposta = int(input(f'Seu saldo atual é {saldo}. Quanto você deseja apostar? '))
            if 0 < aposta <= saldo:
                return aposta
            else:
                print("Aposta inválida. O valor deve estar entre 1 e o seu saldo atual.")
        except ValueError:
            print("Digite um valor numérico válido.")

# Função para mostrar as cartas de uma mão
def mostrar_mao(mao, jogador):
    print(f"Cartas do {jogador}:")
    for carta in mao:
        valor = carta["value"]
        if valor in ["KING", "QUEEN", "JACK"]:
            valor = "10"
        elif valor == "ACE":
            if sum([11 if c["value"] == "ACE" else int(c["value"]) if c["value"].isnumeric() else 10 for c in mao]) <= 21:
                valor = "11"
            else:
                valor = "1"
        print(f'{valor} ({carta["value"]}) de {carta["suit"]}')
    separador()

# Função para mostrar o valor total de uma mão
def mostrar_valor(mao, jogador):
    valor = calcular_valor_mao(mao)
    print(f"Valor da mão do {jogador}: {valor}")
    separador()

# Função para o funcionamento da rodada 
def jogar_rodada(nome_jogador, saldo_jogador):
    while saldo_jogador > 0:
        continuar_jogando = input("Iniciar rodada (S/N): ")
        if continuar_jogando.upper() != 'S':
            separador()
            print("Já vai? Volte mais vezes!")
            separador()
            exibir_podio()
            separador()
            exit()
        aposta = fazer_aposta(saldo_jogador)
        saldo_jogador -= aposta

        deck_id = criar_baralho()

        cartas_do_jogador = sortear_cartas(deck_id, 2)
        cartas_do_dealer = sortear_cartas(deck_id, 2)

        mostrar_mao(cartas_do_jogador, "Jogador")
        separador()
        mostrar_mao(cartas_do_dealer, "Maquina")
        separador()
        mostrar_valor(cartas_do_jogador, "Jogador")
        separador()
        while True: 
            escolha = input("Deseja (+) mais cartas ou (-)? ").lower()

            if escolha == "+":
                nova_carta = sortear_cartas(deck_id, 1)[0]
                cartas_do_jogador.append(nova_carta)
                mostrar_mao([nova_carta], "Jogador")
                mostrar_valor(cartas_do_jogador, "Jogador")

                if calcular_valor_mao(cartas_do_jogador) > 21:
                    print("Jogador estourou com mais de 21 pontos!")
                    resultado = "Maquina"
                    break
            elif escolha == "-":
                while calcular_valor_mao(cartas_do_dealer) < 16:
                    nova_carta = sortear_cartas(deck_id, 1)[0]
                    cartas_do_dealer.append(nova_carta)

                resultado = determinar_vencedor(cartas_do_jogador, cartas_do_dealer)
                break
            else:
                print("Escolha inválida. Digite 'pedir' para pedir mais cartas ou 'parar' para parar.")

        mostrar_mao(cartas_do_dealer, "Maquina")

        if resultado == "Jogador":
            saldo_jogador += 2 * aposta
            print(f"Jogador vence! Saldo atual: {saldo_jogador}")
        elif resultado == "Empate":
            saldo_jogador += aposta
            print(f"Empate! Saldo atual: {saldo_jogador}")
        else:
            print(f"Maquina vence! Saldo atual: {saldo_jogador}")
        separador()

        if saldo_jogador == 0:
            print("Você ficou sem fichas. O jogo está encerrado.")
            separador()
            exibir_podio()
            separador
            exit()
        
        atualizar_saldo(nome_jogador, saldo_jogador)

# Função para obter os 3 melhores jogadores (pódio) do banco de dados
def obter_podio():
    conn = oracledb.connect(user="RM99585", password="210305", dsn="oracle.fiap.com.br/orcl")
    cursor = conn.cursor()

    # Recupere os jogadores com os maiores saldos em ordem decrescente
    cursor.execute('SELECT nome, saldo FROM jogadores ORDER BY saldo DESC')

    # Obtenha os 3 melhores jogadores
    top_jogadores = cursor.fetchmany(3)

    conn.close()

    return top_jogadores

# Função para exibir o pódio dos melhores jogadores
def exibir_podio():
    top_jogadores = obter_podio()

    if top_jogadores:
        print("Pódio dos Melhores Jogadores:")
        for i, (nome, saldo) in enumerate(top_jogadores, start=1):
            print(f"{i}. {nome}: Saldo - {saldo}")
    else:
        print("Nenhum jogador encontrado no pódio.")

if __name__ == "__main__":
    criar_tabela_jogadores()
    jogar_blackjack()
