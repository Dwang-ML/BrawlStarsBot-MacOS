# How to install:

Type the following code into Terminal. Be patient as downloading and installing may take a while.
```commandline
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install pyenv
arch -arm64 pyenv install 3.11.7
arch -arm64 pyenv global 3.11.7
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
source ~/.zshrc
which python3
python3 --version
pyenv versions
git clone https://github.com/Dwang-ML/BrawlStarsBot-MacOS
cd BrawlStarsBot-MacOS
pip install -r requirements.txt
```

#How to run after installation:

Run this in a BRAND-NEW Terminal, or if you are experienced, its as simple as running main.py.
```commandline
cd BrawlStarsBot-MacOS
python3 main.py
```

Notes :
- You must have ARM64 Python installed for onnxruntime-silicon, which ideally boosts performance. 

Mac dev:
 - DwangML