import yaml

class GeneralUtils:

    def __init__(self):
        pass

    @staticmethod
    def read_yaml_file(file_path):
        with open(file_path, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return None