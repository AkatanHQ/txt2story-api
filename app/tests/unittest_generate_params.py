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

if __name__ == '__main__':
    unittest.main()
