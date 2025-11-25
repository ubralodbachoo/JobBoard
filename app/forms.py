from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField('სახელი', validators=[
        DataRequired(message='სახელი აუცილებელია'),
        Length(min=3, max=64, message='სახელი უნდა იყოს 3-64 სიმბოლო')
    ])
    email = StringField('ელფოსტა', validators=[
        DataRequired(message='ელფოსტა აუცილებელია'),
        Email(message='არასწორი ელფოსტის ფორმატი')
    ])
    password = PasswordField('პაროლი', validators=[
        DataRequired(message='პაროლი აუცილებელია'),
        Length(min=6, message='პაროლი უნდა იყოს მინიმუმ 6 სიმბოლო')
    ])
    confirm_password = PasswordField('გაიმეორეთ პაროლი', validators=[
        DataRequired(message='გაიმეორეთ პაროლი'),
        EqualTo('password', message='პაროლები არ ემთხვევა')
    ])
    submit = SubmitField('რეგისტრაცია')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('ეს სახელი უკვე გამოყენებულია. გთხოვთ აირჩიოთ სხვა.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('ეს ელფოსტა უკვე დარეგისტრირებულია.')


class LoginForm(FlaskForm):
    email = StringField('ელფოსტა', validators=[
        DataRequired(message='ელფოსტა აუცილებელია'),
        Email(message='არასწორი ელფოსტის ფორმატი')
    ])
    password = PasswordField('პაროლი', validators=[
        DataRequired(message='პაროლი აუცილებელია')
    ])
    remember_me = BooleanField('დამახსოვრება')
    submit = SubmitField('შესვლა')


class JobForm(FlaskForm):
    title = StringField('სათაური', validators=[
        DataRequired(message='სათაური აუცილებელია'),
        Length(max=200, message='სათაური არ უნდა აღემატებოდეს 200 სიმბოლოს')
    ])
    short_description = TextAreaField('მოკლე აღწერა', validators=[
        DataRequired(message='მოკლე აღწერა აუცილებელია'),
        Length(max=300, message='მოკლე აღწერა არ უნდა აღემატებოდეს 300 სიმბოლოს')
    ])
    full_description = TextAreaField('სრული აღწერა', validators=[
        DataRequired(message='სრული აღწერა აუცილებელია')
    ])
    company = StringField('კომპანია', validators=[
        DataRequired(message='კომპანიის სახელი აუცილებელია'),
        Length(max=100, message='კომპანიის სახელი არ უნდა აღემატებოდეს 100 სიმბოლოს')
    ])
    salary = StringField('ხელფასი', validators=[
        Length(max=100, message='ხელფასი არ უნდა აღემატებოდეს 100 სიმბოლოს')
    ])
    location = StringField('ლოკაცია', validators=[
        DataRequired(message='ლოკაცია აუცილებელია'),
        Length(max=100, message='ლოკაცია არ უნდა აღემატებოდეს 100 სიმბოლოს')
    ])
    category = SelectField('კატეგორია', choices=[
        ('IT', 'IT'),
        ('Design', 'დიზაინი'),
        ('Marketing', 'მარკეტინგი'),
        ('Sales', 'გაყიდვები'),
        ('Management', 'მენეჯმენტი'),
        ('Finance', 'ფინანსები'),
        ('Other', 'სხვა')
    ], validators=[DataRequired(message='კატეგორია აუცილებელია')])
    submit = SubmitField('დამატება')


class ProfileUpdateForm(FlaskForm):
    username = StringField('სახელი', validators=[
        DataRequired(message='სახელი აუცილებელია'),
        Length(min=3, max=64, message='სახელი უნდა იყოს 3-64 სიმბოლო')
    ])
    email = StringField('ელფოსტა', validators=[
        DataRequired(message='ელფოსტა აუცილებელია'),
        Email(message='არასწორი ელფოსტის ფორმატი')
    ])
    profile_picture = FileField('პროფილის სურათი', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'მხოლოდ სურათები დაშვებულია!')
    ])
    submit = SubmitField('განახლება')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('ეს ელფოსტა უკვე დარეგისტრირებულია.')


class DeleteAccountForm(FlaskForm):
    password = PasswordField('პაროლი', validators=[
        DataRequired(message='პაროლი აუცილებელია დასადასტურებლად')
    ])
    confirm_delete = StringField('დასადასტურებლად ჩაწერეთ "DELETE"', validators=[
        DataRequired(message='გთხოვთ ჩაწეროთ DELETE')
    ])
    submit = SubmitField('ანგარიშის წაშლა')

