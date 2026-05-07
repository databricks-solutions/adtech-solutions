from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('DATABRICKS_APP_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
