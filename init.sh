python3 -m venv .venv

source ./.venv/bin/activate

python3 -m pip install --upgrade pip

pip3 install -r requirements.txt -r requirements.dev.txt

./scripts/git-hooks/install-hooks.sh

tox
