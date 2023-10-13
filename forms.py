from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, URL, Email, Length


class RegisterForm(FlaskForm):
    username = StringField("User Name", validators=[
                           DataRequired("Enter User Name."), Length(min=2, max=30, message="Name must be 2-30 characters long")])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(
        min=2, max=30, message="Password must me at least 8 characters long")])
    submit = SubmitField("Register")


class LoginForm (FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class CreateChannelForm(FlaskForm):
    channel_name = StringField("Channel Name", validators=[DataRequired()])
    description = StringField("About This Channel", validators=[DataRequired()])
    submit = SubmitField("Create")
