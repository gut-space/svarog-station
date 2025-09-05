# Custom Commands for Satellite Pipelines

This document describes the custom command functionality that allows users to specify custom commands for satellite reception pipelines.

## Overview

The ground station software now supports custom commands that can be specified in the satellite configuration. This allows users to override the default commands used by pipelines with their own custom commands.

## Configuration

### Adding Custom Commands

To specify a custom command for a satellite, add a `custom_command` field to the satellite configuration in `config.yml`:

```yaml
satellites:
- freq: 137.9e6
  name: METEOR-M2 3
  pipeline: satdump
  custom_command: "satdump -i airspy0 -v"
  save_to_disk: ALL
```

### CLI Management

You can manage custom commands using the CLI:

```bash
# Set custom command for a satellite
python cli.py config sat "METEOR-M2 3" --custom-command "satdump -i airspy0 -v"

# Remove custom command (set to empty string)
python cli.py config sat "METEOR-M2 3" --custom-command ""

# View current configuration
python cli.py config sat "METEOR-M2 3"
```

## Pipeline Integration

### How It Works

1. **Configuration Parsing**: The `custom_command` field is parsed from the satellite configuration
2. **Pipeline Execution**: Custom commands are passed to pipelines via the `execute_pipeline` function
3. **Pipeline Usage**: Pipelines can use the custom commands to override default behavior

### Pipeline Function Signature

All pipelines now accept a `custom_command` parameter:

```python
@set_sh_defaults
def execute(working_dir: str, frequency: str, duration: timedelta, metadata, custom_command=None, sh=None):
    # Use custom_command if provided, otherwise use default
    if custom_command:
        cmd = custom_command
    else:
        cmd = "default_command"

    # Execute the command...
```

### Example: Satdump Pipeline

The satdump pipeline demonstrates how to use custom commands:

```python
# Use custom command if provided, otherwise use default
if custom_command:
    cmd = custom_command
else:
    cmd = "./satdump record thoutput --samplerate 3e6 --frequency 137e6 --baseband_format cf32 --source airspy --timeout 10"

print(f"Executing command: {cmd}")
```

## Metadata

Custom commands are also stored in the observation metadata:

- **Field**: `custom_command`
- **Value**: The custom command string specified in the configuration
- **Access**: `metadata.get('custom_command')`

## Use Cases

### 1. Custom SDR Device Selection
```yaml
custom_command: "satdump -i airspy0 -v"
```

### 2. Custom Frequency and Sample Rate
```yaml
custom_command: "satdump -i airspy0 --frequency 137.9M --samplerate 2.4M"
```

### 3. Custom Output Format
```yaml
custom_command: "satdump -i airspy0 --output_format wav --output_file custom_output"
```

### 4. Debug Mode
```yaml
custom_command: "satdump -i airspy0 -v --debug --log_level DEBUG"
```

## Backward Compatibility

- **Existing Configurations**: Continue to work without modification
- **Pipelines**: All existing pipelines have been updated to accept the new parameter
- **Default Behavior**: If no `custom_command` is specified, pipelines use their default commands

## Implementation Details

### Files Modified

1. **`station/utils/models.py`**: Added `custom_command` field to `SatelliteConfiguration`
2. **`station/cli.py`**: Added `--custom-command` argument and handling logic
3. **`station/pipelines/factory.py`**: Modified pipeline execution to pass custom commands
4. **`station/pipelines/satdump.py`**: Updated to use custom commands
5. **Other pipelines**: Updated function signatures for consistency

### Data Flow

```
config.yml → CLI → SatelliteConfiguration → execute_pipeline → Pipeline → custom_command
```

## Testing

The functionality can be tested using:

```bash
# Test CLI help
python cli.py config sat --help

# Test setting custom commands
python cli.py config sat "METEOR-M2 3" --custom-command "satdump -i airspy0 -v"

# Test pipeline execution (in test environment)
python -c "
from pipelines.factory import execute_pipeline
from utils.configuration import open_config
from metadata import Metadata
import datetime

config = open_config()
sat = next(s for s in config['satellites'] if s['name'] == 'METEOR-M2 3')
metadata = Metadata()
results, dir, updated_metadata = execute_pipeline(sat, datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10), metadata)
print('Custom command:', updated_metadata.get('custom_command'))
"
```

## Future Enhancements

Potential future improvements:

1. **Command Validation**: Validate custom commands before execution
2. **Template System**: Support for parameterized commands with variables
3. **Command History**: Track and log executed commands
4. **Safety Checks**: Prevent execution of potentially dangerous commands
5. **Environment Variables**: Support for environment variable substitution in commands
