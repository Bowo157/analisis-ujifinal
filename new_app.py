import sys
import subprocess

# Check and install required packages
required_packages = ['flask', 'pandas', 'numpy', 'scipy', 'matplotlib']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

from flask import Flask, render_template, request, session, jsonify
from werkzeug.utils import secure_filename
import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key in production

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('new_index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file yang diunggah'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Tidak ada file yang dipilih'})
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                return jsonify({'error': 'Format file tidak didukung'})
            
            session['data'] = df.to_json(date_format='iso')
            return jsonify({'success': 'File berhasil diunggah', 'columns': df.columns.tolist()})
        except Exception as e:
            return jsonify({'error': f'Terjadi kesalahan saat memproses file: {str(e)}'})

@app.route('/manual_input', methods=['POST'])
def manual_input():
    data = request.json
    try:
        df = pd.DataFrame(data['data'])
        
        for column, dtype in data['dtypes'].items():
            if dtype == 'number':
                df[column] = pd.to_numeric(df[column], errors='coerce')
            elif dtype == 'date':
                df[column] = pd.to_datetime(df[column], errors='coerce')
        
        df = df.dropna()
        
        session['data'] = df.to_json(date_format='iso')
        
        return jsonify({
            'success': 'Data berhasil diinput',
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'shape': df.shape
        })
    except Exception as e:
        return jsonify({'error': f'Terjadi kesalahan saat memproses data: {str(e)}'})

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'data' not in session:
        return jsonify({'error': 'Tidak ada data tersedia untuk analisis'})
    
    analysis_type = request.json.get('analysis_type')
    columns = request.json.get('columns')
    
    df = pd.read_json(session['data'])
    
    if analysis_type == 'descriptive':
        result = df[columns].describe().to_dict()
    elif analysis_type == 't_test':
        if len(columns) != 2:
            return jsonify({'error': 'Uji T membutuhkan tepat dua kolom'})
        t_stat, p_value = stats.ttest_ind(df[columns[0]], df[columns[1]])
        result = {'t_statistic': t_stat, 'p_value': p_value}
    elif analysis_type == 'correlation':
        result = df[columns].corr().to_dict()
    elif analysis_type == 'regression':
        if len(columns) != 2:
            return jsonify({'error': 'Regresi membutuhkan tepat dua kolom'})
        x = df[columns[0]]
        y = df[columns[1]]
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        result = {'slope': slope, 'intercept': intercept, 'r_value': r_value, 'p_value': p_value, 'std_err': std_err}
    else:
        return jsonify({'error': 'Jenis analisis tidak didukung'})
    
    return jsonify({'result': result})

@app.route('/visualize', methods=['POST'])
def visualize():
    if 'data' not in session:
        return jsonify({'error': 'Tidak ada data tersedia untuk visualisasi'})
    
    viz_type = request.json.get('viz_type')
    columns = request.json.get('columns')
    
    df = pd.read_json(session['data'])
    
    plt.figure(figsize=(10, 6))
    
    if viz_type == 'scatter':
        if len(columns) != 2:
            return jsonify({'error': 'Diagram pencar membutuhkan tepat dua kolom'})
        plt.scatter(df[columns[0]], df[columns[1]])
        plt.xlabel(columns[0])
        plt.ylabel(columns[1])
    elif viz_type == 'bar':
        df[columns].plot(kind='bar')
    elif viz_type == 'histogram':
        df[columns].hist()
    else:
        return jsonify({'error': 'Jenis visualisasi tidak didukung'})
    
    plt.title(f'Visualisasi {viz_type.capitalize()}')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    
    return jsonify({'plot': plot_url})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)