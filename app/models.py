from . import db
from flask_login import UserMixin
from datetime import datetime
from . import bcrypt

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Храним хеш, а не пароль
    
    shops = db.relationship('Shop', backref='owner', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

    # Метод для установки пароля (автоматически хеширует)
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Метод для проверки пароля
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    # Методы для Flask-Login
    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False


# Модель магазина
class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор
    name = db.Column(db.String(100), unique=True, nullable=False)  # Название магазина (уникальное)
    
    # Внешний ключ для связи с владельцем (пользователем)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Связь: один магазин может содержать много товаров
    products = db.relationship('Product', backref='shop', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100))  # Добавляем поле для хранения имени файла изображения
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    comments = db.relationship('Comment', backref='product', lazy=True)

    def __repr__(self):
        return f"Product('{self.title}', '{self.price}')"

# Модель комментария
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор
    text = db.Column(db.Text, nullable=False)  # Текст комментария
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания (автоматически)
    
    # Внешний ключ для связи с пользователем
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Внешний ключ для связи с товаром
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)