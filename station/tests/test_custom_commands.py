"""
Tests for the custom command functionality.

This module tests the custom command feature that allows users to specify
custom commands for satellite recipes.
"""

import unittest
import os
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Set up test environment before imports
os.environ["SVAROG_CONFIG_DIR"] = "tests/config"

from utils.configuration import open_config, save_config
from utils.models import SatelliteConfiguration
from recipes.factory import execute_recipe, get_recipe
from metadata import Metadata


class TestCustomCommands(unittest.TestCase):
    """Test cases for custom command functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create test config directory
        self.config_dir = "tests/config"
        os.makedirs(self.config_dir, exist_ok=True)

        # Create test configuration
        self.test_config = {
            'aos_at': 12,
            'location': {
                'elevation': 123,
                'latitude': 45.6,
                'longitude': 78.9,
                'name': 'Test Station'
            },
            'max_elevation_greater_than': 0,
            'norad': ['https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle'],
            'satellites': [
                {
                    'freq': '137.62e6',
                    'name': 'NOAA 15',
                    'recipe': 'noaa-apt'
                },
                {
                    'freq': '137.9e6',
                    'name': 'METEOR-M2 3',
                    'recipe': 'satdump',
                    'custom_command': 'satdump -i airspy0 -v'
                },
                {
                    'freq': '137.1e6',
                    'name': 'NOAA 19',
                    'recipe': 'noaa-apt'
                }
            ],
            'server': {
                'id': 1,
                'secret': '1234567890abcdef01234567890abcde',
                'url': 'http://127.0.0.1:5000/receive'
            },
            'strategy': 'max-elevation'
        }

        # Save test configuration
        config_path = os.path.join(self.config_dir, "config.yml")
        save_config(self.test_config)

        # Create temporary observation directory
        self.temp_obs_dir = tempfile.mkdtemp(prefix="test_obs_")

    def tearDown(self):
        """Clean up test environment."""
        # Remove test config directory
        shutil.rmtree(self.config_dir, ignore_errors=True)

        # Remove temporary observation directory
        shutil.rmtree(self.temp_obs_dir, ignore_errors=True)

    def test_satellite_configuration_with_custom_command(self):
        """Test that satellite configuration can have custom_command field."""
        config = open_config()
        meteor_sat = next(s for s in config['satellites'] if s['name'] == 'METEOR-M2 3')

        self.assertIn('custom_command', meteor_sat)
        self.assertEqual(meteor_sat['custom_command'], 'satdump -i airspy0 -v')
        self.assertEqual(meteor_sat['recipe'], 'satdump')

    def test_satellite_configuration_without_custom_command(self):
        """Test that satellite configuration works without custom_command field."""
        config = open_config()
        noaa_sat = next(s for s in config['satellites'] if s['name'] == 'NOAA 15')

        self.assertNotIn('custom_command', noaa_sat)
        self.assertEqual(noaa_sat['recipe'], 'noaa-apt')

    def test_get_recipe_with_custom_command(self):
        """Test that get_recipe function works with custom_command field."""
        config = open_config()
        meteor_sat = next(s for s in config['satellites'] if s['name'] == 'METEOR-M2 3')

        recipe_func, recipe_name = get_recipe(meteor_sat)

        self.assertEqual(recipe_name, 'satdump')
        self.assertIsNotNone(recipe_func)

    def test_recipe_function_signatures(self):
        """Test that all recipes accept custom_command parameter."""
        from recipes import satdump, noaa_apt, meteor_qpsk, noaa_apt_gr

        # Check that all recipe execute functions have custom_command parameter
        import inspect

        recipes = [satdump, noaa_apt, meteor_qpsk, noaa_apt_gr]

        for recipe in recipes:
            sig = inspect.signature(recipe.execute)
            params = list(sig.parameters.keys())

            # Should have custom_command parameter (after metadata)
            self.assertIn('custom_command', params)

            # custom_command should be after metadata
            metadata_index = params.index('metadata')
            custom_command_index = params.index('custom_command')
            self.assertGreater(custom_command_index, metadata_index)

    def test_configuration_round_trip(self):
        """Test that custom_command survives configuration save/load cycle."""
        # Create satellite with custom command
        satellite = {
            'freq': '137.9e6',
            'name': 'TEST-SAT',
            'recipe': 'satdump',
            'custom_command': 'test-command -v'
        }

        # Add to config
        config = open_config()
        config['satellites'].append(satellite)
        save_config(config)

        # Reload config
        new_config = open_config()
        test_sat = next(s for s in new_config['satellites'] if s['name'] == 'TEST-SAT')

        # Check that custom_command is preserved
        self.assertEqual(test_sat['custom_command'], 'test-command -v')

    def test_empty_custom_command_handling(self):
        """Test that empty custom_command is handled correctly."""
        config = open_config()

        # Add satellite with empty custom command
        satellite = {
            'freq': '137.1e6',
            'name': 'EMPTY-SAT',
            'recipe': 'satdump',
            'custom_command': ''
        }

        config['satellites'].append(satellite)
        save_config(config)

        # Reload and check
        new_config = open_config()
        empty_sat = next(s for s in new_config['satellites'] if s['name'] == 'EMPTY-SAT')

        # Empty string should be preserved
        self.assertEqual(empty_sat['custom_command'], '')

    def test_custom_command_parameter_passing(self):
        """Test that custom_command parameter is passed correctly through the chain."""
        # This test verifies that the custom_command parameter flows correctly
        # through the execution chain without actually executing recipes

        config = open_config()
        meteor_sat = next(s for s in config['satellites'] if s['name'] == 'METEOR-M2 3')

        # Verify the satellite has custom_command
        self.assertEqual(meteor_sat['custom_command'], 'satdump -i airspy0 -v')

        # Test that get_recipe works with custom_command
        recipe_func, recipe_name = get_recipe(meteor_sat)
        self.assertEqual(recipe_name, 'satdump')

        # Test that the recipe function signature accepts custom_command
        import inspect
        sig = inspect.signature(recipe_func)
        params = list(sig.parameters.keys())
        self.assertIn('custom_command', params)

    def test_satdump_recipe_custom_command_logic(self):
        """Test that satdump recipe logic handles custom_command correctly."""
        from recipes.satdump import execute

        # Test the logic without actually executing commands
        metadata = Metadata()

        # Test with custom command - use keyword arguments to avoid conflicts
        results = execute(working_dir='/tmp/test',
                         frequency='137.9e6',
                         duration=timedelta(minutes=10),
                         metadata=metadata,
                         custom_command='custom-satdump-command',
                         sh=None)

        # Check that the recipe returns expected results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 'RAW')

        # Test without custom command (should use default) - use keyword arguments
        results = execute(working_dir='/tmp/test',
                         frequency='137.9e6',
                         duration=timedelta(minutes=10),
                         metadata=metadata,
                         custom_command=None,
                         sh=None)

        # Check that the recipe returns expected results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 'RAW')

    def test_metadata_custom_command_storage(self):
        """Test that custom_command is stored in metadata."""
        config = open_config()
        meteor_sat = next(s for s in config['satellites'] if s['name'] == 'METEOR-M2 3')

        metadata = Metadata()
        los_time = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Mock the recipe execution to avoid actual file operations
        with patch('recipes.satdump.execute') as mock_execute:
            mock_execute.return_value = [('RAW', '/tmp/test.raw')]

            results, obs_dir, updated_metadata = execute_recipe(meteor_sat, los_time, metadata)

            # Check that custom_command is in metadata
            self.assertEqual(updated_metadata.get('custom_command'), 'satdump -i airspy0 -v')
            self.assertEqual(updated_metadata.get('recipe'), 'satdump')
            self.assertEqual(updated_metadata.get('frequency'), '137.9e6')

    def test_custom_command_field_in_models(self):
        """Test that custom_command field is properly defined in models."""
        # Test that SatelliteConfiguration includes custom_command
        from utils.models import SatelliteConfiguration

        # Create a satellite config with custom_command
        sat_config = SatelliteConfiguration(
            freq='137.9e6',
            name='TEST-SAT',
            recipe='satdump',
            custom_command='test-command'
        )

        # Verify the field is present
        self.assertEqual(sat_config['custom_command'], 'test-command')
        self.assertEqual(sat_config['freq'], '137.9e6')
        self.assertEqual(sat_config['name'], 'TEST-SAT')
        self.assertEqual(sat_config['recipe'], 'satdump')

    def test_custom_command_validation(self):
        """Test that custom_command can contain various command formats."""
        test_commands = [
            'satdump -i airspy0 -v',
            'satdump -i airspy0 --frequency 137.9M',
            'custom_script.sh --debug --verbose',
            'python3 /usr/local/bin/satdump --config custom.conf',
            'docker run satdump:latest -i airspy0'
        ]

        # Test each command individually
        for i, cmd in enumerate(test_commands):
            with self.subTest(cmd=cmd):
                # Create a fresh config for each test
                test_config = self.test_config.copy()
                test_config['satellites'] = test_config['satellites'].copy()

                # Create satellite with this command
                satellite = {
                    'freq': '137.9e6',
                    'name': f'TEST-SAT-{i}',
                    'recipe': 'satdump',
                    'custom_command': cmd
                }

                # Add to config
                test_config['satellites'].append(satellite)
                save_config(test_config)

                # Reload and verify
                new_config = open_config()
                test_sat = next(s for s in new_config['satellites'] if s['name'] == satellite['name'])
                self.assertEqual(test_sat['custom_command'], cmd)


if __name__ == '__main__':
    unittest.main()
