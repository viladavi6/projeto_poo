import tkinter as tk
from tkinter import messagebox
import banco_dados as db
import sqlite3
import random

# ---------------------------------------------------------------
# This project was developed as part of the Backend Python course
# offered by Digital Innovation One (DIO) in partnership with Vivo.
# ---------------------------------------------------------------

db.criar_tabelas()

def centralizar_janela(janela, largura, altura):
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")

def buscar_conta_por_cpf(cpf_usuario):
    conexao = db.conectar()
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT contas.id, contas.agencia, contas.numero_conta, contas.saldo
        FROM contas
        JOIN usuarios ON contas.usuario_id = usuarios.id
        WHERE usuarios.cpf = ?
    ''', (cpf_usuario,))
    conta = cursor.fetchone()
    conexao.close()
    return conta

def inserir_usuario():
    def salvar_usuario():
        try:
            conexao = db.conectar()
            cursor = conexao.cursor()
            cursor.execute('''
                INSERT INTO usuarios (nome, cpf, nascimento, rua, numero, bairro, cidade, uf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                nome.get(), cpf.get(), nascimento.get(), rua.get(), numero.get(),
                bairro.get(), cidade.get(), uf.get()
            ))
            conexao.commit()
            conexao.close()
            messagebox.showinfo("Success", "User registered successfully.")
            janela_usuario.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "CPF already exists.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    janela_usuario = tk.Toplevel()
    janela_usuario.title("Register User")
    centralizar_janela(janela_usuario, 400, 350)

    campos = [("Name", ""), ("CPF", ""), ("Birth Date", ""), ("Street", ""), ("Number", ""),
              ("District", ""), ("City", ""), ("State (UF)", "")]
    entradas = []

    for i, (label_text, _) in enumerate(campos):
        tk.Label(janela_usuario, text=label_text).grid(row=i, column=0, sticky="e", pady=2)
        entry = tk.Entry(janela_usuario)
        entry.grid(row=i, column=1, pady=2)
        entradas.append(entry)

    nome, cpf, nascimento, rua, numero, bairro, cidade, uf = entradas
    tk.Button(janela_usuario, text="Save", width=20, command=salvar_usuario).grid(row=len(campos), columnspan=2, pady=10)

def inserir_conta():
    def salvar_conta():
        cpf_usuario = cpf.get()
        conexao = db.conectar()
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE cpf = ?", (cpf_usuario,))
        usuario = cursor.fetchone()

        if usuario:
            id_usuario = usuario[0]
            numero_conta = f"{random.randint(10000,99999)}-{random.randint(0,9)}"
            agencia = "0001"
            cursor.execute('''
                INSERT INTO contas (agencia, numero_conta, usuario_id)
                VALUES (?, ?, ?)
            ''', (agencia, numero_conta, id_usuario))
            conexao.commit()
            conexao.close()
            messagebox.showinfo("Success", f"Account created!\nAgency: {agencia}\nAccount: {numero_conta}")
            janela_conta.destroy()
        else:
            messagebox.showerror("Error", "CPF not found. Please register the user first.")
            conexao.close()

    janela_conta = tk.Toplevel()
    janela_conta.title("Register Account")
    centralizar_janela(janela_conta, 350, 120)

    tk.Label(janela_conta, text="User CPF:").grid(row=0, column=0, pady=10)
    cpf = tk.Entry(janela_conta)
    cpf.grid(row=0, column=1)

    tk.Button(janela_conta, text="Create Account", command=salvar_conta).grid(row=1, columnspan=2, pady=10)

def realizar_transacao(tipo):
    def confirmar():
        conta = buscar_conta_por_cpf(cpf.get())
        if not conta:
            messagebox.showerror("Error", "Account not found for this CPF.")
            return

        conta_id, _, _, saldo = conta
        try:
            valor_float = float(valor.get())
            if valor_float <= 0:
                raise ValueError("Value must be greater than zero.")

            if tipo == "saque" and valor_float > saldo:
                raise ValueError("Insufficient balance.")

            conexao = db.conectar()
            cursor = conexao.cursor()

            novo_saldo = saldo + valor_float if tipo == "deposito" else saldo - valor_float

            cursor.execute("UPDATE contas SET saldo = ? WHERE id = ?", (novo_saldo, conta_id))
            cursor.execute('''
                INSERT INTO movimentacoes (conta_id, tipo, valor)
                VALUES (?, ?, ?)
            ''', (conta_id, tipo, valor_float))
            conexao.commit()
            conexao.close()

            messagebox.showinfo("Success", f"{tipo.capitalize()} successful.\nNew Balance: R${novo_saldo:.2f}")
            janela_transacao.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    janela_transacao = tk.Toplevel()
    janela_transacao.title(tipo.capitalize())
    centralizar_janela(janela_transacao, 350, 150)

    tk.Label(janela_transacao, text="User CPF:").grid(row=0, column=0, pady=5)
    cpf = tk.Entry(janela_transacao)
    cpf.grid(row=0, column=1)

    tk.Label(janela_transacao, text="Amount (R$):").grid(row=1, column=0, pady=5)
    valor = tk.Entry(janela_transacao)
    valor.grid(row=1, column=1)

    tk.Button(janela_transacao, text="Confirm", command=confirmar).grid(row=2, columnspan=2, pady=10)

def exibir_extrato():
    def mostrar():
        conta = buscar_conta_por_cpf(cpf.get())
        if not conta:
            messagebox.showerror("Error", "Account not found.")
            return

        conta_id = conta[0]
        conexao = db.conectar()
        cursor = conexao.cursor()
        cursor.execute('''
            SELECT tipo, valor, data
            FROM movimentacoes
            WHERE conta_id = ?
            ORDER BY data DESC
        ''', (conta_id,))
        transacoes = cursor.fetchall()
        conexao.close()

        janela_resultado = tk.Toplevel()
        janela_resultado.title("Statement")
        centralizar_janela(janela_resultado, 400, 300)

        if not transacoes:
            tk.Label(janela_resultado, text="No transactions found.").pack(pady=10)
            return

        for tipo, valor, data in transacoes:
            tk.Label(janela_resultado, text=f"{data[:19]} - {tipo.capitalize()}: R${valor:.2f}").pack(anchor="w")

    janela_extrato = tk.Toplevel()
    janela_extrato.title("Statement")
    centralizar_janela(janela_extrato, 350, 100)

    tk.Label(janela_extrato, text="User CPF:").grid(row=0, column=0, pady=10)
    cpf = tk.Entry(janela_extrato)
    cpf.grid(row=0, column=1)

    tk.Button(janela_extrato, text="Show Statement", command=mostrar).grid(row=1, columnspan=2, pady=10)

# Main window setup
janela = tk.Tk()
janela.title("Digital Bank")
centralizar_janela(janela, 400, 400)

tk.Label(janela, text="Digital Bank", font=("Arial", 14)).pack(pady=20)

tk.Button(janela, text="Register User", width=30, command=inserir_usuario).pack(pady=5)
tk.Button(janela, text="Register Account", width=30, command=inserir_conta).pack(pady=5)
tk.Button(janela, text="Deposit", width=30, command=lambda: realizar_transacao("deposito")).pack(pady=5)
tk.Button(janela, text="Withdraw", width=30, command=lambda: realizar_transacao("saque")).pack(pady=5)
tk.Button(janela, text="Statement", width=30, command=exibir_extrato).pack(pady=5)
tk.Button(janela, text="Exit", width=30, command=janela.destroy).pack(pady=20)

janela.mainloop()
