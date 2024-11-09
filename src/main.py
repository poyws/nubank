import sqlite3
import random
from datetime import datetime

def conectar_bd():
    conn = sqlite3.connect("nubank_ficticio.db")
    return conn

def criar_tabelas():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS contas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        senha TEXT NOT NULL,
                        saldo REAL NOT NULL,
                        emprestimo REAL NOT NULL,
                        limite_transferencia REAL NOT NULL,
                        tentativas_login INTEGER NOT NULL
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transacoes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conta_id INTEGER,
                        tipo TEXT NOT NULL,
                        valor REAL NOT NULL,
                        data TEXT NOT NULL,
                        saldo_anterior REAL,
                        saldo_atual REAL,
                        FOREIGN KEY (conta_id) REFERENCES contas(id)
                      )''')
    conn.commit()
    conn.close()

def adicionar_conta(nome, senha, saldo_inicial=0, emprestimo=0, limite_transferencia=5000):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO contas (nome, senha, saldo, emprestimo, limite_transferencia, tentativas_login) 
                      VALUES (?, ?, ?, ?, ?, ?)''', (nome, senha, saldo_inicial, emprestimo, limite_transferencia, 3))
    conn.commit()
    conn.close()

def obter_conta(nome, senha):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM contas WHERE nome = ? AND senha = ?''', (nome, senha))
    conta = cursor.fetchone()
    conn.close()
    return conta

def registrar_transacao(conta_id, tipo, valor, saldo_anterior, saldo_atual):
    conn = conectar_bd()
    cursor = conn.cursor()
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''INSERT INTO transacoes (conta_id, tipo, valor, data, saldo_anterior, saldo_atual) 
                      VALUES (?, ?, ?, ?, ?, ?)''', (conta_id, tipo, valor, data_atual, saldo_anterior, saldo_atual))
    conn.commit()
    conn.close()

def obter_historico(conta_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''SELECT tipo, valor, data, saldo_anterior, saldo_atual FROM transacoes WHERE conta_id = ?''', (conta_id,))
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

class ContaBancaria:
    def __init__(self, id_conta, nome, saldo, emprestimo, limite_transferencia, tentativas_login):
        self.id_conta = id_conta
        self.nome = nome
        self.saldo = saldo
        self.emprestimo = emprestimo
        self.limite_transferencia = limite_transferencia
        self.tentativas_login = tentativas_login

    def depositar(self, valor):
        if valor > 0:
            saldo_anterior = self.saldo
            self.saldo += valor
            registrar_transacao(self.id_conta, 'Depósito', valor, saldo_anterior, self.saldo)
            print(f"Depósito de R${valor} realizado com sucesso!")
        else:
            print("O valor do depósito deve ser maior que zero.")

    def sacar(self, valor):
        if valor > 0 and valor <= self.saldo:
            saldo_anterior = self.saldo
            self.saldo -= valor
            registrar_transacao(self.id_conta, 'Saque', valor, saldo_anterior, self.saldo)
            print(f"Saque de R${valor} realizado com sucesso!")
        elif valor > self.saldo:
            print("Saldo insuficiente.")
        else:
            print("O valor do saque deve ser maior que zero.")

    def verificar_saldo(self):
        print(f"Saldo atual de {self.nome}: R${self.saldo}")

    def verificar_saldo_total(self):
        saldo_total = self.saldo + self.emprestimo
        print(f"Saldo total (incluindo empréstimos) de {self.nome}: R${saldo_total}")

    def transferir(self, valor, conta_destino):
        if valor > 0 and valor <= self.saldo and valor <= self.limite_transferencia:
            saldo_anterior = self.saldo
            self.saldo -= valor
            conta_destino.depositar(valor)
            registrar_transacao(self.id_conta, 'Transferência', valor, saldo_anterior, self.saldo)
            print(f"Transferência de R${valor} realizada com sucesso para {conta_destino.nome}.")
        else:
            print("Saldo insuficiente ou valor inválido para transferência.")

    def pedir_emprestimo(self, valor):
        if valor > 0 and valor <= 1000:
            juros = valor * 0.05  # juros de 5% sobre o valor do empréstimo
            valor_total = valor + juros
            saldo_anterior = self.saldo
            self.emprestimo += valor
            self.saldo += valor_total
            registrar_transacao(self.id_conta, 'Empréstimo', valor, saldo_anterior, self.saldo)
            print(f"Empréstimo de R${valor} aprovado! Juros de 5% aplicados.")
        else:
            print("Valor do empréstimo inválido ou superior ao limite.")

    def alterar_senha(self, nova_senha):
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''UPDATE contas SET senha = ? WHERE id = ?''', (nova_senha, self.id_conta))
        conn.commit()
        conn.close()
        print("Senha alterada com sucesso!")

    def mostrar_historico(self):
        transacoes = obter_historico(self.id_conta)
        print(f"Histórico de transações de {self.nome}:")
        if not transacoes:
            print("Nenhuma transação registrada.")
        for transacao in transacoes:
            print(f"{transacao[0]}: R${transacao[1]} em {transacao[2]} (Saldo anterior: R${transacao[3]}, Saldo atual: R${transacao[4]})")

