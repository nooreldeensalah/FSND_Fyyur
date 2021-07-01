# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
db = SQLAlchemy(app)


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, server_default="f", default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="venue")


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(70), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, server_default="f", default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", backref="artist")


class Show(db.Model):
    __tablename__ = "Show"
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
