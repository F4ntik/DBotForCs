import sys
import os

# Add the src directory to sys.path to allow direct imports of modules from src
# For example: from bot.bot_server import BotServer
# This assumes conftest.py is in dbot/tests/
# and the source code is in dbot/src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