def login():
    tentativas = 3
    while tentativas > 0:
        nome = input("Digite seu nome: ")
        senha = input("Digite sua senha: ")
        conta = obter_conta(nome, senha)
        if conta:
            if conta[6] <= 0:
                print("Conta bloqueada devido a tentativas excessivas de login.")
                return None
            print(f"Bem-vindo, {nome}!")
            return ContaBancaria(conta[0], conta[1], conta[3], conta[4], conta[5], conta[6])
        tentativas -= 1
        print(f"Nome ou senha incorretos. Tentativas restantes: {tentativas}")
        atualizar_tentativas(nome, conta[6] - 1 if conta else 0)
    print("Número de tentativas excedido. Conta bloqueada.")
    return None

def atualizar_tentativas(nome, tentativas_restantes):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''UPDATE contas SET tentativas_login = ? WHERE nome = ?''', (tentativas_restantes, nome))
    conn.commit()
    conn.close()

def criar_conta():
    nome = input("Digite seu nome para cadastro: ")
    senha = input("Digite sua senha para cadastro: ")
    saldo_inicial = float(input("Digite o valor do depósito inicial: R$"))
    adicionar_conta(nome, senha, int(saldo_inicial))
    print(f"Conta criada com sucesso para {nome}!")

def menu(cliente):
    while True:
        print("\nMenu:")
        print("1. Depositar")
        print("2. Sacar")
        print("3. Verificar saldo")
        print("4. Ver saldo total (incluindo empréstimos)")
        print("5. Transferir")
        print("6. Pedir empréstimo")
        print("7. Ver histórico de transações")
        print("8. Alterar senha")
        print("9. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            valor = float(input("Digite o valor a ser depositado: R$"))
            cliente.depositar(valor)
        elif opcao == "2":
            valor = float(input("Digite o valor a ser sacado: R$"))
            cliente.sacar(valor)
        elif opcao == "3":
            cliente.verificar_saldo()
        elif opcao == "4":
            cliente.verificar_saldo_total()
        elif opcao == "5":
            nome_destino = input("Digite o nome do destinatário: ")
            conta_destino = obter_conta(nome_destino, senha="")
            if conta_destino:
                conta_destino_obj = ContaBancaria(conta_destino[0], conta_destino[1], conta_destino[3], conta_destino[4], conta_destino[5], conta_destino[6])
                valor = float(input("Digite o valor a ser transferido: R$"))
                cliente.transferir(valor, conta_destino_obj)
            else:
                print("Conta de destinatário não encontrada.")
        elif opcao == "6":
            valor = float(input("Digite o valor do empréstimo: R$"))
            cliente.pedir_emprestimo(valor)
        elif opcao == "7":
            cliente.mostrar_historico()
        elif opcao == "8":
            nova_senha = input("Digite a nova senha: ")
            cliente.alterar_senha(nova_senha)
        elif opcao == "9":
            print("Saindo... Até logo!")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    criar_tabelas()
    opcao = input("Você já tem uma conta? (s/n): ")
    if opcao == "s":
        cliente = login()
        if cliente:
            menu(cliente)
    else:
        criar_conta()
