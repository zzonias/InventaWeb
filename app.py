from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# URL do Back-End em FastAPI
BACKEND_URL = "http://127.0.0.1:8000"

# --- ROTAS DE PÁGINAS (FRONT-END) ---

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/produtos')
def produtos():
    return render_template('produtos.html')

@app.route('/clientes')
def clientes():
    return render_template('clientes.html')

@app.route('/vendas')
def vendas():
    return render_template('vendas.html')

# --- ROTAS DE PROXY (CONTORNO DE CORS) ---
# O Front-End acessa o Back-End através destas rotas.

@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(subpath):
    url = f"{BACKEND_URL}/{subpath}"
    
    try:
        # Repassando a requisição para o Back-End FastAPI
        if request.method == 'GET':
            response = requests.get(url)
        elif request.method == 'POST':
            response = requests.post(url, json=request.json)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.json)
        elif request.method == 'DELETE':
            response = requests.delete(url)
            
        # Repassando a resposta de volta ao Front-End JavaScript
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Não foi possível conectar ao servidor Back-End. Verifique se ele está rodando."}), 503

if __name__ == '__main__':
    # Rodando o Flask na porta 5000 acessível na rede
    app.run(host='0.0.0.0', debug=True, port=5000)
