import os
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from sklearn.linear_model import LinearRegression
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Required for flashing messages

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def process_csv(file_path):
    try:
        df = pd.read_csv(file_path, parse_dates=['Date'])
        df['Conversion Rate'] = df['Conversion Rate'].str.rstrip('%').astype('float') / 100.0
        df = df.sort_values('Date')
        monthly_data = df.groupby(pd.Grouper(key='Date', freq='ME'))
        
        monthly_reports = monthly_data.agg({
            'Clicks': 'sum',
            'Actions': 'sum',
            'Sale Amount': 'sum',
            'Earnings': 'sum',
            'EPA': 'mean',
            'EPC': 'mean',
            'Conversion Rate': 'mean',
            'AOV': 'mean'
        })
        
        return monthly_reports
    except Exception as e:
        logging.error(f"Error in process_csv: {str(e)}")
        return pd.DataFrame()  # Return an empty DataFrame if there's an error

def create_graph(df, column, projection=None):
    fig = px.line(df, x=df.index, y=column, title=f'{column} Over Time')
    
    if projection is not None:
        proj_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=6, freq='M')
        fig.add_trace(go.Scatter(x=proj_dates, y=projection, mode='lines', name='Projection', line=dict(dash='dash')))
    
    img = BytesIO()
    fig.write_image(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def project_future(df, column, periods=6):
    X = np.arange(len(df)).reshape(-1, 1)
    y = df[column].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    future_X = np.arange(len(df), len(df) + periods).reshape(-1, 1)
    projection = model.predict(future_X)
    
    return projection

@app.route('/', methods=['GET', 'POST'])
def index():
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'impact_report.csv')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            file.save(file_path)
            flash('File successfully updated')
            return redirect(url_for('index'))

    monthly_reports = pd.DataFrame()
    overall_performance = {}
    graphs = {}
    projection_data = pd.DataFrame()
    growth_table = pd.DataFrame()  # New DataFrame for growth table

    if os.path.exists(file_path):
        try:
            logging.debug(f"Attempting to process CSV file: {file_path}")
            monthly_reports = process_csv(file_path)
            logging.debug(f"CSV processed successfully. Shape of monthly_reports: {monthly_reports.shape}")
            
            earnings_projection = project_future(monthly_reports, 'Earnings')
            clicks_projection = project_future(monthly_reports, 'Clicks')
            
            graphs = {
                'Earnings': create_graph(monthly_reports, 'Earnings', earnings_projection),
                'Clicks': create_graph(monthly_reports, 'Clicks', clicks_projection),
                'Conversion_Rate': create_graph(monthly_reports, 'Conversion Rate')
            }
            
            overall_performance = monthly_reports.sum().to_dict()  # Convert to dictionary
            
            projection_data = pd.DataFrame({
                'Month': pd.date_range(start=monthly_reports.index[-1] + pd.Timedelta(days=1), periods=6, freq='M'),
                'Projected Earnings': earnings_projection,
                'Projected Clicks': clicks_projection
            })
            
            # Calculate growth rates
            growth_table = monthly_reports.pct_change()
            growth_table = growth_table.multiply(100).round(2)  # Convert to percentage and round to 2 decimal places
            
        except Exception as e:
            logging.error(f"An error occurred while processing the CSV file: {str(e)}")
            flash(f"An error occurred while processing the CSV file: {str(e)}")
    else:
        logging.warning(f"CSV file not found: {file_path}")
        flash("No CSV file found. Please upload a file.")

    logging.debug(f"Final shape of monthly_reports: {monthly_reports.shape}")
    logging.debug(f"Type of monthly_reports: {type(monthly_reports)}")
    logging.debug(f"Overall performance: {overall_performance}")

    return render_template('report.html', 
                           monthly_reports=monthly_reports, 
                           overall_performance=overall_performance,
                           graphs=graphs,
                           projection_data=projection_data,
                           growth_table=growth_table)  # Add growth_table to the template context

if __name__ == '__main__':
    app.run(debug=True)
