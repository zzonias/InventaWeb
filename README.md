# InventaWeb

Um sistema simples e moderno para controle de estoque e gestão de vendas. O projeto utiliza uma arquitetura separada com um Back-End rápido construído em **FastAPI** e um Front-End elegante construído em **Flask** (utilizando HTML, CSS puro e JavaScript).

## 🚀 Tecnologias Utilizadas

- **Back-End:** Python, FastAPI, Banco de Dados SQLite.
- **Front-End:** Python, Flask, HTML5, CSS3 (Design moderno com Flexbox e Grid), JavaScript (Fetch API).

## 🛠️ Como Instalar e Configurar

1. Certifique-se de ter o [Python](https://www.python.org/downloads/) instalado no seu computador.
2. Clone este repositório ou abra a pasta do projeto no seu terminal.
3. Instale todas as dependências necessárias executando o comando abaixo:
   ```powershell
   pip install fastapi uvicorn pydantic flask requests
   ```

## 💻 Como Rodar o Sistema

O funcionamento do InventaWeb exige que o Back-End e o Front-End estejam rodando **ao mesmo tempo**. Para isso, abra **dois terminais** na pasta do projeto:

**No Terminal 1 (Iniciando o Back-End):**
```powershell
uvicorn main:app --reload --port 8000
```

**No Terminal 2 (Iniciando o Front-End):**
```powershell
python app.py
```

Após iniciar os dois servidores, abra o seu navegador e acesse o sistema pelo link:
👉 **`http://127.0.0.1:5000`**

## 🌐 Acesso por Outros Dispositivos (Rede Local)

O sistema já está configurado (`host='0.0.0.0'`) para aceitar conexões de outros computadores ou celulares que estejam conectados na **mesma rede Wi-Fi/cabo**. 

Para acessar de outro dispositivo, basta substituir `127.0.0.1` pelo endereço IP do computador principal. Exemplo:
`http://192.168.15.10:5000`

*(Nota: Caso a página não carregue, verifique se o Firewall do Windows não está bloqueando o Python).*
