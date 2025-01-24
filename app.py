from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import and_, func
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinica.db'  # Para SQLite
# Ou para PostgreSQL:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:senha@localhost/nome_do_banco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Mude para uma chave segura em produção

UPLOAD_FOLDER = os.path.join('static', 'img')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'sua-senha'

# Constante com as especialidades disponíveis
ESPECIALIDADES = [
    'Cardiologia',
    'Dermatologia',
    'Clínico Geral',
    'Pediatria',
    'Ortopedia',
    'Ginecologia',
    'Oftalmologia',
    'Neurologia'
]

# Constantes para limites de consultas
MAX_CONSULTAS_DIA = 8
MAX_CONSULTAS_SEMANA = 30

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default='paciente')  # Agora só teremos 'paciente'
    
    # Remover relacionamento com médico
    paciente = db.relationship('Paciente', backref='usuario', uselist=False)

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    consultas = db.relationship('Consulta', backref='paciente', lazy=True)

class Medico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(50), nullable=False)
    crm = db.Column(db.String(20), unique=True, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    
    consultas = db.relationship('Consulta', backref='medico', lazy=True)

class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medico.id'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='agendada')
    
    @staticmethod
    def verificar_disponibilidade(medico_id, data_hora):
        # Verifica se já existe consulta no mesmo horário
        consulta_existente = Consulta.query.filter_by(
            medico_id=medico_id,
            data_hora=data_hora,
            status='agendada'
        ).first()
        
        if consulta_existente:
            return False, "Horário já está ocupado"
        
        # Verifica número de consultas do médico no dia
        inicio_dia = data_hora.replace(hour=0, minute=0, second=0)
        fim_dia = inicio_dia + timedelta(days=1)
        
        consultas_dia = Consulta.query.filter(
            Consulta.medico_id == medico_id,
            Consulta.data_hora.between(inicio_dia, fim_dia),
            Consulta.status == 'agendada'
        ).count()
        
        if consultas_dia >= 8:  # Limite de 8 consultas por dia
            return False, "Médico atingiu o limite de consultas para este dia"
        
        # Verifica número de consultas do paciente na semana
        inicio_semana = data_hora - timedelta(days=data_hora.weekday())
        fim_semana = inicio_semana + timedelta(days=7)
        
        return True, "Horário disponível"

# Atualize as relações no modelo Usuario
Usuario.paciente = db.relationship('Paciente', backref='usuario', uselist=False)
Usuario.medico = db.relationship('Medico', backref='usuario', uselist=False)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            flash('Login realizado com sucesso!')
            return redirect(url_for('perfil'))
        else:
            flash('Email ou senha incorretos.')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        telefone = request.form.get('telefone')
        data_nascimento = request.form.get('data_nascimento')
        
        # Validações básicas
        if not all([nome, email, senha, confirmar_senha]):
            flash('Por favor, preencha todos os campos obrigatórios.')
            return redirect(url_for('cadastro'))
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem.')
            return redirect(url_for('cadastro'))
        
        # Verificar se o email já está cadastrado
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.')
            return redirect(url_for('cadastro'))
        
        try:
            # Criar novo usuário
            novo_usuario = Usuario(
                email=email,
                senha=generate_password_hash(senha),
                tipo='paciente'
            )
            db.session.add(novo_usuario)
            db.session.flush()  # Gera o ID do usuário
            
            # Criar novo paciente
            data_nasc = datetime.strptime(data_nascimento, '%Y-%m-%d').date() if data_nascimento else None
            novo_paciente = Paciente(
                nome=nome,
                email=email,
                telefone=telefone,
                data_nascimento=data_nasc,
                usuario_id=novo_usuario.id
            )
            db.session.add(novo_paciente)
            db.session.commit()
            
            # Fazer login automático após o cadastro
            login_user(novo_usuario)
            flash('Cadastro realizado com sucesso!')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao realizar cadastro. Por favor, tente novamente.')
            print(f"Erro no cadastro: {str(e)}")  # Para debug
            return redirect(url_for('cadastro'))
    
    return render_template('cadastro.html')

@app.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    if not current_user.is_authenticated:
        flash('Por favor, faça login para agendar uma consulta.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        medico_id = request.form.get('medico_id')
        data = request.form.get('data')
        horario = request.form.get('horario')
        
        # Criar data_hora
        try:
            data_hora = datetime.strptime(f"{data} {horario}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash('Data ou horário inválido')
            return redirect(url_for('agendar'))
        
        # Verificar disponibilidade
        disponivel, mensagem = Consulta.verificar_disponibilidade(medico_id, data_hora)
        if not disponivel:
            flash(mensagem)
            return redirect(url_for('agendar'))
        
        # Criar nova consulta
        nova_consulta = Consulta(
            paciente_id=current_user.paciente.id,
            medico_id=medico_id,
            data_hora=data_hora
        )
        
        try:
            db.session.add(nova_consulta)
            db.session.commit()
            flash('Consulta agendada com sucesso!')
            return redirect(url_for('perfil'))
        except:
            db.session.rollback()
            flash('Erro ao agendar consulta')
    
    especialidade_selecionada = request.args.get('especialidade', '')
    
    # Buscar médicos agrupados por especialidade
    medicos_por_especialidade = {}
    for especialidade in ESPECIALIDADES:
        medicos = Medico.query.filter_by(especialidade=especialidade).all()
        if medicos:
            # Converter médicos para dicionário para ser serializável
            medicos_lista = [{'id': m.id, 'nome': m.nome, 'crm': m.crm} for m in medicos]
            medicos_por_especialidade[especialidade] = medicos_lista
    
    return render_template('agendar.html',
                         especialidades=ESPECIALIDADES,
                         medicos=Medico.query.all(),
                         medicos_por_especialidade=medicos_por_especialidade,
                         especialidade_selecionada=especialidade_selecionada,
                         hoje=datetime.now().strftime('%Y-%m-%d'),
                         max_data=(datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'))

@app.route('/api/horarios-disponiveis', methods=['GET'])
def horarios_disponiveis():
    medico_id = request.args.get('medico_id')
    data = request.args.get('data')
    
    if not medico_id or not data:
        return jsonify([])
    
    # Horários possíveis de consulta
    horarios_possiveis = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
    
    # Converter a data para datetime
    data_consulta = datetime.strptime(data, '%Y-%m-%d').date()
    
    # Buscar consultas existentes do médico na data
    consultas = Consulta.query.filter(
        Consulta.medico_id == medico_id,
        db.func.date(Consulta.data_hora) == data_consulta
    ).all()
    
    # Remover horários já agendados
    horarios_ocupados = [c.data_hora.strftime('%H:%M') for c in consultas]
    horarios_disponiveis = [h for h in horarios_possiveis if h not in horarios_ocupados]
    
    return jsonify(horarios_disponiveis)

@app.route('/painel-medico')
@login_required
def painel_medico():
    if current_user.tipo != 'medico':
        abort(403)  # Acesso negado
    
    # Buscar consultas do médico
    hoje = datetime.now().date()
    consultas_hoje = Consulta.query.filter(
        Consulta.medico_id == current_user.medico.id,
        db.func.date(Consulta.data_hora) == hoje
    ).order_by(Consulta.data_hora).all()
    
    proximas_consultas = Consulta.query.filter(
        Consulta.medico_id == current_user.medico.id,
        db.func.date(Consulta.data_hora) > hoje
    ).order_by(Consulta.data_hora).all()
    
    return render_template('painel_medico.html',
                         consultas_hoje=consultas_hoje,
                         proximas_consultas=proximas_consultas)

@app.route('/perfil')
@login_required
def perfil():
    # Buscar consultas do usuário
    consultas = Consulta.query.filter_by(
        paciente_id=current_user.paciente.id
    ).order_by(Consulta.data_hora.desc()).all()
    
    return render_template('perfil.html', consultas=consultas)

@app.route('/cancelar-consulta/<int:consulta_id>', methods=['POST'])
@login_required
def cancelar_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Verificar se o usuário tem permissão para cancelar
    if current_user.tipo == 'paciente' and consulta.paciente_id != current_user.paciente.id:
        abort(403)
    
    # Não permitir cancelamento de consultas passadas
    if consulta.data_hora < datetime.now():
        return jsonify({'error': 'Não é possível cancelar consultas passadas'}), 400
    
    consulta.status = 'cancelada'
    db.session.commit()
    
    return jsonify({'message': 'Consulta cancelada com sucesso'})

# Recrie o banco de dados
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Criar alguns médicos de exemplo
        medicos = [
            Medico(nome='Dr. João Silva', especialidade='Cardiologia', crm='12345-SP'),
            Medico(nome='Dra. Maria Santos', especialidade='Dermatologia', crm='23456-SP'),
            Medico(nome='Dr. Pedro Oliveira', especialidade='Clínico Geral', crm='34567-SP')
        ]
        
        for medico in medicos:
            db.session.add(medico)
        
        db.session.commit()

# Chame esta função para recriar o banco de dados
init_db()

if __name__ == '__main__':
    app.run(debug=True)  # Ativa o modo debug para desenvolvimento 