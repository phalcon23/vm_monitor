import subprocess
import json
import os
import sys

# ANSI escape codes for coloring
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'

def clear_screen():
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')

def get_vm_list():
    # Execute the xe vm-list command
    # Command to run in terminal: xe vm-list params=uuid,name-label,power-state
    result = subprocess.Popen(['xe', 'vm-list', 'params=uuid,name-label,power-state'], stdout=subprocess.PIPE)
    output, _ = result.communicate()
    return output.decode('utf-8')

def parse_vm_list(output):
    # Initialize an empty list to store VM details
    vms = []
    # Initialize an empty dictionary to store individual VM details
    vm = {}
    # Iterate over each line in the command output
    for line in output.splitlines():
        # Strip leading and trailing whitespace
        line = line.strip()
        # Check if the line contains the UUID
        if line.startswith('uuid ( RO)'):
            # If vm dictionary is not empty, append it to the vms list
            if vm and 'Control domain on host' not in vm.get('name', ''):
                vms.append(vm)
                vm = {}
            # Extract and store the UUID
            vm['uuid'] = line.split(':', 1)[1].strip()
        # Check if the line contains the name-label
        elif line.startswith('name-label ( RW)'):
            # Extract and store the name-label
            vm['name'] = line.split(':', 1)[1].strip()
        # Check if the line contains the power-state
        elif line.startswith('power-state ( RO)'):
            # Extract and store the power-state
            vm['state'] = line.split(':', 1)[1].strip()
    # Append the last VM to the list if it exists and does not contain "Control domain on host"
    if vm and 'Control domain on host' not in vm.get('name', ''):
        vms.append(vm)
    return vms

def read_json_file(filename):
    # Read the existing JSON file
    if os.path.exists(filename):
        with open(filename, 'r') as json_file:
            return json.load(json_file)
    return []

def write_to_json_file(data, filename):
    # Open the specified file in write mode
    with open(filename, 'w') as json_file:
        # Write the data to the file in JSON format
        json.dump(data, json_file, indent=4)

def update_vm_list(existing_vms, new_vms):
    # Create a dictionary for quick lookup of existing VMs by UUID
    existing_vms_dict = {vm['uuid']: vm for vm in existing_vms}
    new_vms_dict = {vm['uuid']: vm for vm in new_vms}
    
    # Track changes for debugging
    changes = []

    # Iterate over new VMs and update the existing list
    for new_vm in new_vms:
        uuid = new_vm['uuid']
        if uuid in existing_vms_dict:
            # Update the existing VM entry if there are changes
            existing_vm = existing_vms_dict[uuid]
            if existing_vm['name'] != new_vm['name'] or existing_vm['state'] != new_vm['state']:
                changes.append("Updated VM: {}, Name: {} -> {}, State: {} -> {}".format(
                    uuid, existing_vm['name'], new_vm['name'], existing_vm['state'], new_vm['state']))
                existing_vm['name'] = new_vm['name']
                existing_vm['state'] = new_vm['state']
            # Ensure the 'monitored' field is present and valid
            if 'monitored' not in existing_vm or existing_vm['monitored'] not in ['yes', 'no']:
                changes.append("Updated VM: {}, Monitored: {} -> no".format(
                    uuid, existing_vm.get('monitored', 'N/A')))
                existing_vm['monitored'] = 'no'
        else:
            # Add new VM entry with default 'monitored' status
            new_vm['monitored'] = 'no'
            changes.append("Added VM: {}, Name: {}, State: {}".format(
                uuid, new_vm['name'], new_vm['state']))
            existing_vms.append(new_vm)
    
    # Remove VMs that are no longer present in the new VM list
    for uuid in list(existing_vms_dict.keys()):
        if uuid not in new_vms_dict:
            changes.append("Removed VM: {}, Name: {}, State: {}".format(
                uuid, existing_vms_dict[uuid]['name'], existing_vms_dict[uuid]['state']))
            existing_vms = [vm for vm in existing_vms if vm['uuid'] != uuid]
    
    return existing_vms, changes

def colorize_state(state):
    if state == 'running':
        return GREEN + state.ljust(10)[:10] + RESET
    elif state == 'halted':
        return RED + state.ljust(10)[:10] + RESET
    else:
        return state.ljust(10)[:10]

def colorize_monitored(monitored):
    if monitored == 'yes':
        return GREEN + monitored.ljust(3) + RESET
    elif monitored == 'no':
        return RED + monitored.ljust(3) + RESET
    else:
        return monitored.ljust(3)

if __name__ == "__main__":
    # Check for --gui argument
    if '--gui' not in sys.argv:
        print("GUI mode not enabled. Exiting.")
        exit()

    while True:
        # Clear the screen
        clear_screen()
        
        # Get the VM list by executing the command
        output = get_vm_list()
        
        # Write the command output to a temporary file for debugging
        with open('vm_list.tmp', 'w') as tmp_file:
            tmp_file.write(output)
        
        # Read the command output from the temporary file
        with open('vm_list.tmp', 'r') as tmp_file:
            output = tmp_file.read()
        
        # Parse the command output to extract VM details
        new_vm_list = parse_vm_list(output)
        
        # Read the existing VM details from the JSON file
        existing_vm_list = read_json_file('vm_list.json')
        
        # Update the existing VM list with new VM details
        updated_vm_list, changes = update_vm_list(existing_vm_list, new_vm_list)
        
        # Always print VM details (debug always on)
        print("Changes made to the JSON file:")
        for change in changes:
            print(change)
        print("\nUpdated VM List:")
        for index, vm in enumerate(updated_vm_list, start=1):
            state_colored = colorize_state(vm.get('state', 'N/A'))
            monitored_colored = colorize_monitored(vm.get('monitored', 'no'))
            name_formatted = vm.get('name', 'N/A').ljust(20)[:20]
            index_formatted = "{:2})".format(index)
            print("{} State: {} - Monit: {} - Name: {} - UUID: {}".format(index_formatted, state_colored, monitored_colored, name_formatted, vm['uuid']))
        
        # Write the updated VM details to the JSON file
        write_to_json_file(updated_vm_list, 'vm_list.json')
        
        # Prompt the user to enter a VM number to toggle the monitor status
        while True:
            try:
                vm_number_str = raw_input("\nEnter VM number to toggle monitor status (or 0 to exit): ")
                if vm_number_str.isdigit():
                    vm_number = int(vm_number_str)
                    if vm_number == 0:
                        exit()
                    elif vm_number > 0 and vm_number <= len(updated_vm_list):
                        selected_vm = updated_vm_list[vm_number - 1]
                        selected_vm['monitored'] = 'yes' if selected_vm['monitored'] == 'no' else 'no'
                        print("Toggled monitor status for VM: {}".format(selected_vm['name']))
                        # Write the updated VM details to the JSON file
                        write_to_json_file(updated_vm_list, 'vm_list.json')
                        break
                    else:
                        print("Invalid VM number.")
                else:
                    print("Invalid input. Please enter a number.")
            except Exception as e:
                print("An error occurred: {}".format(e))