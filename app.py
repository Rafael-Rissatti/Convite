import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pokemon_secret_key'
app.config['SQLALCHEMY_DATABASE_PATH'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rsvp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['SQLALCHEMY_DATABASE_PATH']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    acompanhante = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(10), nullable=False) # 'sim' ou 'nao'

with app.app_context():
    db.create_all()

ADMIN_PASSWORD = 'pika'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    nome = request.form.get('nome')
    acompanhante = request.form.get('acompanhante')
    status = request.form.get('status')
    
    if nome and status:
        novo_rsvp = RSVP(nome=nome, acompanhante=acompanhante, status=status)
        db.session.add(novo_rsvp)
        db.session.commit()
        return jsonify({"status": "success", "message": "Temos que pegar todos! Sua presença foi registrada com sucesso!"})
    return jsonify({"status": "error", "message": "Por favor, preencha todos os campos obrigatórios."}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return render_template('login.html', error="Senha da Equipe Rocket? Tente novamente!")
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    confirmados = RSVP.query.filter_by(status='sim').all()
    ausentes = RSVP.query.filter_by(status='nao').all()
    
    return render_template('admin.html', confirmados=confirmados, ausentes=ausentes)

@app.route('/api/stats')
def stats():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
        
    count_sim = RSVP.query.filter_by(status='sim').count()
    count_nao = RSVP.query.filter_by(status='nao').count()
    
    return jsonify({
        "sim": count_sim,
        "nao": count_nao
    })

@app.route('/admin/delete/<int:id>', methods=['POST'])
def delete_rsvp(id):
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    rsvp = RSVP.query.get_or_404(id)
    db.session.delete(rsvp)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:id>', methods=['POST'])
def edit_rsvp(id):
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    rsvp = RSVP.query.get_or_404(id)
    rsvp.nome = request.form.get('nome')
    rsvp.acompanhante = request.form.get('acompanhante')
    rsvp.status = request.form.get('status')
    
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
