
from flask import Flask, render_template_string, request
import asyncio
import random
import string
import requests
from playwright.async_api import async_playwright

app = Flask(__name__)

HTML = """
<!doctype html>
<title>Osmosis Auto Signup</title>
<h2>Osmosis Free Trial Generator</h2>
<form method="post">
  <button type="submit">Generate Account</button>
</form>
{% if result %}
  <p><strong>Email:</strong> {{ result.email }}</p>
  <p><strong>Password:</strong> {{ result.password }}</p>
  <p><strong>First Name:</strong> {{ result.first_name }}</p>
  <p><strong>Last Name:</strong> {{ result.last_name }}</p>
  <p><strong>Status:</strong> {{ result.status }}</p>
{% endif %}
"""

def generate_random_string(length=6):
    return ''.join(random.choices(string.ascii_letters, k=length)).capitalize()

def generate_email():
    session = requests.Session()
    domain = session.get("https://api.mail.tm/domains").json()["hydra:member"][0]["domain"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    email = f"{username}@{domain}"
    password = "Fuck@123"
    session.post("https://api.mail.tm/accounts", json={"address": email, "password": password})
    resp = session.post("https://api.mail.tm/token", json={"address": email, "password": password})
    token = resp.json()["token"]
    return email, password, token, session

async def register_account(email, password, first_name, last_name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.osmosis.org/invite/n41K4pG", wait_until="networkidle", timeout=60000)
        try:
            await page.click("text=Accept All", timeout=5000)
        except:
            pass
        await page.fill('input[placeholder*="Enter email"]', email)
        await page.fill('input[placeholder*="First or Preferred"]', first_name)
        await page.fill('input[placeholder*="Last Name"]', last_name)
        await page.fill('input[type="password"]', password)
        await page.click('button:has-text("Let\'s go!")')
        await page.wait_for_timeout(5000)
        await browser.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        email, password, token, session = generate_email()
        first_name = generate_random_string()
        last_name = generate_random_string()
        asyncio.run(register_account(email, password, first_name, last_name))

        # Wait for email
        activation_link = None
        headers = {"Authorization": f"Bearer {token}"}
        for _ in range(20):
            inbox = session.get("https://api.mail.tm/messages", headers=headers).json()
            if inbox["hydra:member"]:
                msg_id = inbox["hydra:member"][0]["id"]
                msg = session.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers).json()
                body = msg["html"][0] if msg["html"] else msg["text"]
                import re
                match = re.search(r"https://www\.osmosis\.org/email-confirmation[^\"']+", body)
                if match:
                    activation_link = match.group(0)
                    session.get(activation_link)
                    break
            asyncio.run(asyncio.sleep(3))
        status = "✅ Activated" if activation_link else "❌ Activation Failed"
        result = type('Result', (), dict(email=email, password=password, first_name=first_name, last_name=last_name, status=status))
    return render_template_string(HTML, result=result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
