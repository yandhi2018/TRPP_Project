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
    """Модель пользователя системы"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True)

    def set_password(self, password):
        """Установка хеша пароля пользователя
        
        Args:
            password (str): Пароль в открытом виде
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля пользователя
        
        Args:
            password (str): Пароль для проверки
            
        Returns:
            bool: True если пароль верный, иначе False
        """
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    """Модель поста/публикации на форуме"""
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
    """Модель изображения, прикрепленного к посту"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, default=0)
    size = db.Column(db.String(20), default='medium')
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    """Модель комментария к посту"""
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя для Flask-Login
    
    Args:
        user_id (int): ID пользователя
        
    Returns:
        User: Объект пользователя или None если не найден
    """
    return User.query.get(int(user_id))

def allowed_file(filename):
    """Проверка разрешенных расширений файлов
    
    Args:
        filename (str): Имя файла
        
    Returns:
        bool: True если расширение разрешено, иначе False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Главная страница с последними постами
    
    Returns:
        Response: HTML-страница с пагинированным списком постов
    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    """Страница просмотра поста с комментариями
    
    Args:
        post_id (int): ID поста
        
    Returns:
        Response: HTML-страница с деталями поста
    """
    post = Post.query.get_or_404(post_id)
    post.views = post.views + 1 if post.views else 1
    db.session.commit()
    return render_template('post_detail.html', post=post)

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Добавление комментария к посту
    
    Args:
        post_id (int): ID поста
        
    Returns:
        Response: Перенаправление на страницу поста
    """
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
    """Удаление комментария
    
    Args:
        comment_id (int): ID комментария
        
    Returns:
        Response: Перенаправление на страницу поста
    """
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
    """Страница профиля пользователя с его постами
    
    Returns:
        Response: HTML-страница профиля
    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('profile.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя
    
    Returns:
        Response: Форма регистрации или перенаправление после успешной регистрации
    """
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
    """Аутентификация пользователя
    
    Returns:
        Response: Форма входа или перенаправление после успешного входа
    """
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
    """Выход пользователя из системы
    
    Returns:
        Response: Перенаправление на главную страницу
    """
    logout_user()
    return redirect(url_for('index'))

@app.route('/forum')
def forum():
    """Страница форума с фильтрацией и поиском
    
    Returns:
        Response: HTML-страница форума
    """
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
    """Страница торговой площадки
    
    Returns:
        Response: HTML-страница с товарами
    """
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

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    """Создание нового поста
    
    Returns:
        Response: Форма создания поста или перенаправление после создания
    """
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        section = request.form.get('section')
        price = request.form.get('price')
        
        if not title or not content:
            flash('Заголовок и содержание поста обязательны', 'error')
            return redirect(url_for('create_post'))
        
        try:
            price_value = float(price) if price else None
        except ValueError:
            flash('Некорректное значение цены', 'error')
            return redirect(url_for('create_post'))
        
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
    
    section = request.args.get('section')
    show_price = request.args.get('price') == '1'
    return render_template('create_post.html', section=section, show_price=show_price)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Редактирование существующего поста
    
    Args:
        post_id (int): ID редактируемого поста
        
    Returns:
        Response: Форма редактирования или перенаправление после сохранения
    """
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.section = request.form['section']
        
        price = request.form.get('price')
        try:
            post.price = float(price) if price else None
        except ValueError:
            flash('Некорректное значение цены', 'error')
            return redirect(url_for('edit_post', post_id=post.id))
        
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
    
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Удаление поста
    
    Args:
        post_id (int): ID удаляемого поста
        
    Returns:
        Response: Перенаправление на форум
    """
    post = Post.query.get_or_404(post_id)
    
    if post.user_id != current_user.id:
        abort(403)
    
    try:
        for image in post.images:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            except OSError:
                pass
        
        db.session.delete(post)
        db.session.commit()
        
        flash('Пост успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении поста: {str(e)}', 'error')
    
    return redirect(url_for('forum'))

def create_test_data():
    """Создание тестовых данных в БД"""
    with app.app_context():
        try:
            if User.query.first() is None:
                admin = User(username="admin")
                admin.set_password("admin123")
                
                gamer = User(username="gamer1")
                gamer.set_password("qwerty")
                
                streamer = User(username="streamer")
                streamer.set_password("123456")
                
                db.session.add_all([admin, gamer, streamer])
                db.session.commit()

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
            
def main():
    """Запуск приложения."""
    with app.app_context():
        db.create_all()
    app.run(debug=True)


if __name__ == '__main__':
    main()