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
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    app.logger.info("File upload initiated.")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        app.logger.info("File saved to: %s", file_path)  # Log the file path
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                return jsonify({'error': 'Unsupported file format'})
            
            session['data'] = df.to_json()
            app.logger.info("File uploaded successfully with columns: %s", df.columns.tolist())
            return jsonify({'success': 'File uploaded successfully', 'columns': df.columns.tolist()})
        except Exception as e:
            app.logger.error("Error processing file: %s", str(e))
            return jsonify({'error': f'Error processing file: {str(e)}'})

@app.route('/manual_input', methods=['POST'])
def manual_input():
    data = request.json
    try:
        # Convert the input data to a pandas DataFrame
        df = pd.DataFrame(data['data'])
        
        # Validate the data types
        for column, dtype in data['dtypes'].items():
            if dtype == 'number':
                df[column] = pd.to_numeric(df[column], errors='coerce')
            elif dtype == 'date':
                df[column] = pd.to_datetime(df[column], errors='coerce')
        
        # Remove rows with NaN values
        df = df.dropna()
        
        # Store the DataFrame in the session
        session['data'] = df.to_json(date_format='iso')
        
        return jsonify({
            'success': 'Data input successfully',
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'shape': df.shape
        })
    except Exception as e:
        return jsonify({'error': f'Error processing data: {str(e)}'})

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'data' not in session:
        return jsonify({'error': 'No data available for analysis'})
    
    analysis_type = request.json.get('analysis_type')
    columns = request.json.get('columns')
    
    df = pd.read_json(session['data'])
    
    if analysis_type == 'descriptive':
        result = df[columns].describe().to_dict()
    elif analysis_type == 't_test':
        if len(columns) != 2:
            return jsonify({'error': 'T-test requires exactly two columns'})
        t_stat, p_value = stats.ttest_ind(df[columns[0]], df[columns[1]])
        result = {'t_statistic': t_stat, 'p_value': p_value}
    elif analysis_type == 'correlation':
        result = df[columns].corr().to_dict()
    elif analysis_type == 'regression':
        if len(columns) != 2:
            return jsonify({'error': 'Regression requires exactly two columns'})
        x = df[columns[0]]
        y = df[columns[1]]
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        result = {'slope': slope, 'intercept': intercept, 'r_value': r_value, 'p_value': p_value, 'std_err': std_err}
    else:
        return jsonify({'error': 'Unsupported analysis type'})
    
    return jsonify({'result': result})

@app.route('/visualize', methods=['POST'])
def visualize():
    if 'data' not in session:
        return jsonify({'error': 'No data available for visualization'})
    
    viz_type = request.json.get('viz_type')
    columns = request.json.get('columns')
    
    df = pd.read_json(session['data'])
    
    plt.figure(figsize=(10, 6))
    
    if viz_type == 'scatter':
        if len(columns) != 2:
            return jsonify({'error': 'Scatter plot requires exactly two columns'})
        plt.scatter(df[columns[0]], df[columns[1]])
        plt.xlabel(columns[0])
        plt.ylabel(columns[1])
    elif viz_type == 'bar':
        df[columns].plot(kind='bar')
    elif viz_type == 'histogram':
        df[columns].hist()
    else:
        return jsonify({'error': 'Unsupported visualization type'})
    
    plt.title(f'{viz_type.capitalize()} Plot')
    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    
    return jsonify({'plot': plot_url})

if __name__ == '__main__':
    app.run(debug=True)
