#!/usr/bin/env python3
import sys
print("Python version:", sys.version)
print("Starting imports...")

try:
    from flask import Flask
    print("✓ Flask imported")
except Exception as e:
    print("✗ Flask import error:", e)
    sys.exit(1)

try:
    import mysql.connector
    print("✓ MySQL connector imported")
except Exception as e:
    print("✗ MySQL connector import error:", e)

try:
    from enhanced_xlsx_parser import process_excel_file_enhanced
    print("✓ Enhanced XLSX parser imported")
except Exception as e:
    print("✗ Enhanced XLSX parser import error:", e)

try:
    from graduation_requirements_checker import analyze_student_graduation
    print("✓ Graduation requirements checker imported")
except Exception as e:
    print("✗ Graduation requirements checker import error:", e)

try:
    from notification_system import get_user_notifications
    print("✓ Notification system imported")
except Exception as e:
    print("✗ Notification system import error:", e)

print("All imports completed successfully!")

app = Flask(__name__)
print("Flask app created")

@app.route('/')
def hello():
    return "Hello World!"

if __name__ == '__main__':
    print("Starting Flask development server...")
    app.run(debug=True, host='0.0.0.0', port=5000)