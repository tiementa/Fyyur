from flask import Flask
from .app import app
from . import models

models.db.__init__app(app)