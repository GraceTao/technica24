import requests, random
from rapidfuzz import process, fuzz


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
        self.common_name = species_json["main_common_name"]
        # self.img_url = self.get_species_image()

    def __repr__(self):
        return self.scientific_name


class SpeciesClient(object):
    def __init__(self, token):
        self.sess = requests.Session()
        self.base_url = f"https://apiv3.iucnredlist.org/api/v3/species/page/0?token={token}"
        self.species_list = self.fetch_all_species()

    def fetch_all_species(self):
        # Fetch species list once during initialization
        resp = self.sess.get(self.base_url)
        if resp.status_code == 200:
            species_data = resp.json()['result']
            return [Species(species) for species in species_data]
        else:
            print("Failed to fetch species data")
            return []

    def get_random_species(self):
        return random.choice(self.species_list) if self.species_list else None
    
    def get_species_by_name(self, name):
        for species in self.species_list:
            if species.scientific_name == name or species.common_name == name:
                return species
        return None
    
    def search_species(self, query):
        # Returns the top 10 matches based on the similarity ratio
        scientific_names = [species.scientific_name for species in self.species_list]

        # Use RapidFuzz to find the top matches based on the scientific names
        results = process.extract(query, scientific_names, scorer=fuzz.token_sort_ratio, limit=10)

        # Retrieve the corresponding Species objects based on the matched indices
        matched_species = [self.species_list[scientific_names.index(result[0])] for result in results]

        return matched_species
