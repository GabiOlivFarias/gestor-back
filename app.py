# backend/app.py

import os
import psycopg2
from psycopg2.extras import RealDictCursor # Facilita a conversão para dicionário
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (usado para desenvolvimento local)
load_dotenv()

app = Flask(__name__)
# Configura o CORS para permitir requisições do seu frontend
# Em produção, seria ideal restringir a origem: CORS(app, origins=["https://seu-frontend.onrender.com"])
CORS(app)

# Função para obter a conexão com o banco de dados PostgreSQL
def get_db_connection():
    """Estabelece conexão com o banco de dados PostgreSQL usando a URL do ambiente."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    return conn

# Comando para inicializar o banco de dados (agora para PostgreSQL)
@app.cli.command('init-db')
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
    # Usando RealDictCursor para que o resultado já venha no formato de dicionário
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
    # O placeholder no psycopg2 é %s em vez de ?
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
    
    # Busca a cobrança para verificar o estado atual
    cur.execute("SELECT * FROM cobrancas WHERE id = %s", (id,))
    cobranca = cur.fetchone()

    if cobranca is None:
        cur.close()
        conn.close()
        return jsonify({'error': 'Cobrança não encontrada'}), 404

    # Incrementa o número de parcelas pagas
    novas_parcelas_pagas = cobranca['parcelas_pagas'] + 1
    
    cur.execute(
        "UPDATE cobrancas SET parcelas_pagas = %s WHERE id = %s", 
        (novas_parcelas_pagas, id)
    )
    conn.commit()
    
    cur.close()
    conn.close()
    return jsonify({'status': 'success', 'novas_parcelas_pagas': novas_parcelas_pagas})
