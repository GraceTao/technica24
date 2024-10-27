import requests


class Species(object):
    def __init__(self, species_json):
        self.kingdom_name = species_json["kingdom_name"]
        self.phylum_name = species_json["phylum_name"]
        self.class_name = species_json["class_name"]
        self.order_name = species_json["order_name"]
        self.family_name = species_json["family_name"]
        self.genus_name = species_json["genus_name"]
        self.scientific_name = species_json["scientific_name"]
        self.taxonomic_authority = species_json["taxonomic_authority"]

    def __repr__(self):
        return self.title


class SpeciesClient(object):
    def __init__(self, token):
        self.sess = requests.Session()
        self.base_url = f"https://apiv3.iucnredlist.org/api/v3/species/page/0?token={token}"


