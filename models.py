from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


#create db instance
db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Venue(db.Model): # Venue Model
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship('Genre', secondary='venue_genre', backref=db.backref('venues'))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):             # Artist Model
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship('Genre', secondary='artist_genre', backref=db.backref('artists'))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):       # Show Model
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)    
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)  
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    
    def __repr__(self):
        return f'<Show {self.id} {self.start_time} artist_id={self.artist_id} venue_id={self.venue_id}>'


class Genre(db.Model):      # Genre Model
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

artist_genre = db.Table('artist_genre',             # Table Genre pour Atist 
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True)
)

venue_genre = db.Table('venue_genre',       # Table Genre pour Venue
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), primary_key=True)
)