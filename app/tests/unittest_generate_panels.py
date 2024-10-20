import unittest
from app.generate.generate_panels import generate_panels  # Adjust import based on your module structure
import json

class TestGeneratePanels(unittest.TestCase):
    def setUp(self):
        # Set up the scenario for the tests
        self.scenario = {
            "description": "Adrien and Vincent want to start a new product, and they create it in one night before presenting it to the board.",
            "characters": [
                {"id": 0, "name": "Adrien", "appearance": "A guy with blond hair wearing glasses."},
                {"id": 1, "name": "Vincent", "appearance": "A black guy with black hair and a beard"},
            ],
        }
        self.num_panels = 2

    def test_generate_panels_structure(self):
        # Call the generate_panels function and get the result
        result = generate_panels(self.scenario, self.num_panels)

        # Check if the result is not None
        self.assertIsNotNone(result)

        # Check if the result matches the expected structure
        self.assertIn('title', result)
        self.assertIn('genre', result)
        self.assertIn('keywords', result)
        self.assertIn('panels', result)

    def test_generate_panels_content(self):
        # Call the generate_panels function and get the result
        result = generate_panels(self.scenario, self.num_panels)

        # Example assertions for expected content
        panels = result["panels"]
        self.assertGreater(len(panels), 0)

        # Check each panel for structure
        for panel in panels:
            self.assertIn('index', panel)
            self.assertIn('description', panel)
            self.assertIn('text', panel)

    def test_invalid_scenario(self):
        # Test for invalid scenario input (e.g., missing fields)
        with self.assertRaises(ValueError):
            generate_panels({}, self.num_panels)  # Pass an invalid scenario

if __name__ == '__main__':
    unittest.main()
