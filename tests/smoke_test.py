import requests
import re
from datetime import datetime

base = 'http://127.0.0.1:5000'
s = requests.Session()

def post(path, data):
    r = s.post(base+path, data=data, allow_redirects=True)
    print(f'POST {path} -> {r.status_code}')
    return r

def get(path):
    r = s.get(base+path)
    print(f'GET {path} -> {r.status_code}')
    return r

def main():
    user = 'smoketest_user'
    pwd = 'password123'

    # Register
    post('/register', {'username': user, 'password': pwd})

    # Login
    r = post('/login', {'username': user, 'password': pwd})
    if 'Invalid credentials' in r.text:
        print('Login failed')
        return

    # Create category
    post('/categories', {'name': 'Food'})

    # Find category id from /add page
    r = get('/add')
    m = re.search(r'<option value="(\d+)">Food</option>', r.text)
    if not m:
        print('Could not find category id in /add page')
        return
    cat_id = m.group(1)
    print('Found category id:', cat_id)

    # Add expense
    today = datetime.utcnow().strftime('%Y-%m-%d')
    post('/add', {'amount': '12.50', 'description': 'Test lunch', 'date': today, 'category': cat_id})

    # Set budget for current month
    month = datetime.utcnow().strftime('%Y-%m')
    post('/budgets', {'month': month, 'category': cat_id, 'amount': '10.00'})

    # Fetch dashboard
    r = get('/dashboard')
    if 'Budget exceeded' in r.text or '⚠' in r.text:
        print('Budget alert present on dashboard')
    else:
        print('No budget alert found on dashboard')

    # Fetch monthly report
    year, mnum = month.split('-')
    r = get(f'/monthly_report/{year}/{int(mnum)}')
    if 'Test lunch' in r.text:
        print('Expense appears in monthly report')
    else:
        print('Expense not found in monthly report')

if __name__ == '__main__':
    main()
