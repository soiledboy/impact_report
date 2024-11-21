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
        # Read the CSV file
        df = pd.read_csv(file_path, parse_dates=['Date'])
        
        # Sort by date
        df = df.sort_values('Date')
        
        # Group by month
        monthly_data = df.groupby(pd.Grouper(key='Date', freq='ME'))
        
        # Calculate monthly aggregates
        monthly_reports = monthly_data.agg({
            'Clicks': 'sum',
            'Actions': 'sum',
            'Sale Amount': 'sum',
            'Total Earnings': 'sum',  # Make sure we're using Total Earnings
            'EPA': 'mean',
            'EPC': 'mean',
            'Conversion Rate': 'mean',
            'AOV': 'mean'
        })
        
        return monthly_reports
        
    except Exception as e:
        logging.error(f"Error in process_csv: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def create_graph(df, column, projection=None, cumulative=False):
    # Map the column names to actual DataFrame columns
    column_mapping = {
        'Earnings': 'Total Earnings',
        'Clicks': 'Clicks',
        'Conversion Rate': 'Conversion Rate',
        'Sales': 'Sale Amount'  # Add mapping for Sales
    }
    
    actual_column = column_mapping.get(column, column)
    
    # Calculate cumulative values if requested
    if cumulative:
        plot_data = df[actual_column].cumsum()
        title = f'Cumulative {column} Over Time'
    else:
        plot_data = df[actual_column]
        title = f'{column} Over Time'
    
    fig = px.line(x=df.index, y=plot_data, title=title)
    
    # Add monthly percentage changes for cumulative graphs
    if cumulative:
        # Calculate monthly percentage changes
        monthly_pct_change = df[actual_column].pct_change() * 100
        
        # Add annotations for each month's percentage change
        for idx in range(1, len(df)):
            pct_change = monthly_pct_change.iloc[idx]
            if not pd.isna(pct_change):  # Skip if percentage change is NaN
                fig.add_annotation(
                    x=df.index[idx],
                    y=plot_data.iloc[idx],
                    text=f"{pct_change:.1f}%",
                    showarrow=True,
                    arrowhead=1,
                    yshift=10,
                    font=dict(size=10),
                    arrowsize=0.3,
                    arrowwidth=1
                )
    
    if projection is not None:
        proj_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=6, freq='M')
        fig.add_trace(go.Scatter(x=proj_dates, y=projection, mode='lines', name='Projection', line=dict(dash='dash')))
    
    # Update layout to accommodate annotations
    if cumulative:
        fig.update_layout(
            showlegend=True,
            margin=dict(t=50, b=50, l=50, r=50),
            height=600  # Make the graph taller to fit annotations
        )
    
    img = BytesIO()
    fig.write_image(img, format='png')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

def project_future(df, column, periods=6):
    # Map the column names to actual DataFrame columns
    column_mapping = {
        'Earnings': 'Total Earnings',
        'Clicks': 'Clicks'
    }
    
    actual_column = column_mapping.get(column, column)
    X = np.arange(len(df)).reshape(-1, 1)
    y = df[actual_column].values
    
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
                'Conversion_Rate': create_graph(monthly_reports, 'Conversion Rate'),
                'Cumulative_Sales': create_graph(monthly_reports, 'Sales', cumulative=True),
                'Cumulative_Earnings': create_graph(monthly_reports, 'Earnings', cumulative=True)
            }
            
            overall_performance = monthly_reports.sum().to_dict()  # Convert to dictionary
            
            # Calculate average monthly earnings growth rate
            earnings = monthly_reports['Total Earnings'].values
            growth_rates = []
            
            for i in range(1, len(earnings)):
                if earnings[i-1] != 0:  # Avoid division by zero
                    growth_rate = ((earnings[i] - earnings[i-1]) / earnings[i-1]) * 100
                    growth_rates.append(growth_rate)
            
            # Calculate average growth rate, defaulting to 0 if no valid rates
            avg_monthly_growth = float(round(sum(growth_rates) / len(growth_rates), 2)) if growth_rates else 0
            overall_performance['Average Monthly Earnings Growth'] = avg_monthly_growth
            
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
