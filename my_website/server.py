from flask import Flask, send_from_directory
import pathlib

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    html_path = pathlib.Path(__file__).parent / 'index.html'
    return html_path.read_text(encoding='utf-8')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)