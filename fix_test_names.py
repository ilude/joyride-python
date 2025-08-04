#!/usr/bin/env python3
"""Fix naming conventions in test files"""

import os
import re

# Files to fix
test_files = [
    'tests/test_event_registry.py',
    'tests/disabled/test_event_types.py',
    'tests/disabled/test_events_base.py'
]

for file_path in test_files:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} - file not found")
        continue
        
    print(f"Fixing {file_path}...")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace class names
    replacements = [
        (r'\bDNSEvent\b', 'JoyrideDNSEvent'),
        (r'\bContainerEvent\b', 'JoyrideContainerEvent'),
        (r'\bNodeEvent\b', 'JoyrideNodeEvent'),
        (r'\bFileEvent\b', 'JoyrideFileEvent'),
        (r'\bSystemEvent\b', 'JoyrideSystemEvent'),
        (r'\bErrorEvent\b', 'JoyrideErrorEvent'),
        (r'\bHealthEvent\b', 'JoyrideHealthEvent'),
        (r'\bEventFilter\b', 'JoyrideEventFilter'),
        (r'\bEventSubscription\b', 'JoyrideEventSubscription'),
        (r'\bEventRegistry\b', 'JoyrideEventRegistry'),
        (r'\bEventBus\b', 'JoyrideEventBus'),
        (r'\bEvent\b(?!\w)', 'JoyrideEvent'),  # Event but not EventFilter, etc.
        (r'\bEventHandler\b', 'JoyrideEventHandler'),
        (r'\bEventProducer\b', 'JoyrideEventProducer'),
    ]

    for old_name, new_name in replacements:
        content = re.sub(old_name, new_name, content)

    # Fix import statements
    import_replacements = [
        (r'from app\.events\.base import', 'from app.events.core import'),
        (r'from app\.events\.types import \((.*?)\)', lambda m: f"from app.events.types import ({', '.join(['Joyride' + name.strip() for name in m.group(1).split(',')])})")
    ]
    
    for pattern, replacement in import_replacements:
        if callable(replacement):
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            content = re.sub(pattern, replacement, content)

    # Write the file back
    with open(file_path, 'w') as f:
        f.write(content)

print("Fixed naming conventions in all test files")
