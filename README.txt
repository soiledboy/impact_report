Impact Report Analysis Tool
This Flask app provides advanced analysis and projections based on data from the Performance by Day section of Impact Reports. It is designed to enhance the insights provided by the default Impact Report graphs.

Features
Processes data extracted from Impact Reports > Overview > Performance by Day.
Generates custom visualizations and projections using tools like plotly and pandas.
Easy to set up and run locally with Flask.

Installation and Setup
Clone the repository:
git clone https://github.com/soiledboy/impact_report.git
cd impact_report

Set up a virtual environment:
Install virtualenv if you haven’t already:
pip install virtualenv
Create and activate a virtual environment:
virtualenv venv
source venv/bin/activate (On Windows, use venv\Scripts\activate)

Install dependencies:
With the virtual environment activated, install the required packages:
pip install -r requirements.txt

Prepare your data:
Extract your Impact Report CSV file:

Navigate to Reports > Overview > Performance by Day in your Impact Reports system.
Click Extract to CSV and save the file.

Run the app:
Place the extracted CSV file in the root directory of the project. Then start the Flask app:
python flask_app.py

Access the app:
Open your browser and navigate to:
http://127.0.0.1:5000

Usage
Upload your extracted CSV file through the app interface.
Explore visualizations and projections based on the performance data.

Contributing
Contributions are welcome! Feel free to fork this repository, make improvements, and submit a pull request.

License
This project is licensed under the MIT License (LICENSE).