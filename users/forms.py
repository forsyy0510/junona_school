from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(message='Имя пользователя обязательно'),
        Length(min=3, max=150, message='Имя пользователя должно быть от 3 до 150 символов')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен'),
        Length(min=6, message='Пароль должен содержать минимум 6 символов')
    ])
    submit = SubmitField('Войти')
    
    def validate_username(self, field):
        """Дополнительная валидация имени пользователя"""
        if field.data and not field.data.strip():
            raise ValidationError('Имя пользователя не может быть пустым') 