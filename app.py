from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = "inventaweb-secret-session-key-for-auth"

# URL do Back-End em FastAPI
BACKEND_URL = "http://127.0.0.1:8000"

# --- MIDDLEWARE DE AUTENTICAÇÃO ---

@app.before_request
def require_login():
    # Permitir rotas estáticas e rotas de login/registro
    if request.path.startswith('/static') or request.path in ['/login', '/register', '/api/auth/login', '/api/auth/register']:
        return
    if 'store_id' not in session:
        return redirect(url_for('login'))

# --- ROTAS DE PÁGINAS (FRONT-END) ---

@app.route('/')
def dashboard():
    return render_template('dashboard.html', store_name=session.get('store_name'))

@app.route('/produtos')
def produtos():
    return render_template('produtos.html', store_name=session.get('store_name'))

@app.route('/clientes')
def clientes():
    return render_template('clientes.html', store_name=session.get('store_name'))

@app.route('/vendas')
def vendas():
    return render_template('vendas.html', store_name=session.get('store_name'))

@app.route('/login')
def login():
    if 'store_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register')
def register():
    if 'store_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- ROTAS DE PROXY (CONTORNO DE CORS E INJEÇÃO DE CABEÇALHO) ---

@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_proxy(subpath):
    url = f"{BACKEND_URL}/{subpath}"
    
    # Injeta a identificação da loja se o usuário estiver logado
    headers = {}
    if 'store_id' in session:
        headers['X-Store-ID'] = str(session['store_id'])
        
    try:
        # Repassando a requisição para o Back-End FastAPI
        if request.method == 'GET':
            response = requests.get(url, headers=headers)
        elif request.method == 'POST':
            response = requests.post(url, json=request.json, headers=headers)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.json, headers=headers)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers)
            
        # Captura o sucesso da autenticação para iniciar a sessão no Flask
        if subpath in ['auth/login', 'auth/register'] and response.status_code == 200:
            data = response.json()
            session['store_id'] = data.get('store_id')
            session['store_name'] = data.get('store_name')
            
        # Verificar se a resposta é um PDF (binário)
        if 'application/pdf' in response.headers.get('Content-Type', ''):
            return response.content, response.status_code, {
                'Content-Type': 'application/pdf',
                'Content-Disposition': response.headers.get('Content-Disposition', '')
            }
            
        # Repassando a resposta de volta ao Front-End JavaScript
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Não foi possível conectar ao servidor Back-End. Verifique se ele está rodando."}), 503

if __name__ == '__main__':
    # Rodando o Flask na porta 5000 acessível na rede
    app.run(host='0.0.0.0', debug=True, port=5000)
