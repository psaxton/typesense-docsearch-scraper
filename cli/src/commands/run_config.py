from .abstract_command import AbstractCommand


class RunConfig(AbstractCommand):
    def get_name(self):
        return "run"

    def get_description(self):
        return "Run a config"

    def get_usage(self):
        return super(RunConfig, self).get_usage() + " config"

    def get_options(self):
        return [{"name": "config", "description": "path to the config to run"}]

    def run(self, args):
        from scraper.src.index import run_config

        self.check_not_docsearch_app_id("run a config manually")
        return run_config("C:/Users/groov/OneDrive/Documents/GitHub/typesense-docsearch-scraper/configs/public/typesense_docs.json")
    