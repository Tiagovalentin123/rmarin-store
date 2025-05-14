# Loja Online R.MARIN - Instruções

Este ficheiro contém as instruções para configurar e executar a aplicação da loja online R.MARIN.

## 1. Pré-requisitos

*   Python 3.11 ou superior
*   pip (gestor de pacotes Python)
*   Acesso a uma base de dados MySQL (para produção; uma base de dados local `mydb` com utilizador `root` e password `password` é usada por defeito para desenvolvimento, conforme configurado no `create_flask_app`).

## 2. Configuração

1.  **Descompactar o Projeto:** Extraia o conteúdo do ficheiro `rmarin_store.zip` para um diretório à sua escolha.
2.  **Ambiente Virtual:** Navegue até ao diretório do projeto (`rmarin_store`) e crie/ative um ambiente virtual:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```
3.  **Instalar Dependências:** Instale as bibliotecas necessárias:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configurar Chaves de Pagamento (Stripe):**
    *   Abra o ficheiro `src/main.py`.
    *   Localize as linhas:
        ```python
        app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY", "pk_test_YOUR_PUBLIC_KEY") # Replace with your test public key
        app.config["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_SECRET_KEY") # Replace with your test secret key
        ```
    *   **IMPORTANTE:** Substitua `"pk_test_YOUR_PUBLIC_KEY"` e `"sk_test_YOUR_SECRET_KEY"` pelas suas chaves **reais** (ou de teste) fornecidas pelo Stripe. Para produção, é altamente recomendado configurar estas chaves através de variáveis de ambiente (`STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`) em vez de as colocar diretamente no código.
5.  **Configurar Número WhatsApp:**
    *   Abra os ficheiros `src/static/base.html` e `src/static/about.html`.
    *   Procure por `SEUNUMEROWHATSAPP`.
    *   **IMPORTANTE:** Substitua `SEUNUMEROWHATSAPP` pelo seu número de WhatsApp completo, incluindo o código do país (ex: `55119XXXXXXXX` para Brasil, `3519XXXXXXXX` para Portugal).
6.  **Configurar Base de Dados (Produção):**
    *   No ficheiro `src/main.py`, a linha de configuração da base de dados é:
        ```python
        app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{os.getenv("DB_USERNAME", "root")}:{os.getenv("DB_PASSWORD", "password")}@{os.getenv("DB_HOST", "localhost")}:{os.getenv("DB_PORT", "3306")}/{os.getenv("DB_NAME", "mydb")}"
        ```
    *   Para produção, configure as variáveis de ambiente `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, e `DB_NAME` com as credenciais da sua base de dados MySQL.
7.  **Imagens dos Produtos:**
    *   A aplicação adiciona produtos de exemplo se a base de dados estiver vazia.
    *   Coloque as imagens correspondentes (`bikini_a.jpg`, `shorts_b.jpg`, `onepiece_c.jpg`) no diretório `src/static/images/`.
    *   Para adicionar os seus próprios produtos, pode modificar a função `add_dummy_products` em `src/routes/store.py` ou criar uma interface de administração (não incluída neste projeto base).

## 3. Executar a Aplicação (Desenvolvimento)

Após a configuração, execute a aplicação Flask:

```bash
python src/main.py
```

A aplicação estará acessível em `http://localhost:5000` (ou na porta definida pela variável de ambiente `PORT`).

## 4. Funcionalidades Implementadas

*   Catálogo de produtos.
*   Carrinho de compras (adicionar, remover, atualizar quantidade).
*   Checkout com recolha de dados do cliente (nome, email, telefone, morada).
*   Seleção de método de pagamento (Cartão de Crédito via Stripe implementado em modo de teste; placeholders para MB WAY e PayPal).
*   Processamento de pagamento simulado com Stripe (requer chaves de teste válidas).
*   Criação de encomenda na base de dados.
*   Atualização do estado da encomenda e stock após pagamento bem-sucedido (Stripe).
*   Página de confirmação de encomenda.
*   Página "Sobre Nós" com texto de exemplo.
*   Links para contacto via WhatsApp (requer configuração do número).

## 5. Próximos Passos e Melhorias

*   **Produção:** Configure variáveis de ambiente para todas as chaves secretas e credenciais de base de dados.
*   **MB WAY / PayPal:** Implemente a lógica de integração para MB WAY e PayPal, substituindo os placeholders.
*   **Gestão de Produtos/Encomendas:** Crie uma interface de administração para gerir produtos, stocks e visualizar encomendas.
*   **Autenticação de Utilizador:** Implemente um sistema de login para clientes.
*   **Emails Transacionais:** Configure o envio de emails de confirmação de encomenda, envio, etc.
*   **Design:** Personalize o design e layout conforme a identidade visual da R.MARIN.
*   **Imagens:** Adicione imagens reais dos produtos.
*   **Segurança:** Reveja e reforce as medidas de segurança, especialmente em produção.
*   **Testes:** Adicione testes automatizados.

## 6. Deployment

Esta aplicação Flask está estruturada para ser implementada. Pode usar o comando `deploy_apply_deployment` com `type='flask'` e o diretório local `/home/ubuntu/rmarin_store`.

