💞 VPS DEPLOY 💞
Get your Necessary Variables

✨ Clone the repository:
```
git clone https://github.com/xteam-cloner/xteam-urbot
```

✨ Go to the cloned folder:
```
cd xteam-urbot
```
✨ Create a virtual env:
```
virtualenv -p /usr/bin/python3 venv 
 . ./venv/bin/activate
```
✨ Install the requirements:
```
pip3 install --no-cache-dir  -r requirements.txt
```

✨ Fill your variables in the env by

```
nano .env
```
✨ If you have finished edit, CTRL S + CTRL X.

✨ Install screen to keep running your bot when you close the terminal by
```
screen -S xteam-urbot
```
✨ Finally Run the bot:
```
bash startup
```
✨ For getting out from screen session press
• Ctrl+a and Ctrl+d

✨ Termux Session Gen
```
apt update && apt upgrade -y && apt install python wget -y && pip install Telethon && wget https://raw.githubusercontent.com/xteam-cloner/Userbotx/dev/resources/session/ssgen.py && python ssgen.py
```
