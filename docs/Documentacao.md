# Documentação Completa (PT-BR)

## Introdução

O **MedSync** é uma plataforma web desenvolvida para otimizar o agendamento de consultas médicas. Este sistema oferece funcionalidades completas para pacientes, médicos e administradores de clínicas.

---

## Arquitetura do Sistema

### Tecnologias Utilizadas

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python com Flask
- **Banco de Dados**: SQLite
- **Gerenciamento de Dependências**: pip

### Estrutura de Pastas

- `app/`: Contém os principais arquivos da aplicação.
  - `templates/`: Arquivos HTML.
  - `static/`: Arquivos CSS, JS e imagens.
  - `routes.py`: Gerencia as rotas da aplicação.
  - `models.py`: Define as classes do banco de dados.
  - `forms.py`: Define os formulários utilizados.

---

## Funcionalidades Principais

### Agendamento de Consultas

- Pacientes podem selecionar médicos, datas e horários disponíveis.
- Médicos podem visualizar e gerenciar suas agendas.

### Cadastro de Usuários

- Cadastro de pacientes e profissionais com validação de dados.
- Atualização e exclusão de usuários via painel administrativo.

### Lembretes

- Notificações por e-mail para lembrar os pacientes sobre consultas.

---

## Configuração do Ambiente

1. Clone o repositório:
   ```bash
   git clone https://github.com/joaoportolan93/medical-scheduler.git
   cd MedSync
   ```

2. Crie um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # No Windows, use venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Inicialize o banco de dados:
   ```bash
   flask init-db
   ```

5. Inicie o servidor:
   ```bash
   flask run
   ```

Acesse o sistema em [http://localhost:5000](http://localhost:5000).

