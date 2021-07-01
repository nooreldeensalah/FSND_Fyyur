# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


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


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []
    city_state_pair = []
    for venue in Venue.query.distinct(Venue.city, Venue.state):
        city_state_pair.append((venue.city, venue.state))
    for city, state in city_state_pair:
        data_dict = {"city": city, "state": state, "venues": []}
        for venue in Venue.query.filter_by(city=city, state=state).all():
            data_dict["venues"].append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": Venue.query.join(Show)
                    .filter(Venue.id == venue.id, Show.start_time > datetime.now())
                    .count(),
                }
            )
        data.append(data_dict)
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    response = {"count": None, "data": list()}  # Initializing dictionary
    search_term = request.form["search_term"]
    for venue in Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all():
        response["count"] = Venue.query.filter(
            Venue.name.ilike(f"%{search_term}%")
        ).count()
        response["data"].append(
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": Venue.query.join(Show)
                .filter(Venue.id == venue.id, Show.start_time > datetime.now())
                .count(),
            }
        )

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=search_term,
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    data = Venue.query.get(venue_id).__dict__
    data["genres"] = data["genres"].translate({ord(i): None for i in '{"}'}).split(",")
    data["website"] = data["website_link"]
    del data["website_link"]  # Due to naming inconsistencies in the project files.
    data["past_shows_count"] = (
        Venue.query.join(Show)
        .filter(Venue.id == venue_id, Show.start_time < datetime.now())
        .count()
    )
    data["upcoming_shows_count"] = (
        Venue.query.join(Show)
        .filter(Venue.id == venue_id, Show.start_time > datetime.now())
        .count()
    )
    data["past_shows"] = []
    data["upcoming_shows"] = []
    for show in (
        Show.query.join(Venue)
        .filter(Venue.id == venue_id, Show.start_time < datetime.now())
        .all()
    ):
        data["past_shows"].append(
            {
                "artist_id": show.artist_id,
                "artist_name": Artist.query.filter(Artist.id == show.artist_id)
                .first()
                .name,
                "artist_image_link": Artist.query.filter(Artist.id == show.artist_id)
                .first()
                .image_link,
                "start_time": format_datetime(str(show.start_time), format="full"),
            }
        )
    for show in (
        Show.query.join(Venue)
        .filter(Venue.id == venue_id, Show.start_time > datetime.now())
        .all()
    ):
        data["upcoming_shows"].append(
            {
                "artist_id": show.artist_id,
                "artist_name": Artist.query.filter(Artist.id == show.artist_id)
                .first()
                .name,
                "artist_image_link": Artist.query.filter(Artist.id == show.artist_id)
                .first()
                .image_link,
                "start_time": format_datetime(str(show.start_time), format="full"),
            }
        )
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    error = False
    try:
        request_body = VenueForm(request.form).data
        # I have to remove csrf_token to use tuple-unpacking form, I'll preserve the original request body
        data_dict = {
            key: request_body[key] for key in request_body if key != "csrf_token"
        }
        data = Venue(**data_dict)
        db.session.add(data)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash(
            "An error occurred. Venue " + request.form["name"] + " could not be listed."
        )
    else:
        flash("Venue " + request.form["name"] + " was successfully listed!")
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    data = []
    for artist in Artist.query.all():
        data.append({"id": artist.id, "name": artist.name})
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    response = {"count": None, "data": list()}
    search_term = request.form["search_term"]
    for artist in Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all():
        response["count"] = Artist.query.filter(
            Artist.name.ilike(f"%{search_term}%")
        ).count()
        response["data"].append(
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": Artist.query.join(Show)
                .filter(Artist.id == artist.id, Show.start_time > datetime.now())
                .count(),
            }
        )

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=search_term,
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    data = Artist.query.get(artist_id).__dict__
    data["genres"] = data["genres"].translate({ord(i): None for i in '{"}'}).split(",")
    data["website"] = data["website_link"]
    del data["website_link"]  # Due to naming inconsistencies in the project files.
    data["past_shows_count"] = (
        Artist.query.join(Show)
        .filter(Artist.id == artist_id, Show.start_time < datetime.now())
        .count()
    )
    data["upcoming_shows_count"] = (
        Artist.query.join(Show)
        .filter(Artist.id == artist_id, Show.start_time > datetime.now())
        .count()
    )
    data["past_shows"] = []
    data["upcoming_shows"] = []
    for show in (
        Show.query.join(Artist)
        .filter(Artist.id == artist_id, Show.start_time < datetime.now())
        .all()
    ):
        data["past_shows"].append(
            {
                "venue_id": show.venue_id,
                "venue_name": Venue.query.filter(Venue.id == show.venue_id)
                .first()
                .name,
                "venue_image_link": Venue.query.filter(Venue.id == show.venue_id)
                .first()
                .image_link,
                "start_time": format_datetime(str(show.start_time), format="full"),
            }
        )
    for show in (
        Show.query.join(Artist)
        .filter(Artist.id == artist_id, Show.start_time > datetime.now())
        .all()
    ):
        data["upcoming_shows"].append(
            {
                "venue_id": show.venue_id,
                "venue_name": Venue.query.filter(Venue.id == show.venue_id)
                .first()
                .name,
                "venue_image_link": Venue.query.filter(Venue.id == show.venue_id)
                .first()
                .image_link,
                "start_time": format_datetime(str(show.start_time), format="full"),
            }
        )
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id).__dict__
    artist["genres"] = (
        artist["genres"].translate({ord(i): None for i in '{"}'}).split(",")
    )
    form = ArtistForm(**artist)
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    error = False
    try:
        form_body = ArtistForm(request.form).data
        artist = Artist.query.get(artist_id)
        artist.name = form_body["name"]
        artist.genres = form_body["genres"]
        artist.city = form_body["city"]
        artist.state = form_body["state"]
        artist.phone = form_body["phone"]
        artist.facebook_link = form_body["facebook_link"]
        artist.website_link = form_body["website_link"]
        artist.image_link = form_body["image_link"]
        artist.seeking_description = form_body["seeking_description"]
        artist.seeking_venue = form_body["seeking_venue"]
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id).__dict__
    venue["genres"] = (
        venue["genres"].translate({ord(i): None for i in '{"}'}).split(",")
    )
    form = VenueForm(**venue)
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    error = False
    try:
        form_body = VenueForm(request.form).data
        venue = Venue.query.get(venue_id)
        venue.name = form_body["name"]
        venue.genres = form_body["genres"]
        venue.city = form_body["city"]
        venue.state = form_body["state"]
        venue.address = form_body["address"]
        venue.phone = form_body["phone"]
        venue.facebook_link = form_body["facebook_link"]
        venue.website_link = form_body["website_link"]
        venue.image_link = form_body["image_link"]
        venue.seeking_description = form_body["seeking_description"]
        venue.seeking_talent = form_body["seeking_talent"]
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    error = False
    try:
        request_body = ArtistForm(request.form).data
        # Removing csrf_token while preserving the original request body to be able to use tuple-unpacking
        data_dict = {
            key: request_body[key] for key in request_body if key != "csrf_token"
        }
        data = Artist(**data_dict)
        db.session.add(data)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash(
            "An error occurred. Artist "
            + request.form["name"]
            + " could not be listed."
        )
    else:
        flash("Artist " + request.form["name"] + " was successfully listed!")
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    data = []
    for show in Show.query.all():
        data.append(
            {
                "venue_id": show.venue_id,
                "venue_name": Venue.query.join(Show)
                .filter(Show.id == show.id)
                .filter(Venue.id == show.venue_id)
                .first()
                .name,
                "artist_id": show.artist_id,
                "artist_name": Artist.query.join(Show)
                .filter(Show.id == show.id)
                .filter(Artist.id == show.artist_id)
                .first()
                .name,
                "artist_image_link": Artist.query.join(Show)
                .filter(Show.id == show.id)
                .filter(Artist.id == show.artist_id)
                .first()
                .image_link,
                "start_time": format_datetime(str(show.start_time), format="full"),
            }
        )
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    error = False
    try:
        request_body = ShowForm(request.form).data
        # Removing csrf_token while preserving the original request body to be able to use tuple-unpacking
        data_dict = {
            key: request_body[key] for key in request_body if key != "csrf_token"
        }
        data = Show(**data_dict)
        db.session.add(data)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash("An error occurred. Show could not be listed.")
    else:
        flash("Show was successfully listed!")
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
