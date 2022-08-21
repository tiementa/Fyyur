#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
import re
from operator import itemgetter 
import collections
from models import Venue, venue_genre, Artist, artist_genre, Show, Genre
from models import db    # importing db from models
from csrfprotect import csrf



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# db = SQLAlchemy(app)
db.init_app(app)    #  initialized db
migrate = Migrate(app, db)
csrf.init_app(app)
collections.Callable = collections.abc.Callable


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')   # Venue View 
def venues():
    
    venues = Venue.query.all()
    data = []   
    cstate_data = set()

    for venue in venues:
        cstate_data.add( (venue.city, venue.state) )  
    
    cstate_data = list(cstate_data)
    cstate_data.sort(key=itemgetter(1,0))   

    now = datetime.now()    
    for one_cstate in cstate_data:
        v_list = []
        for venue in venues:
            if (venue.city == one_cstate[0]) and (venue.state == one_cstate[1]):
                venue_shows = Show.query.filter_by(venue_id=venue.id).all()
                num_upcoming = 0
                for show in venue_shows:
                    if show.start_time > now:
                        num_upcoming += 1

                v_list.append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": num_upcoming
                })
        data.append({
            "city": one_cstate[0],
            "state": one_cstate[1],
            "venues": v_list
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])  # Recherche de Venue
def search_venues():
    search_term = request.form.get('search_term', '').strip()
    venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()   
    v_list = []
    now = datetime.now()
    for venue in venues:
        venue_shows = Show.query.filter_by(venue_id=venue.id).all()
        num_upcoming = 0
        for show in venue_shows:
            if show.start_time > now:
                num_upcoming += 1

        v_list.append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming 
        })

    response = {
        "count": len(venues),
        "data": v_list
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')    # Venue individuel selection
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)   

    if not venue:
        return redirect(url_for('index'))
    else:
        genres = [ genre.name for genre in venue.genres ]       
        past_shows = []
        past_shows_count = 0
        upcoming_shows = []
        upcoming_shows_count = 0
        now = datetime.now()
        for show in venue.shows:
            if show.start_time > now:
                upcoming_shows_count += 1
                upcoming_shows.append({
                    "artist_id": show.artist_id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
            if show.start_time < now:
                past_shows_count += 1
                past_shows.append({
                    "artist_id": show.artist_id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })

        data = {
            "id": venue_id,
            "name": venue.name,
            "genres": genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
            "website_link": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": upcoming_shows_count
        }

        return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])      # Creation de Venue
def create_venue_submission():
    form = VenueForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    address = form.address.data.strip()
    phone = form.phone.data
    phone = re.sub('\D', '', phone) 
    genres = form.genres.data             
    seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website_link = form.website_link.data.strip()
    facebook_link = form.facebook_link.data.strip()
    
    if not form.validate():
        flash( form.errors )
        return redirect(url_for('create_venue_submission'))

    else:
        error = False
        try:
            nw_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, \
                seeking_talent=seeking_talent, seeking_description=seeking_description, image_link=image_link, \
                website_link=website_link, facebook_link=facebook_link)
            for genre in genres:
                get_genre = Genre.query.filter_by(name=genre).one_or_none()  
                if get_genre:
                    nw_venue.genres.append(get_genre)
                else:
                    nw_genre = Genre(name=genre)
                    db.session.add(nw_genre)
                    nw_venue.genres.append(nw_genre)  

            db.session.add(nw_venue)
            db.session.commit()
        except Exception as e:
            error = True
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
          
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
            return redirect(url_for('index'))
        else:
            flash('An error occurred. Venue ' + name + ' could not be listed.')
            abort(500)


@app.route('/venues/<venue_id>/delete', methods=['GET'])    # delete venue 
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return redirect(url_for('index'))
    else:
        error = False
        venue_name = venue.name
        try:
            db.session.delete(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash(f'An error occurred deleting venue {venue_name}.')
            abort(500)
        else:
            return jsonify({
                'deleted': True,
                'url': url_for('venues')
            })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.order_by(Artist.name).all() 

    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST']) #search artist
def search_artists():
    search_term = request.form.get('search_term', '').strip()
    artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()  
    artist_list = []
    now = datetime.now()
    for artist in artists:
        artist_shows = Show.query.filter_by(artist_id=artist.id).all()
        num_upcoming = 0
        for show in artist_shows:
            if show.start_time > now:
                num_upcoming += 1

        artist_list.append({
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": num_upcoming  
        })

    response = {
        "count": len(artists),
        "data": artist_list
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))



