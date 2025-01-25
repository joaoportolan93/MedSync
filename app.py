from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import and_, func
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinica.db'  # Para SQLite
# Ou para PostgreSQL:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:senha@localhost/nome_do_banco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Mude para uma chave segura em produção

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    cpf = db.Column(db.String(14))
    genero = db.Column(db.String(20))
    endereco = db.Column(db.String(200))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    foto_perfil = db.Column(db.String(200))  # Caminho para a foto
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
    status = db.Column(db.String(20), default='agendada')  # agendada, realizada, cancelada
    data_cancelamento = db.Column(db.DateTime)
    motivo_cancelamento = db.Column(db.String(200))
    
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
        try:
            # Obter dados do formulário
            nome = request.form.get('nome')
            email = request.form.get('email')
            senha = request.form.get('senha')
            telefone = request.form.get('telefone')
            data_nascimento = request.form.get('data_nascimento')

            # Validações básicas
            if not nome or not email or not senha:
                flash('Por favor, preencha todos os campos obrigatórios.')
                return redirect(url_for('cadastro'))

            # Verificar se o email já existe
            if Usuario.query.filter_by(email=email).first():
                flash('Email já cadastrado.')
                return redirect(url_for('cadastro'))

            # Criar usuário
            novo_usuario = Usuario(
                email=email,
                senha=generate_password_hash(senha),
                tipo='paciente'
            )
            
            # Adicionar usuário ao banco
            db.session.add(novo_usuario)
            db.session.flush()

            # Criar paciente
            novo_paciente = Paciente(
                nome=nome,
                email=email,
                telefone=telefone,
                usuario_id=novo_usuario.id
            )

            # Tratar data de nascimento se fornecida
            if data_nascimento:
                try:
                    data_nasc = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                    novo_paciente.data_nascimento = data_nasc
                except ValueError:
                    pass  # Se a data for inválida, ignora

            # Adicionar paciente ao banco
            db.session.add(novo_paciente)
            db.session.commit()

            # Login automático
            login_user(novo_usuario)
            flash('Cadastro realizado com sucesso!')
            return redirect(url_for('perfil'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro no cadastro: {str(e)}")  # Log do erro
            flash('Erro ao realizar cadastro. Por favor, tente novamente.')
            return redirect(url_for('cadastro'))

    return render_template('cadastro.html')

@app.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    if request.method == 'POST':
        try:
            # Pegar dados do formulário
            medico_id = request.form.get('medico_id')
            data = request.form.get('data')
            horario = request.form.get('horario')
            
            # Converter data e horário para datetime
            data_hora = datetime.strptime(f"{data} {horario}", "%Y-%m-%d %H:%M")
            
            # Criar nova consulta
            nova_consulta = Consulta(
                paciente_id=current_user.paciente.id,
                medico_id=medico_id,
                data_hora=data_hora,
                status='agendada'
            )
            
            db.session.add(nova_consulta)
            db.session.commit()
            
            flash('Consulta agendada com sucesso!', 'success')
            return redirect(url_for('perfil'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao agendar consulta. Por favor, tente novamente.', 'error')
            print(f"Erro no agendamento: {str(e)}")  # Para debug
    
    # Código GET existente
    especialidade_selecionada = request.args.get('especialidade', '')
    especialidades = ['Cardiologia', 'Dermatologia', 'Ortopedia', 'Pediatria', 'Ginecologia', 'Oftalmologia']
    hoje = date.today().strftime('%Y-%m-%d')
    max_data = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    medicos_por_especialidade = {}
    for esp in especialidades:
        medicos = Medico.query.filter_by(especialidade=esp).all()
        medicos_por_especialidade[esp] = [{'id': m.id, 'nome': m.nome, 'crm': m.crm} for m in medicos]
    
    return render_template('agendar.html',
                         especialidades=especialidades,
                         especialidade_selecionada=especialidade_selecionada,
                         medicos_por_especialidade=medicos_por_especialidade,
                         hoje=hoje,
                         max_data=max_data)

@app.route('/api/horarios-disponiveis', methods=['GET'])
def horarios_disponiveis():
    data = request.args.get('data')
    
    if not data:
        return jsonify([])
    
    # Horários possíveis de consulta
    horarios_possiveis = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
    
    try:
        # Converter a data para datetime
        data_consulta = datetime.strptime(data, '%Y-%m-%d').date()
        
        # Buscar consultas existentes na data
        consultas = Consulta.query.filter(
            db.func.date(Consulta.data_hora) == data_consulta
        ).all()
        
        # Remover horários já agendados
        horarios_ocupados = [c.data_hora.strftime('%H:%M') for c in consultas]
        horarios_disponiveis = [h for h in horarios_possiveis if h not in horarios_ocupados]
        
        return jsonify(horarios_disponiveis)
        
    except Exception as e:
        print(f"Erro ao buscar horários: {str(e)}")
        return jsonify([]), 500

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
    if current_user.tipo == 'paciente':
        consultas = Consulta.query.filter_by(
            paciente_id=current_user.paciente.id
        ).order_by(Consulta.data_hora.desc()).all()
    else:
        consultas = Consulta.query.filter_by(
            medico_id=current_user.medico.id
        ).order_by(Consulta.data_hora.desc()).all()
    
    # Adicionar datetime.now() ao contexto
    return render_template('perfil.html', 
                         consultas=consultas,
                         now=datetime.now())

@app.route('/cancelar-consulta/<int:consulta_id>', methods=['POST'])
@login_required
def cancelar_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Verificar se o usuário tem permissão para cancelar
    if current_user.paciente.id != consulta.paciente_id:
        flash('Você não tem permissão para cancelar esta consulta.', 'error')
        return redirect(url_for('perfil'))
    
    # Verificar se a consulta já passou
    if consulta.data_hora < datetime.now():
        flash('Não é possível cancelar consultas passadas.', 'error')
        return redirect(url_for('perfil'))
    
    # Verificar se a consulta já foi cancelada
    if consulta.status == 'cancelada':
        flash('Esta consulta já foi cancelada.', 'error')
        return redirect(url_for('perfil'))
    
    motivo = request.form.get('motivo', '')
    consulta.status = 'cancelada'
    consulta.data_cancelamento = datetime.now()
    consulta.motivo_cancelamento = motivo
    
    try:
        db.session.commit()
        flash('Consulta cancelada com sucesso.', 'success')
    except:
        db.session.rollback()
        flash('Erro ao cancelar consulta.', 'error')
    
    return redirect(url_for('perfil'))

@app.route('/editar-perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    if request.method == 'POST':
        paciente = current_user.paciente
        
        # Atualizar informações básicas
        paciente.nome = request.form.get('nome')
        paciente.telefone = request.form.get('telefone')
        paciente.cpf = request.form.get('cpf')
        paciente.genero = request.form.get('genero')
        paciente.endereco = request.form.get('endereco')
        paciente.cidade = request.form.get('cidade')
        paciente.estado = request.form.get('estado')
        
        # Processar data de nascimento
        data_nasc = request.form.get('data_nascimento')
        if data_nasc:
            paciente.data_nascimento = datetime.strptime(data_nasc, '%Y-%m-%d').date()
        
        # Processar foto de perfil
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                foto.save(filepath)
                paciente.foto_perfil = os.path.join('uploads', filename)
        
        try:
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
        except:
            db.session.rollback()
            flash('Erro ao atualizar perfil.', 'error')
        
        return redirect(url_for('perfil'))
    
    return render_template('editar_perfil.html')

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