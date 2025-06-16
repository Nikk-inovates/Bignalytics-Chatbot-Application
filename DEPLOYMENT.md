# 🚀 Deploy FastAPI Chatbot with Supabase Cert on AWS EC2

## ✅ Prerequisites

- AWS EC2 instance (Ubuntu or Amazon Linux)
- SSH `.pem` key
- GitHub repo of your chatbot
- Domain (e.g., `bignalytics-chatbot.me`)
- Supabase root cert file (`supabase-ca.pem.crt`)

---

## ⚙️ 1. Connect to EC2

```bash
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>
🔄 2. Update System & Install Dependencies
Ubuntu:
bash
Copy
Edit
sudo apt update && sudo apt upgrade -y
sudo apt install git python3-pip python3-venv -y
Amazon Linux:
bash
Copy
Edit
sudo yum update -y
sudo yum install git python3-pip python3-virtualenv -y
📥 3. Clone Git Repository
bash
Copy
Edit
git clone https://github.com/your-user/your-chatbot-repo.git
cd your-chatbot-repo
🐍 4. Create Virtual Environment
bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
📦 5. Install Requirements
bash
Copy
Edit
pip install -r requirements.txt
📝 6. Create .env File
bash
Copy
Edit
nano .env
Paste:

env
Copy
Edit
OPENROUTER_API_KEY=your-deepseek-api-key
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
SSL_CERT_PATH=/etc/ssl/certs/supabase-ca.pem
📤 7. Upload Supabase SSL Cert
On your local system:
bash
Copy
Edit
scp "C:\Users\nikhi\Downloads\supabase-ca.pem.crt" ec2-user@<EC2_PUBLIC_IP>:/home/ec2-user/
On EC2:
bash
Copy
Edit
sudo mv /home/ec2-user/supabase-ca.pem.crt /etc/ssl/certs/supabase-ca.pem
sudo chmod 644 /etc/ssl/certs/supabase-ca.pem
🧪 8. Test FastAPI App
bash
Copy
Edit
uvicorn main:app --host 0.0.0.0 --port 8000
Test in browser:

cpp
Copy
Edit
http://<EC2_PUBLIC_IP>:8000
🌐 9. (Optional) Use Your Domain bignalytics-chatbot.me
A. Update DNS
Go to your DNS provider

Add A record:

makefile
Copy
Edit
Host: @
Value: <EC2_PUBLIC_IP>
B. Install NGINX + Certbot
bash
Copy
Edit
sudo apt install nginx -y
sudo snap install core && sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
C. Start NGINX
bash
Copy
Edit
sudo systemctl enable nginx
sudo systemctl start nginx
D. Get SSL Certificate
bash
Copy
Edit
sudo certbot --nginx -d bignalytics-chatbot.me
🔁 10. NGINX Reverse Proxy (Optional)
nginx
Copy
Edit
server {
    listen 80;
    server_name bignalytics-chatbot.me;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
Apply Changes
bash
Copy
Edit
sudo nginx -t
sudo systemctl reload nginx
🧩 Summary of Key Commands
Task	Command
Connect to EC2	ssh -i ...
Clone Repo	git clone ...
Create venv	python3 -m venv venv
Install deps	pip install -r requirements.txt
Upload cert	scp + sudo mv
Update .env	With keys and cert path
Setup domain + HTTPS	NGINX + Certbot
Start FastAPI app	uvicorn main:app --host 0.0.0.0 --port 8000

🛠️ Want More?
Let me know if you want:

✅ systemd service for auto-start

✅ Full NGINX site config file

✅ .env.template for repo