@app.route('/artists/<int:artist_id>')      #Select artist by id
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)   
    if not artist:
        return redirect(url_for('index'))
    else:
        genres = [ genre.name for genre in artist.genres ]
        past_shows = []
        past_shows_count = 0
        upcoming_shows = []
        upcoming_shows_count = 0
        now = datetime.now()
        past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time < now).all()
        coming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time > now).all()

        for show in past_shows_query:
            past_shows_count += 1
            past_shows.append({
                    "venue_id": show.venue_id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })
        for show in coming_shows_query:
             upcoming_shows_count += 1
             upcoming_shows.append({
                    "venue_id": show.venue_id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": format_datetime(str(show.start_time))
                })

        data = {
            "id": artist_id,
            "name": artist.name,
            "genres": genres,
            "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
            "website_link": artist.website_link,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": upcoming_shows_count
        }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])    # edit single artist
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)  
    if not artist:
        return redirect(url_for('index'))
    else:
        form = ArtistForm(obj=artist)
    genres = [ genre.name for genre in artist.genres ]
    
    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": artist.state,
        "phone": (artist.phone[:3] + '-' + artist.phone[3:6] + '-' + artist.phone[6:]),
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    phone = form.phone.data
    phone = re.sub('\D', '', phone) 
    genres = form.genres.data                 
    seeking_venue = True if form.seeking_venue.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website_link = form.website_link.data.strip()
    facebook_link = form.facebook_link.data.strip()
    
    if not form.validate():
        flash( form.errors )
        return redirect(url_for('edit_artist_submission', artist_id=artist_id))

    else:
        error = False

        try:
            artist = Artist.query.get(artist_id)
            artist.name = name
            artist.city = city
            artist.state = state
            artist.phone = phone
            artist.seeking_venue = seeking_venue
            artist.seeking_description = seeking_description
            artist.image_link = image_link
            artist.website_link = website_link
            artist.facebook_link = facebook_link
            artist.genres = []

            for genre in genres:
                get_genre = Genre.query.filter_by(name=genre).one_or_none()  
                if get_genre:
                    artist.genres.append(get_genre)

                else:
                    nw_genre = Genre(name=genre)
                    db.session.add(nw_genre)
                    artist.genres.append(nw_genre)  
            db.session.commit()
        except Exception as e:
            error = True
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('Artist ' + request.form['name'] + ' was successfully updated!')
            return redirect(url_for('show_artist', artist_id=artist_id))
        else:
            flash('An error occurred. Artist ' + name + ' could not be updated.')
            abort(500)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])  # edit single Venue
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)  
    if not venue:
        return redirect(url_for('index'))
    else:
        form = VenueForm(obj=venue)
    genres = [ genre.name for genre in venue.genres ]
    
    venue = {
        "id": venue_id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": (venue.phone[:3] + '-' + venue.phone[3:6] + '-' + venue.phone[6:]),
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)



@app.route('/venues/<int:venue_id>/edit', methods=['POST'])         # edit single Venue
def edit_venue_submission(venue_id):
    form = VenueForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    address = form.address.data.strip()
    phone = form.phone.data
    phone = re.sub('\D', '', phone) 
    genres = form.genres.data                   
    seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website_link = form.website_link.data.strip()
    facebook_link = form.facebook_link.data.strip()
    
    if not form.validate():
        flash( form.errors )
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))

    else:
        error = False
        try:
            venue = Venue.query.get(venue_id)

            venue.name = name
            venue.city = city
            venue.state = state
            venue.address = address
            venue.phone = phone
            venue.seeking_talent = seeking_talent
            venue.seeking_description = seeking_description
            venue.image_link = image_link
            venue.website_link = website_link
            venue.facebook_link = facebook_link
            venue.genres = []
            for genre in genres:
                get_genre = Genre.query.filter_by(name=genre).one_or_none() 
                if get_genre:
                    venue.genres.append(get_genre)

                else:
                    nw_genre = Genre(name=genre)
                    db.session.add(nw_genre)
                    venue.genres.append(nw_genre)  
            db.session.commit()
        except Exception as e:
            error = True
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('Venue ' + request.form['name'] + ' was successfully updated!')
            return redirect(url_for('show_venue', venue_id=venue_id))
        else:
            flash('An error occurred. Venue ' + name + ' could not be updated.')
            abort(500)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()

    name = form.name.data.strip()
    city = form.city.data.strip()
    state = form.state.data
    phone = form.phone.data
    phone = re.sub('\D', '', phone) 
    genres = form.genres.data             
    seeking_venue = True if form.seeking_venue.data == 'Yes' else False
    seeking_description = form.seeking_description.data.strip()
    image_link = form.image_link.data.strip()
    website_link = form.website_link.data.strip()
    facebook_link = form.facebook_link.data.strip()

    if not form.validate():
        flash( form.errors )
        return redirect(url_for('create_artist_submission'))

    else:
        error = False
        try:
            new_artist = Artist(name=name, city=city, state=state, phone=phone, \
                seeking_venue=seeking_venue, seeking_description=seeking_description, image_link=image_link, \
                website_link=website_link, facebook_link=facebook_link)
            for genre in genres:
                get_genre = Genre.query.filter_by(name=genre).one_or_none() 
                if get_genre:
                    new_artist.genres.append(get_genre)

                else:
                    nw_genre = Genre(name=genre)
                    db.session.add(nw_genre)
                    new_artist.genres.append(nw_genre)  

            db.session.add(new_artist)
            db.session.commit()
        except Exception as e:
            error = True
            db.session.rollback()
        finally:
            db.session.close()

        if not error:
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
            return redirect(url_for('index'))
        else:
            flash('An error occurred. Artist ' + name + ' could not be listed.')
            abort(500)

@app.route('/artists/<artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return redirect(url_for('index'))
    else:
        error = False
        artist_name = artist.name
        try:
            db.session.delete(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash(f'An error occurred deleting artist {artist_name}.')
            abort(500)
        else:
            return jsonify({
                'deleted': True,
                'url': url_for('artists')
            })


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows = Show.query.all()
    
    for show in shows:
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])       # create show
def create_show_submission():
    form = ShowForm()

    artist_id = form.artist_id.data.strip()
    venue_id = form.venue_id.data.strip()
    start_time = form.start_time.data

    error = False
    
    try:
        new_show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
        db.session.add(new_show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        flash(f'An error occurred.  Show could not be listed.')
    else:
        flash('Show was successfully listed!')
    
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''