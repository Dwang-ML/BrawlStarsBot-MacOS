# PylaAI

PylaAI is currently the best external Brawl Stars bot.
This repository is intended for devs and it's recommended for others to use the official version from the discord.

**Warning :** This is the source-code, which is meant for developpers or people that know how to install python libraries and run python scripts --> The official build is linked in the discord, which is the source-code converted into an exe so you don't need additional knowledge to run the bot. (You will have to go through a linkvertise link)

How to run : 
- Install python (tested with python 3.11.9)
- in a cmd in the folder run `pip install -r requirements.txt` to install the necessary libraries. Read Notes if you have a gpu.
- run main.py
- enjoy !

Notes :
- If you have an nvidia GPU, you can better performances by installing the GPU version of PyTorch, check https://pytorch.org/get-started/locally/ to get the command for your pc (you will need to install CUDA and Cudnn if you don't already have them)
- This is the "localhost" version which means everything API related isn't enabled (login, online stats tracking, auto brawler list updating, auto icon updating, auto wall model updating). 
You can make it "online" by changing the base api url in utils.py and recoding the app to answer to the different endpoints. Site's code might become opensource but currently isn't.
- You can get the .pt version of the ai vision model at https://github.com/AngelFireLA/BrawlStarsBotMaking
- This repository won't contain early access features before they are released to the public.
- Please respect the "no selling" license as respect for our work.

Devs : 
- Iyordanov
- AngelFire

# If you want to contribute, don't hesitate to create an Issue, a Pull Request, or/and make a ticket on the Pyla discord server at :
https://discord.gg/xUusk3fw4A

Don't know what to do ? Check the To-Fix and Idea lists :
https://trello.com/b/SAz9J6AA/public-pyla-trello
