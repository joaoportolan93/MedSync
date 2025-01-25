
# Medical Scheduler

Bem-vindo ao repositório do **Medical Scheduler**, um sistema projetado para simplificar e modernizar o agendamento de consultas médicas.

Este README fornece uma breve visão geral do projeto e instruções básicas para começar a utilizá-lo. Para informações mais detalhadas, consulte a [Documentação Completa](DOCUMENTATION.md) ou o [Manual de Uso](USER_GUIDE.md).

---

## Apresentação

O **Medical Scheduler** é uma aplicação web responsiva, intuitiva e funcional, desenvolvida para otimizar o fluxo de trabalho de clínicas e consultórios médicos. Ele permite que pacientes agendem consultas rapidamente e que profissionais de saúde gerenciem suas agendas de forma eficiente.

Principais funcionalidades:

- **Agendamento Online**: Marque, cancele ou remarque consultas.
- **Gerenciamento de Usuários**: Cadastro de pacientes e profissionais.
- **Lembretes Automáticos**: Envio de notificações para evitar faltas.

---

## Tecnologias Utilizadas

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Banco de Dados**: SQLite

---

## Instruções Básicas

### 1. Clonar o Repositório

```bash
git clone https://github.com/joaoportolan93/medical-scheduler.git
cd medical-scheduler
```

### 2. Configurar o Ambiente

Crie um ambiente virtual e instale as dependências:

```bash
python3 -m venv venv
source venv/bin/activate  # No Windows, use venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Inicializar o Banco de Dados

Configure o banco de dados com:

```bash
flask init-db
```

### 4. Executar o Servidor

Inicie o servidor localmente:

```bash
flask run
```

Acesse o sistema no navegador em: [http://localhost:5000](http://localhost:5000)

---

Para mais detalhes sobre a arquitetura e funcionalidades do sistema, acesse a [Documentação Completa](DOCUMENTATION.md).

Para instruções detalhadas sobre como utilizar o sistema, veja o [Manual de Uso](USER_GUIDE.md).

---

## Contribuições

Contribuições são bem-vindas! Por favor, abra uma issue ou envie um pull request.

## Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo LICENSE para mais detalhes.

