from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    PasswordField, 
    TextAreaField, 
    FloatField, 
    SubmitField,
    BooleanField,
    FileField
)
from wtforms.validators import (
    DataRequired, 
    Email, 
    Length, 
    ValidationError,
    EqualTo,
    NumberRange
)
from flask_wtf.file import FileAllowed
from .models import User, Shop

class BaseForm(FlaskForm):
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Этот email уже зарегистрирован')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Поле email обязательно для заполнения"),
        Email(message="Введите корректный email адрес")
    ], render_kw={
        "placeholder": "example@example.com",
        "class": "form-control"
    })

    password = PasswordField('Пароль', validators=[
        DataRequired(message="Введите пароль")
    ], render_kw={
        "placeholder": "Введите ваш пароль",
        "class": "form-control"
    })

    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти', render_kw={
        "class": "btn btn-primary"
    })

class RegisterForm(BaseForm):
    email = StringField('Email', validators=[
        DataRequired(message="Поле email обязательно для заполнения"),
        Email(message="Введите корректный email адрес"),
        Length(max=100, message="Email не должен превышать 100 символов")
    ], render_kw={
        "placeholder": "example@example.com",
        "class": "form-control"
    })

    password = PasswordField('Пароль', validators=[
        DataRequired(message="Введите пароль"),
        Length(min=8, message="Пароль должен быть не менее 8 символов")
    ], render_kw={
        "placeholder": "Придумайте пароль",
        "class": "form-control"
    })

    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(message="Подтвердите пароль"),
        EqualTo('password', message="Пароли должны совпадать")
    ], render_kw={
        "placeholder": "Повторите пароль",
        "class": "form-control"
    })

    submit = SubmitField('Зарегистрироваться', render_kw={
        "class": "btn btn-primary"
    })

class ShopForm(BaseForm):
    name = StringField('Название магазина', validators=[
        DataRequired(message="Введите название магазина"),
        Length(min=3, max=100, message="Название должно быть от 3 до 100 символов")
    ], render_kw={
        "placeholder": "Мой магазин",
        "class": "form-control"
    })

    # Новое поле для изображения магазина
    image = FileField('Изображение магазина', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения (jpg, jpeg, png)')
    ], render_kw={
        "class": "form-control"
    })

    submit = SubmitField('Сохранить', render_kw={
        "class": "btn btn-primary"
    })

    def validate_name(self, field):
        shop = Shop.query.filter_by(name=field.data).first()
        if shop and (not hasattr(self, 'shop') or shop.id != self.shop.id ):
            raise ValidationError('Магазин с таким названием уже существует')

class ProductForm(FlaskForm):
    title = StringField('Название товара', validators=[
        DataRequired(message="Введите название товара"),
        Length(min=3, max=100, message="Название должно быть от 3 до 100 символов")
    ], render_kw={
        "class": "form-control"
    })
    
    description = TextAreaField('Описание товара', validators=[
        DataRequired(message="Введите описание товара"),
        Length(min=10, max=2000, message="Описание должно быть от 10 до 2000 символов")
    ], render_kw={
        "class": "form-control",
        "rows": 5
    })
    
    price = FloatField('Цена', validators=[
        DataRequired(message="Укажите цену товара в рублях"),
        NumberRange(min=0.01, message="Цена должна быть больше 0")
    ], render_kw={
        "class": "form-control"
    })
    
    image = FileField('Изображение товара', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения (jpg, jpeg, png)')
    ], render_kw={
        "class": "form-control"
    })
    
    submit = SubmitField('Сохранить', render_kw={
        "class": "btn btn-primary"
    })

class CommentForm(FlaskForm):
    text = TextAreaField('Отзыв', validators=[
        DataRequired(message="Отзыв не может быть пустым"),
        Length(min=10, max=500, message="Отзыв должен быть от 10 до 500 символов")
    ], render_kw={
        "placeholder": "Ваш отзыв о товаре...",
        "class": "form-control",
        "rows": 3
    })

    submit = SubmitField('Отправить', render_kw={
        "class": "btn btn-primary"
    })

class EditProfileForm(BaseForm):
    email = StringField('Email', validators=[
        DataRequired(message="Поле email обязательно для заполнения"),
        Email(message="Введите корректный email адрес"),
        Length(max=100, message="Email не должен превышать 100 символов")
    ], render_kw={
        "placeholder": "example@example.com",
        "class": "form-control"
    })

    submit = SubmitField('Обновить профиль', render_kw={
        "class": "btn btn-primary"
    })

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Текущий пароль', validators=[
        DataRequired(message="Введите текущий пароль")
    ], render_kw={
        "placeholder": "Ваш текущий пароль",
        "class": "form-control"
    })

    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(message="Введите новый пароль"),
        Length(min=8, message="Пароль должен быть не менее 8 символов")
    ], render_kw={
        "placeholder": "Новый пароль",
        "class": "form-control"
    })

    confirm_password = PasswordField('Подтверждение пароля', validators=[
        DataRequired(message="Подтвердите новый пароль"),
        EqualTo('new_password', message="Пароли должны совпадать")
    ], render_kw={
        "placeholder": "Повторите новый пароль",
        "class": "form-control"
    })

    submit = SubmitField('Изменить пароль', render_kw={
        "class": "btn btn-primary"
    })

class SearchForm(FlaskForm):
    query = StringField('Поиск', validators=[
        DataRequired(message="Введите поисковый запрос")
    ], render_kw={
        "placeholder": "Поиск товаров...",
        "class": "form-control"
    })

    submit = SubmitField('Найти', render_kw={
        "class": "btn btn-outline-success"
    })