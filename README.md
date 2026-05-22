# InventaWeb 🚀

O **InventaWeb** é um sistema moderno, rápido e responsivo de gestão de estoque, vendas e clientes, construído com uma arquitetura dividida entre Front-end Web, App Mobile e Back-end.

## 🛠 Arquitetura do Projeto

O sistema foi arquitetado para ser escalável e seguro, dividindo suas responsabilidades em:

- **Back-end (FastAPI):** Uma API REST extremamente rápida em Python que se conecta com o banco de dados `SQLite` (`inventaweb.db`) para gerenciar e validar todas as transações, estoques e dados dos clientes.
- **Front-end Web (Flask / HTML / CSS / JS):** Interface de administração rica e responsiva. Pode ser acessada tanto pelo computador quanto pelo celular (Web App) de forma confortável.
- **Aplicativo Mobile (Dart / Flutter):** Um projeto de aplicativo nativo (`inventaweb_mobile`) focado na usabilidade de campo, consumindo as mesmas informações do servidor.

## ✨ Principais Funcionalidades

- **📦 Gestão de Produtos:** Cadastro de itens com controle rigoroso de estoque e definição de estoque mínimo (alerta de baixa).
- **👥 Gestão de Clientes:** Cadastro de clientes incluindo e-mail, CPF e telefone. O sistema calcula automaticamente o **Produto Favorito** (mais comprado) de cada cliente com base no histórico de vendas!
- **🛒 PDV (Ponto de Venda):** Registro rápido de vendas, com dedução automática do estoque e cálculo de faturamento no Dashboard.
- **🔔 Caixa de Notificações:** Sistema de alertas na tela inicial para produtos que estão atingindo o limite mínimo de estoque.
- **📲 Integração WhatsApp:** Botão nativo para notificar clientes diretamente no WhatsApp sobre promoções.
- **🌓 Modo Escuro (Dark Mode):** Suporte nativo para tema escuro e tema claro, ativável pelo usuário e salvo na sessão local do navegador.
- **📱 Responsividade Extrema:** O layout se adapta perfeitamente a dispositivos móveis, com um Menu Hambúrguer retrátil para ganhar espaço em telas pequenas.

## 🚀 Como Executar Localmente

### 1. Iniciar o Back-end (API)
Abra um terminal na pasta raiz do projeto e rode:
```bash
python -m uvicorn main:app --port 8000
```

### 2. Iniciar o Front-end Web (Interface)
Abra outro terminal na pasta raiz e rode:
```bash
python app.py
```
A interface estará disponível em `http://127.0.0.1:5000`.

### 3. Expor para a Equipe (Opcional - Cloudflare)
Se quiser gerar um link público para acessar do celular de qualquer lugar:
```bash
cloudflared tunnel --url http://127.0.0.1:5000
```

---
*Desenvolvido em parceria com Antigravity AI.*
