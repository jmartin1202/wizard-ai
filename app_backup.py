from flask import Flask, render_template
from config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    print(' Starting AI Chatbot...')
    print(' Server will be available at: http://localhost:8080')
    app.run(debug=True, host='0.0.0.0', port=8080)
