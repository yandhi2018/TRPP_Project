# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
app.config['SECRET_KEY'] = 'ваш_секретный_ключ'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    section = db.Column(db.String(20))
    price = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('Image', backref='post', lazy=True, cascade='all, delete-orphan')

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, default=0)
    size = db.Column(db.String(20), default='medium')
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    post.views = post.views + 1 if post.views else 1
    db.session.commit()
    return render_template('post_detail.html', post=post)

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    text = request.form.get('text')
    
    if not text:
        flash('Комментарий не может быть пустым', 'error')
        return redirect(url_for('post_detail', post_id=post_id))
    
    comment = Comment(
        text=text,
        user_id=current_user.id,
        post_id=post.id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Комментарий добавлен', 'success')
    return redirect(url_for('post_detail', post_id=post_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Комментарий удалён', 'success')
    return redirect(url_for('post_detail', post_id=comment.post_id))

@app.route('/profile')
@login_required
def profile():
    page = request.args.get('page', 1, type=int)
    # Используем запрос вместо отношения
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('profile.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято!', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация успешна!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forum')
def forum():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    section_filter = request.args.get('section_filter', '')
    
    query = Post.query.filter(Post.section != 'marketplace')
    
    if search_query:
        query = query.filter(
            (Post.title.ilike(f'%{search_query}%')) | 
            (Post.content.ilike(f'%{search_query}%'))
        )
    
    if section_filter:
        query = query.filter_by(section=section_filter)
    
    posts = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('forum.html', posts=posts, search_query=search_query, section_filter=section_filter)

@app.route('/marketplace')
def marketplace():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    price_filter = request.args.get('price_filter', '')
    
    query = Post.query.filter_by(section='marketplace').options(
        db.joinedload(Post.comments),
        db.joinedload(Post.images)
    )
    
    if search_query:
        query = query.filter(
            (Post.title.ilike(f'%{search_query}%')) 
        )
    if price_filter:
        if price_filter == '0-1000':
            query = query.filter(Post.price <= 1000)
        elif price_filter == '1000-5000':
            query = query.filter(Post.price.between(1000, 5000))
        elif price_filter == '5000+':
            query = query.filter(Post.price >= 5000)
    
    items = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('marketplace.html', items=items, search_query=search_query, price_filter=price_filter)

# Создание поста
@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        # Получаем данные из формы
        title = request.form.get('title')
        content = request.form.get('content')
        section = request.form.get('section')
        price = request.form.get('price')
        
        # Валидация обязательных полей
        if not title or not content:
            flash('Заголовок и содержание поста обязательны', 'error')
            return redirect(url_for('create_post'))
        
        # Преобразуем цену в число, если она указана
        try:
            price_value = float(price) if price else None
        except ValueError:
            flash('Некорректное значение цены', 'error')
            return redirect(url_for('create_post'))
        
        # Создаем новый пост
        new_post = Post(
            title=title,
            content=content,
            section=section,
            price=price_value,
            user_id=current_user.id
        )
        
        try:
            db.session.add(new_post)
            db.session.commit()
            
            # Обработка изображений
            if 'images' in request.files:
                for file in request.files.getlist('images'):
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        img = Image(
                            filename=filename,
                            post_id=new_post.id
                        )
                        db.session.add(img)
                
                db.session.commit()
            
            flash('Пост успешно создан!', 'success')
            return redirect(url_for('post_detail', post_id=new_post.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании поста: {str(e)}', 'error')
            return redirect(url_for('create_post'))
    
    # GET запрос - отображаем форму
    section = request.args.get('section')
    show_price = request.args.get('price') == '1'
    return render_template('create_post.html', section=section, show_price=show_price)

# Редактирование поста
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Проверка прав на редактирование
    if post.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        # Обновляем данные поста
        post.title = request.form['title']
        post.content = request.form['content']
        post.section = request.form['section']
        
        # Обработка цены
        price = request.form.get('price')
        try:
            post.price = float(price) if price else None
        except ValueError:
            flash('Некорректное значение цены', 'error')
            return redirect(url_for('edit_post', post_id=post.id))
        
        # Обработка новых изображений
        for i, file in enumerate(request.files.getlist('new_images')):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                image = Image(
                    filename=filename,
                    order=len(post.images) + i,
                    post_id=post.id
                )
                db.session.add(image)
        
        db.session.commit()
        flash('Пост успешно обновлен!', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    
    # GET запрос - отображаем форму редактирования
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        abort(403)
    
    try:
        # Удаляем изображения
        for image in post.images:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            except OSError:
                pass
        
        # Удаляем сам пост (комментарии удалятся каскадно)
        db.session.delete(post)
        db.session.commit()
        
        flash('Пост успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении поста: {str(e)}', 'error')
    
    return redirect(url_for('forum'))

def create_test_data():
    with app.app_context():
        try:
            if User.query.first() is None:
                # Создаем тестовых пользователей
                admin = User(username="admin")
                admin.set_password("admin123")
                
                gamer = User(username="gamer1")
                gamer.set_password("qwerty")
                
                streamer = User(username="streamer")
                streamer.set_password("123456")
                
                db.session.add_all([admin, gamer, streamer])
                db.session.commit()

                # Создаем тестовые посты
                post1 = Post(
                    title="Лучшие сборки в Dota 2",
                    content="Детальные гайды по сборкам для разных героев",
                    section="guides",
                    user_id=admin.id,
                    created_at=datetime(2023, 10, 1)
                )
                
                post2 = Post(
                    title="Продается скин CS2",
                    content="Нож Butterfly | Фейд (Factory New) - 1500$",
                    section="marketplace",
                    price=1500.00,
                    user_id=gamer.id,
                    created_at=datetime(2023, 10, 2)
                )
                
                post3 = Post(
                    title="Обсуждение нового патча",
                    content="Какие изменения вас больше всего заинтересовали?",
                    section="discussion",
                    user_id=streamer.id,
                    created_at=datetime(2023, 10, 3)
                )
                
                db.session.add_all([post1, post2, post3])
                db.session.commit()

                # # Создаем тестовые изображения
                # img1 = Image(
                #     filename="test_image1.jpg",
                #     post_id=post1.id
                # )
                # img2 = Image(
                #     filename="test_image2.jpg",
                #     post_id=post2.id
                # )
                
                # db.session.add_all([img1, img2])
                # db.session.commit()

                # Создаем тестовые комментарии
                comment1 = Comment(
                    text="Отличный гайд, спасибо!",
                    user_id=gamer.id,
                    post_id=post1.id,
                    created_at=datetime(2023, 10, 1, 12, 30)
                )
                
                comment2 = Comment(
                    text="Сколько просите за нож?",
                    user_id=streamer.id,
                    post_id=post2.id,
                    created_at=datetime(2023, 10, 2, 14, 15)
                )
                
                db.session.add_all([comment1, comment2])
                db.session.commit()
                
                print("Тестовые данные успешно созданы!")
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при создании тестовых данных: {str(e)}")
            
if __name__ == '__main__':
    with app.app_context():
        # Удаляем все таблицы (только для разработки!)
        # db.drop_all()
        # Создаем новые таблицы
        db.create_all()
        # Заполняем тестовыми данными
        # create_test_data()
    app.run(debug=True)