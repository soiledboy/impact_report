import pandas as pd

# Read the CSV file (using a raw string for the file path)
df = pd.read_csv(r'C:\Users\mlarson.LOCAL\Documents\dev\impact\impact_report.csv', parse_dates=['Date'])

# Convert 'Conversion Rate' to numeric, removing '%' symbol
df['Conversion Rate'] = df['Conversion Rate'].str.rstrip('%').astype('float') / 100.0

# Sort the dataframe by date
df = df.sort_values('Date')

# Create a monthly grouping
monthly_data = df.groupby(pd.Grouper(key='Date', freq='ME'))

# Function to generate report for a month
def generate_monthly_report(group):
    return pd.Series({
        'Total Clicks': group['Clicks'].sum(),
        'Total Actions': group['Actions'].sum(),
        'Total Sales': group['Sale Amount'].sum(),
        'Total Earnings': group['Earnings'].sum(),
        'Average EPA': group['EPA'].mean(),
        'Average EPC': group['EPC'].mean(),
        'Average Conversion Rate': group['Conversion Rate'].mean(),
        'Average AOV': group['AOV'].mean()
    })

# Generate monthly reports
monthly_reports = monthly_data.apply(generate_monthly_report)

# Calculate monthly growth
monthly_growth = monthly_reports.pct_change()

# Function to format growth as percentage string
def format_growth(value):
    return f"{value*100:+.2f}%" if pd.notnull(value) else "N/A"

# Print the monthly reports with growth
for (date, report), (_, growth) in zip(monthly_reports.iterrows(), monthly_growth.iterrows()):
    print(f"\nMonthly Report for {date.strftime('%B %Y')}:")
    print(f"Total Clicks: {report['Total Clicks']:.0f} (Growth: {format_growth(growth['Total Clicks'])})")
    print(f"Total Actions: {report['Total Actions']:.0f} (Growth: {format_growth(growth['Total Actions'])})")
    print(f"Total Sales: ${report['Total Sales']:.2f} (Growth: {format_growth(growth['Total Sales'])})")
    print(f"Total Earnings: ${report['Total Earnings']:.2f} (Growth: {format_growth(growth['Total Earnings'])})")
    print(f"Average EPA: ${report['Average EPA']:.2f} (Growth: {format_growth(growth['Average EPA'])})")
    print(f"Average EPC: ${report['Average EPC']:.2f} (Growth: {format_growth(growth['Average EPC'])})")
    print(f"Average Conversion Rate: {report['Average Conversion Rate']:.2f}% (Growth: {format_growth(growth['Average Conversion Rate'])})")
    print(f"Average AOV: ${report['Average AOV']:.2f} (Growth: {format_growth(growth['Average AOV'])})")
    print("-" * 60)

# Calculate and print overall performance
overall_performance = generate_monthly_report(df)
print("\nOverall Performance:")
print(f"Total Clicks: {overall_performance['Total Clicks']:.0f}")
print(f"Total Actions: {overall_performance['Total Actions']:.0f}")
print(f"Total Sales: ${overall_performance['Total Sales']:.2f}")
print(f"Total Earnings: ${overall_performance['Total Earnings']:.2f}")
print(f"Average EPA: ${overall_performance['Average EPA']:.2f}")
print(f"Average EPC: ${overall_performance['Average EPC']:.2f}")
print(f"Average Conversion Rate: {overall_performance['Average Conversion Rate']:.2f}%")
print(f"Average AOV: ${overall_performance['Average AOV']:.2f}")
