import os
import yaml
import re
    
    
def load_profiles(filename: str) -> dict:
    """
    Loads person profiles from YAML file located in the utils directory.
    """
    current_dir = os.path.dirname(os.path.dirname(__file__))
    profiles_file = os.path.join(current_dir, "profiles", filename)
    with open(profiles_file, "r") as file:
        return yaml.safe_load(file)

