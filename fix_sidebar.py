import os
import re

template_dir = 'templates'
replace_str = '{% include "_sidebar.html" %}'

files_to_fix = [
    'profile.html', 'security_log.html', 'open_fd.html', 'support.html',
    'fixed_deposits.html', 'beneficiaries.html', 'change_password.html',
    'new_ticket.html', 'transactions.html', 'add_beneficiary.html',
    'transfer.html', 'dashboard.html', 'notifications.html'
]

for filename in files_to_fix:
    filepath = os.path.join(template_dir, filename)
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r') as f:
        content = f.read()
        
    # Find the <aside class="sidebar"> ... </aside> block
    # Using regex with re.DOTALL to match across newlines
    pattern = r'<aside class="sidebar">.*?</aside>'
    new_content = re.sub(pattern, replace_str, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filename}")
    else:
        print(f"No match found in {filename}")
