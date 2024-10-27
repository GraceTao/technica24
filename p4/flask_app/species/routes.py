import base64,io
from io import BytesIO
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user

from .. import species_client
from ..forms import CommentForm, SearchForm
from ..models import User, Comment
from ..utils import current_time

import requests
import openai
import json, folium
from flask import Markup
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut


species = Blueprint("species", __name__)
""" ************ Helper for pictures uses username to get their profile picture************ """
def get_b64_img(username):
    user = User.objects(username=username).first()
    bytes_im = io.BytesIO(user.profile_pic.read())
    image = base64.b64encode(bytes_im.getvalue()).decode()
    return image

""" ************ View functions ************ """

@species.route("/", methods=["GET", "POST"])
def index():
    m = None
    searchform = SearchForm()

    if searchform.validate_on_submit():
        return redirect(url_for("species.search_results", query=searchform.search_query.data))

    if current_user.is_authenticated:
        countries = get_liked_species_locations(current_user.liked_species)
        print(current_user.liked_species)
        m = folium.Map(zoom_start=3)
        for species_data in countries:
        # Add points for countries with the species
            for entry in species_data['result']:
                country = entry['country']
                presence = entry['presence']
                if presence == 'Extant':
                    coords = get_coordinates(country)
                    if coords:
                        folium.Marker(
                            location=coords,
                            popup=f'Species: {species_data["name"]}',
                            icon=folium.Icon(color='green')
                        ).add_to(m)

        m = Markup(m._repr_html_())

    return render_template("index.html", form=searchform, species_of_the_day=species_client.species_of_the_day, map=m)

@species.route("/all-species")
def all_species():

    searchform = SearchForm()

    if searchform.validate_on_submit():
        return redirect(url_for("species.search_results", query=searchform.search_query.data))
    
    return render_template("archive.html", results=species_client.species_list, form=searchform)

@species.route("/search-results/<query>", methods=["GET"])
def search_results(query):
    
    try:
        results = species_client.search_species(query)
    except ValueError as e:
        return render_template("archive.html", error_msg=str(e), form=None)

    return render_template("archive.html", results=results, form=None)

@species.route("/user-detail/<username>")
def user_detail(username):
    user = User.objects(username=username).first()
    error = None if user else f"user {username} does not exist"
    # img = get_b64_img(user.username) use their username for helper function
    bytes_im = BytesIO(user.profile_pic.read())
    image = base64.b64encode(bytes_im.getvalue()).decode() if bytes_im else None

    comments = Comment.objects(commenter=user) if user else None

    return render_template("user_detail.html", error=error, username=username, image=image, comments=comments)

@species.route("/species-detail/<species_name>", methods=["GET", "POST"])
def species_detail(species_name):

    try:
        image_url = get_image_url(species_name)
        description = get_description(species_name)
        species = species_client.get_species_by_name(species_name)
    except ValueError as e:
        return render_template("species_detail.html", error_msg=str(e))

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            commenter=current_user._get_current_object(),
            content=form.text.data,
            date=current_time(),
            species_name=species_name,
        )

        comment.save()

        # current_user.update(add_to_set__liked_species=species_name)
        if species_name not in current_user.liked_species:
            current_user.liked_species.append(species_name)
            current_user.save()

        return redirect(request.path)

    comments = Comment.objects(species_name=species_name)
    return render_template("species_detail.html", species=species, comment_form=form, image_url=image_url, description=description, comments=comments)


def get_image_url(species_name):
    base_url = "https://api.inaturalist.org/v1/taxa"
    params = {
        "q": species_name,
        "rank": "species"
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['results']:
            species = data['results'][0]
            if species['default_photo']:
                return species['default_photo']['medium_url']
    return None


def generate_text(prompt, api_key):
    # Set up the OpenAI API key
    openai.api_key = api_key

    # Make a request to the OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Specify the model
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the generated text from the response
    ret = dict()
    ret['response'] = response['choices'][0]['message']['content']

    #generated_text = response['choices'][0]['message']['content']
    #return generated_text
    return ret

def get_description(species_name):
    api_key = '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'
    prompt = "The species is " + species_name
    prompt += ''' We are looking at the species Brief description of species along with picture
          Where is the species originally from (country/region)?
        Where are species kept/located?
        How many members of the species are left?
        What is the species' risk of extinction?
        Organizations or charities to donate to
        Please include their links for each
'''

    # Generate text based on the prompt
    return generate_text(prompt, api_key)["response"]
    
def get_liked_species_locations(species_list):
    countries = []
    token = "9bb4facb6d23f48efbf424bb05c0c1ef1cf6f468393bc745d42179ac4aca5fee"
    for species in species_list:
        url = f"https://apiv3.iucnredlist.org/api/v3/species/countries/name/{species.replace(' ', '%20')}?token={token}"  # Update to the actual endpoint from the docs

        headers = {
            "accept": "application/json"  # Specify that we accept JSON responses
        }

        response = requests.get(url, headers=headers)
        print(response.json())
        if response.status_code == 200:
            data = response.json()  # Parse JSON response if the request is successful
        else:
            print(f"Error: {response.status_code} - {response.text}")

        countries.append(data)
    return countries

# Function to get coordinates for a country
def get_coordinates(country_name):
    geolocator = Nominatim(user_agent="species_locator")
    try:
        location = geolocator.geocode(country_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            print(f"Coordinates not found for: {country_name}")
            return None
    except GeocoderTimedOut:
        return get_coordinates(country_name)  # Retry if timed out

