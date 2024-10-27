import base64,io
from io import BytesIO
from flask import Blueprint, render_template, url_for, redirect, request, flash
from flask_login import current_user

from .. import species_client
from ..forms import MovieReviewForm, SearchForm
from ..models import User, Comment
from ..utils import current_time

import requests
import openai


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

    searchform = SearchForm()

    if searchform.validate_on_submit():
        return redirect(url_for("species.search_results", query=searchform.search_query.data))
    
    species = species_client.get_random_species()

    return render_template("index.html", form=searchform, species_of_the_day=species)

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

    reviews = Comment.objects(commenter=user) if user else None

    return render_template("user_detail.html", error=error, username=username, image=image, reviews=reviews)

@species.route("/species-detail/<species_name>")
def species_detail(species_name):
    image_url = get_image_url(species_name)
    description = get_description(species_name)
    species = species_client.get_species_by_name(species_name)
    return render_template("species_detail.html", species=species, form=None, image_url=image_url, description=description)


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
    