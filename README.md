# InventaWeb 🚀

O **InventaWeb** é um sistema moderno, rápido e responsivo de gestão de estoque, vendas e clientes, construído com uma arquitetura dividida entre Front-end Web, App Mobile e Back-end.

## 🛠 Arquitetura do Projeto

O sistema foi arquitetado para ser escalável e seguro, dividindo suas responsabilidades em:

- **Back-end (FastAPI):** Uma API REST extremamente rápida em Python que se conecta com o banco de dados `SQLite` (`inventaweb.db`) para gerenciar, validar e isolar todas as transações, estoques e dados dos clientes por loja.
- **Front-end Web (Flask / HTML / CSS / JS):** Interface de administração rica e responsiva, com controle de sessões seguro. Pode ser acessada tanto pelo computador quanto pelo celular (Web App) de forma confortável.
- **Aplicativo Mobile (Dart / Flutter):** Um projeto de aplicativo nativo (`inventaweb_mobile`) focado na usabilidade de campo, consumindo as mesmas informações do servidor.

## ✨ Principais Funcionalidades

- **🔐 Autenticação e Multi-Loja (Multitenancy):** Login e cadastro de novas contas. Cada usuário gerencia os dados de sua própria loja em total isolamento.
- **📦 Gestão de Produtos & Código de Barras (EAN-13):** Cadastro de itens com controle rigoroso de estoque e definição de estoque mínimo (alerta de baixa). Suporte para busca rápida e checkout por bipagem de código de barras.
- **📄 Emissão de Notas Fiscais Auxiliares (NFC-e):** Geração dinâmica de nota fiscal simulada em PDF no back-end (utilizando a biblioteca `ReportLab`) com chave de acesso de 44 dígitos e código de barras, disponível para download a cada venda.
- **📈 Relatórios e Filtros Mensais:**
  * **Dashboard:** Dropdown para filtrar métricas por mês e painel comparativo exibindo total de vendas, faturamento e ticket médio mês a mês.
  * **Vendas:** Histórico organizado automaticamente por abas de períodos mensais.
- **👥 Gestão de Clientes:** Cadastro de clientes incluindo e-mail, CPF e telefone. O sistema calcula automaticamente o **Produto Favorito** (mais comprado) de cada cliente com base no histórico de vendas.
- **🛒 PDV & Integração Mercado Livre:** Registro manual rápido de vendas no caixa ou simulação de vendas online sincronizadas do Mercado Livre com atualização de estoque em tempo real.
- **🌓 Modo Escuro (Dark Mode):** Suporte nativo para tema escuro e tema claro, ativável pelo usuário e salvo na sessão local do navegador.
- **📱 Responsividade Extrema:** O layout se adapta perfeitamente a dispositivos móveis, com menu hambúrguer retrátil e controle facilitado de fechar (botão X).

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

