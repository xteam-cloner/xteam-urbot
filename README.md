<p align="center">
  <img src="./resources/extras/logo_readme.jpg" alt="xteam-urbot Logo">
</p>


<h3 align="center">
    ─「 ᴅᴇᴩʟᴏʏ ᴏɴ ᴠᴘs 」─
</h3>


Copy these blue words on by on from here to use commands in you own vps.
</h3>

✨ Clone the repository:
```console
git clone https://github.com/xteam-cloner/xteam-urbot
```

✨ Go to the cloned folder:
```console
cd xteam-urbot
```
✨ Create a virtual env:
```console
virtualenv -p /usr/bin/python3 venv 
 . ./venv/bin/activate
```
✨ Install the requirements:
```console
pip3 install --no-cache-dir  -r requirements.txt
```

✨ Fill your variables in the env by

```console
nano .env
```
✨ If you have finished edit, CTRL S + CTRL X.

✨ Install screen to keep running your bot when you close the terminal by
```console
screen -S xteam-urbot
```
✨ Finally Run the bot:
```console
bash startup
```
✨ For getting out from screen session press
• Ctrl+a and Ctrl+d

✨ Termux Session Gen
```console
apt update && apt upgrade -y && apt install python wget -y && pip install Telethon && wget https://raw.githubusercontent.com/xteam-cloner/Userbotx/dev/resources/session/ssgen.py && python ssgen.py
```
</h3>

# License
[![License](https://www.gnu.org/graphics/agplv3-155x51.png)](LICENSE)   
xteam is licensed under [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.en.html) v3 or later.
