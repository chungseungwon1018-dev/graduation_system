import os, sys

# Ensure parent directory (project root) is on sys.path so imports succeed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main_app import app, db_config
import io
import os

# Use Flask test client
client = app.test_client()

# First, ensure user exists: use register endpoint
import time
username = f'testuser_{int(time.time())}'
password = 'TestPass123!'
name = 'Test User'

# Register
resp = client.post('/register', data={'username': username, 'password': password, 'confirm_password': password, 'name': name})
print('Register status:', resp.status_code)
print('Register response:', resp.get_data(as_text=True)[:500])

# Login
resp = client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
print('Login status:', resp.status_code)
print('Login response:', resp.get_data(as_text=True)[:500])

# If login didn't succeed, set session manually for test client to simulate a logged-in student
if resp.status_code != 200 or '학생 대시보드' not in resp.get_data(as_text=True):
    with client.session_transaction() as sess:
        sess['user_id'] = username
        sess['role'] = 'student'

# Choose sample file
sample_path = '샘플파일/report_1764415240667_정승원.xlsx'
if not os.path.exists(sample_path):
    sample_path = 'uploads/2021026018_20250602_015456_ex_1.xlsx'

assert os.path.exists(sample_path), f"Sample file not found: {sample_path}"

with open(sample_path, 'rb') as f:
    data = {'file': (f, os.path.basename(sample_path))}
    resp = client.post('/api/student/upload', data=data, content_type='multipart/form-data')
    print('Upload status:', resp.status_code)
    print('Upload response:', resp.get_data(as_text=True))

# Fetch student info
resp = client.get('/api/student/info')
print('Student info status:', resp.status_code)
print('Student info:', resp.get_data(as_text=True))

# Fetch student analysis
resp = client.get('/api/student/analysis')
print('Student analysis status:', resp.status_code)
print('Student analysis:', resp.get_data(as_text=True))
