# api/index.py

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (usado para desenvolvimento local)
load_dotenv()

app = Flask(__name__)
CORS(app)

# Função para obter a conexão com o banco de dados PostgreSQL
def get_db_connection():
    """Estabelece conexão com o banco de dados PostgreSQL usando a URL do ambiente."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

# <--- MUDANÇA 1: DECORADOR REMOVIDO --->
# O decorador @app.cli.command('init-db') foi removido. 
# Ele não é usado no Vercel, mas a função em si é o que precisamos.
def init_db_command():
    conn = get_db_connection()
    cur = conn.cursor()
    # Sintaxe para PostgreSQL: SERIAL PRIMARY KEY auto-incrementa o ID.
    cur.execute('''
    CREATE TABLE IF NOT EXISTS cobrancas (
        id SERIAL PRIMARY KEY,
        nome_cliente TEXT NOT NULL,
        telefone TEXT,
        descricao TEXT,
        valor REAL NOT NULL,
        total_parcelas INTEGER NOT NULL,
        parcelas_pagas INTEGER NOT NULL,
        frequencia TEXT NOT NULL,
        data_inicio TEXT NOT NULL
    )
    ''')
    conn.commit()
    cur.close()
    conn.close()
    print("Banco de dados PostgreSQL inicializado.")

# Endpoint para buscar todas as cobranças
@app.route('/api/cobrancas', methods=['GET'])
def get_cobrancas():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM cobrancas ORDER BY data_inicio")
    cobrancas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(cobrancas)

# Endpoint para adicionar uma nova cobrança
@app.route('/api/cobrancas', methods=['POST'])
def add_cobranca():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO cobrancas 
        (nome_cliente, telefone, descricao, valor, total_parcelas, parcelas_pagas, frequencia, data_inicio) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            data['nome'], data['telefone'], data['descricao'], data['valor'], 
            data['totalParcelas'], 0, data['frequencia'], data['dataInicio']
        )
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'status': 'success'}), 201

# Endpoint para marcar uma parcela como paga
@app.route('/api/cobrancas/<int:id>/pagar', methods=['PUT'])
def marcar_como_pago(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("SELECT * FROM cobrancas WHERE id = %s", (id,))
    cobranca = cur.fetchone()

    if cobranca is None:
        cur.close()
        conn.close()
        return jsonify({'error': 'Cobrança não encontrada'}), 404

    novas_parcelas_pagas = cobranca['parcelas_pagas'] + 1
    
    cur.execute(
        "UPDATE cobrancas SET parcelas_pagas = %s WHERE id = %s", 
        (novas_parcelas_pagas, id)
    )
    conn.commit()
    
    cur.close()
    conn.close()
    return jsonify({'status': 'success', 'novas_parcelas_pagas': novas_parcelas_pagas})


# <--- MUDANÇA 2: ENDPOINT SECRETO ADICIONADO --->
# Adicione este bloco de código no final do seu arquivo.
# TROQUE A CHAVE SECRETA por algo que só você saiba!
SECRET_KEY_FOR_INIT = "gestor-back-gabrielas-projects-5c57887c.vercel.app/api/init-db/minha-chave-super-secreta-para-iniciar-o-banco-123"

@app.route(f'/api/init-db/{SECRET_KEY_FOR_INIT}')
def secret_init_db():
    try:
        init_db_command()
        return "Banco de dados inicializado com sucesso!"
    except Exception as e:
        return f"Ocorreu um erro: {e}", 500