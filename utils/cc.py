import json
import os

def count_command(command_name):
    file_path = '/Users/freewifi/Isotope-tts-bot/data/tts/v00/stats/commands.json'
    
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump({}, f)
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if command_name in data:
        data[command_name] += 1
    else:
        data[command_name] = 1
    

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

