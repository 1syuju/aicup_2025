from flask import Flask, url_for
from flask_cors import CORS

app = Flask(__name__)

@app.route('/')
def sign_in():
    return "hello"

@app.route('/user/<username>')
def get_user(username):
    return ":" + username

@app.route('/age')
def userage():
    age = 3
    return 'i am ' + age + ' years old'

if __name__ == '__main__':
    app.debug = True # in formal environment, here wont be True
    app.run()