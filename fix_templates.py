import os
import glob

replacements = {
    "url_for('login')": "url_for('auth.login')",
    "url_for('signup')": "url_for('auth.signup')",
    "url_for('logout')": "url_for('auth.logout')",
    "url_for('verify_login')": "url_for('auth.verify_login')",
    "url_for('dashboard')": "url_for('user.dashboard')",
    "url_for('transactions')": "url_for('user.transactions')",
    "url_for('download_statement')": "url_for('user.download_statement')",
    "url_for('transfer')": "url_for('user.transfer')",
    "url_for('verify_transfer')": "url_for('user.verify_transfer')",
    "url_for('beneficiaries')": "url_for('user.beneficiaries')",
    "url_for('fixed_deposits')": "url_for('user.fixed_deposits')",
    "url_for('open_fd')": "url_for('user.open_fd')",
    "url_for('notifications')": "url_for('user.notifications')",
    "url_for('support')": "url_for('user.support')",
    "url_for('security_log')": "url_for('user.security_log')",
    "url_for('profile')": "url_for('user.profile')",
    "url_for('change_password')": "url_for('user.change_password')"
}

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            path = os.path.join(root, file)
            with open(path, 'r') as f:
                content = f.read()
            for old, new in replacements.items():
                content = content.replace(old, new)
            with open(path, 'w') as f:
                f.write(content)
print("Templates updated.")
