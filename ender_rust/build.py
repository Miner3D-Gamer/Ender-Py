import os

cwd = os.getcwd()
this = os.path.dirname(os.path.realpath(__file__))
os.chdir(this)
os.system("cargo build --release")
os.chdir(cwd)
