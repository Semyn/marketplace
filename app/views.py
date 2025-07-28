from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from . import db, bcrypt
from .models import User, Shop, Product, Comment
from .forms import (LoginForm, RegisterForm, ShopForm, 
                    ProductForm, CommentForm, SearchForm)
import os

views = Blueprint('views', __name__)

# Конфигурация загрузки файлов
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'app/static/uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Главная страница - популярные товары
@views.route('/')
def index():
    # Получаем 10 последних товаров (в реальном приложении нужно сортировать по популярности)
    products = Product.query.order_by(Product.id.desc()).limit(10).all()
    return render_template('index.html', products=products)

# Страница входа
@views.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Проверяем пароль с помощью bcrypt
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('views.index'))
        else:
            flash('Неверный email или пароль', 'danger')
    return render_template('login.html', form=form)

@views.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))

    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            # Проверяем, не занят ли email
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Этот email уже зарегистрирован!', 'danger')
                return redirect(url_for('views.register'))

            # Создаем нового пользователя
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = User(
                email=form.email.data,
                password_hash=hashed_password
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('views.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')
            return redirect(url_for('views.register'))
    
    return render_template('register.html', form=form)

# Выход из системы
@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.index'))

# Создание магазина
@views.route('/shop/create', methods=['GET', 'POST'])
@login_required
def create_shop():
    form = ShopForm()
    if form.validate_on_submit():
        shop = Shop(
            name=form.name.data,
            owner=current_user
        )
        db.session.add(shop)
        db.session.commit()
        flash('Ваш магазин успешно создан!', 'success')
        return redirect(url_for('views.manage_shop', shop_id=shop.id))
    return render_template('create_shop.html', form=form)

# Управление магазином
@views.route('/shop/manage/<int:shop_id>')
@login_required
def manage_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    
    # Проверяем, что текущий пользователь - владелец магазина
    if shop.owner != current_user:
        abort(403)
    
    return render_template('manage_shop.html', shop=shop)

# Просмотр магазина
@views.route('/shop/<int:shop_id>')
def shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    return render_template('shop.html', shop=shop)

@views.route('/shop/<int:shop_id>/add', methods=['GET', 'POST'])
@login_required
def add_product(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    
    if shop.owner != current_user:
        abort(403)
    
    form = ProductForm()
    
    if form.validate_on_submit():
        try:
            # Обработка загрузки изображения
            image_filename = None
            if form.image.data:
                image = form.image.data
                image_filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.root_path, 'static/uploads', image_filename)
                image.save(image_path)
            
            # Создание товара
            product = Product(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                image=image_filename,  # Сохраняем только имя файла
                shop_id=shop.id
            )
            
            db.session.add(product)
            db.session.commit()
            flash('Товар успешно добавлен!', 'success')
            return redirect(url_for('views.manage_shop', shop_id=shop.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении товара: {str(e)}', 'danger')
    
    return render_template('add_product.html', form=form, shop=shop)

# Страница товара
@views.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product(product_id):
    product = Product.query.get_or_404(product_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Для добавления комментария необходимо войти в систему', 'warning')
            return redirect(url_for('views.login'))
        
        comment = Comment(
            text=form.text.data,
            author=current_user,
            product=product
        )
        db.session.add(comment)
        db.session.commit()
        flash('Ваш комментарий добавлен!', 'success')
        return redirect(url_for('views.product', product_id=product.id))
    
    return render_template('product.html', product=product, form=form)

# Удаление товара
@views.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    shop_id = product.shop.id
    
    # Проверка прав доступа
    if product.shop.owner != current_user:
        abort(403)
    
    # Удаляем изображение товара, если оно есть
    if product.image:
        try:
            os.remove(os.path.join(UPLOAD_FOLDER, product.image))
        except OSError:
            pass
    
    # Удаляем все комментарии к товару
    Comment.query.filter_by(product_id=product.id).delete()
    
    # Удаляем сам товар
    db.session.delete(product)
    db.session.commit()
    flash('Товар успешно удален!', 'success')
    return redirect(url_for('views.manage_shop', shop_id=shop_id))

# Поиск товаров
@views.route('/search')
def search():
    query = request.args.get('q', '')
    
    if query:
        products = Product.query.filter(
            Product.title.ilike(f'%{query}%') | 
            Product.description.ilike(f'%{query}%')
        ).all()
    else:
        products = []
    
    return render_template('search.html', products=products, query=query)

# Личный кабинет пользователя
@views.route('/account')
@login_required
def account():
    shops = current_user.shops
    return render_template('account.html', shops=shops)

# Редактирование профиля
@views.route('/account/edit', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash('Ваш профиль успешно обновлен!', 'success')
        return redirect(url_for('views.account'))
    elif request.method == 'GET':
        form.email.data = current_user.email
    
    return render_template('edit_account.html', form=form)

# Изменение пароля
@views.route('/account/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password_hash, form.old_password.data):
            current_user.password_hash = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Ваш пароль успешно изменен!', 'success')
            return redirect(url_for('views.account'))
        else:
            flash('Неверный текущий пароль', 'danger')
    
    return render_template('change_password.html', form=form)