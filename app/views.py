from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from . import db, bcrypt
from .models import User, Shop, Product, Comment
from .forms import (LoginForm, RegisterForm, ShopForm, 
                    ProductForm, CommentForm, SearchForm,EditProfileForm,ChangePasswordForm)
import os
import uuid

views = Blueprint('views', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/')
def index():
    products = Product.query.order_by(Product.id.desc()).limit(10).all()
    return render_template('index.html', products=products)

@views.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
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
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Этот email уже зарегистрирован!', 'danger')
                return redirect(url_for('views.register'))

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

@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.index'))

@views.route('/shop/create', methods=['GET', 'POST'])
@login_required
def create_shop():
    form = ShopForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image = form.image.data
            unique_filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, unique_filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
            image_filename = unique_filename

        shop = Shop(
            name=form.name.data,
            owner=current_user,
            image=image_filename
        )
        db.session.add(shop)
        db.session.commit()
        flash('Ваш магазин успешно создан!', 'success')
        return redirect(url_for('views.manage_shop', shop_id=shop.id))
    return render_template('create_shop.html', form=form)

@views.route('/shop/manage/<int:shop_id>')
@login_required
def manage_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    
    if shop.owner != current_user:
        abort(403)
    
    return render_template('manage_shop.html', shop=shop)

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
            image_filename = None
            # Исправлено: проверяем, было ли загружено изображение
            if form.image.data:
                image = form.image.data
                # Генерируем уникальное имя файла
                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
                image_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, unique_filename)
                # Создаем директорию, если ее нет
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                image_filename = unique_filename
            
            # Создаем товар с изображением
            product = Product(
                title=form.title.data,
                description=form.description.data,
                price=form.price.data,
                image=image_filename,  # Сохраняем имя файла изображения
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

@views.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    shop_id = product.shop.id
    
    if product.shop.owner != current_user:
        abort(403)
    
    if product.image:
        try:
            image_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, product.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except OSError as e:
            flash(f'Ошибка при удалении изображения: {str(e)}', 'warning')
    
    Comment.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Товар успешно удален!', 'success')
    return redirect(url_for('views.manage_shop', shop_id=shop_id))

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
    
    return render_template('search.html', results=products, query=query)

@views.route('/account')
@login_required
def account():
    shops = current_user.shops
    return render_template('account.html', shops=shops)

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