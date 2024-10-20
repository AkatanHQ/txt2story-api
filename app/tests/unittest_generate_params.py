import unittest
from app.generate.generate_params import ParamTextGenerator

class TestParamTextGenerator(unittest.TestCase):
    def setUp(self):
        # Set up the ParamTextGenerator instance
        self.generator = ParamTextGenerator()

    def test_generate_title(self):
        # Input scenes
        scenes = "Scene 1: A dark and stormy night. Scene 2: A mysterious figure appears. Title suggestion: Shadows in the Storm"
        
        # Expected title (this is the actual outcome you're verifying)
        expected_title = "Shadows in the Storm"
        
        # Call the generate_title function and get the result
        result = self.generator.generate_title(scenes)
        
        # Check if the result matches the expected title
        self.assertEqual(result, expected_title)

    def test_generate_character_description(self):
        # Input characters
        characters = [
            {
                'id': 1,
                'name': 'Gabriel',
                'appearance': 'A tall blond guy with glasses',
                'description': '',
                'picture': None
            },
            {
                'id': 2,
                'name': 'Draco',
                'appearance': 'A black short guy with muscles and glasses',
                'description': '',
                'picture': None
            }
        ]
        
        # Call the generate_character_description function and get the result
        result = self.generator.generate_character_description(characters)
        print(result)
        
        # Check that the result is a list
        self.assertIsInstance(result, list)
        
        # Check the structure of each item in the result list
        for character in result:
            # Ensure each item is a dictionary
            self.assertIsInstance(character, dict)
            
            # Ensure the dictionary has 'name' and 'description' keys
            self.assertIn('name', character)
            self.assertIn('description', character)
            
            # Ensure 'name' is a string
            self.assertIsInstance(character['name'], str)
            
            # Ensure 'description' is a string
            self.assertIsInstance(character['description'], str)

if __name__ == '__main__':
    unittest.main()
