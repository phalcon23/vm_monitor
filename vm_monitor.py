import subprocess  # Module to spawn new processes, connect to their input/output/error pipes, and obtain their return codes
import argparse    # Module for parsing command-line options, arguments, and sub-commands
import json        # Module for parsing JSON (JavaScript Object Notation)
import os          # Module for interacting with the operating system
import shutil      # Module for high-level file operations like copying

def clear_screen():
    """Clear the terminal screen."""
    os.system('clear')  # Use the 'clear' command to clear the terminal screen

def list_vms(debug):
    """
    List VMs using the `xe vm-list` command and save the output to a temporary file.
    
    Args:
        debug (bool): If True, print debug information.
    """
    try:
        # Run the `xe vm-list` command to list all VMs
        process = subprocess.Popen(['xe', 'vm-list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()  # Capture the command's output and error messages
        
        # Check if the command was successful
        if process.returncode != 0:
            print("Error running `xe vm-list`:", stderr)  # Print the error message if the command failed
            return
        
        if debug:
            # Debug: Print the raw output from the `xe vm-list` command
            print("Raw output from `xe vm-list` command:")
            print(stdout)
        
        # Open the file 'vm_list.tmp' in write mode
        with open('vm_list.tmp', 'w') as file:
            # Split the output into individual VMs based on double newlines
            vms = stdout.split('\n\n')
            for vm in vms:
                if vm.strip():  # Ensure the VM block is not empty
                    # Write each line of the VM block to the file
                    for line in vm.split('\n'):
                        file.write(line.strip() + '\n')
                    file.write('\n')  # Add a newline after each VM block
        
        if debug:
            # Debug: Confirm that the 'vm_list.tmp' file was created successfully
            print("vm_list.tmp file created successfully.")
    
    except Exception as e:
        # Print any exception that occurs during the process
        print("An error occurred:", str(e))

def parse_vms_to_json(debug):
    """
    Parse the temporary VM list file and save the data to a JSON file.
    
    Args:
        debug (bool): If True, print debug information.
    """
    try:
        # Open the temporary VM list file for reading
        with open('vm_list.tmp', 'r') as file:
            content = file.read()
        
        # Split the content into individual VMs based on double newlines
        vms = content.split('\n\n')
        vm_list = []
        
        # Iterate over each VM block
        for vm in vms:
            if vm.strip():  # Ensure the VM block is not empty
                vm_info = {}
                # Split each VM block into lines and process each line
                for line in vm.split('\n'):
                    if ':' in line:  # Ensure the line contains a key-value pair
                        key, value = line.split(':', 1)
                        vm_info[key.strip()] = value.strip()
                
                # Extract the VM name and filter out control domains
                name = vm_info.get("name-label ( RW)")
                if name and "Control domain" not in name:
                    # Create a JSON object for the VM
                    vm_json = {
                        "uuid": vm_info.get("uuid ( RO)"),
                        "name": name,
                        "status": vm_info.get("power-state ( RO)"),
                        "monitored": "no"
                    }
                    vm_list.append(vm_json)
        
        # Write the VM list to a JSON file
        with open('vm_list.json', 'w') as json_file:
            json.dump(vm_list, json_file, indent=4)
        
        if debug:
            # Debug: Confirm that the 'vm_list.json' file was created successfully
            print("vm_list.json file created successfully.")
    
    except Exception as e:
        # Print any exception that occurs during the process
        print("An error occurred while parsing VMs to JSON:", str(e))

def display_vms():
    """Display the list of VMs from the JSON file."""
    try:
        # Open the JSON file containing the VM list
        with open('vm_list.json', 'r') as json_file:
            vm_list = json.load(json_file)
        
        if not vm_list:
            print("No VMs found in vm_list.json.")
            return
        
        # Iterate over each VM and display its details
        for index, vm in enumerate(vm_list, start=1):
            status = vm['status']
            monitored = vm['monitored']
            name = vm['name'][:20]
            uuid = vm['uuid']
            
            # Apply color based on status and monitored values
            if status == 'running':
                status = "\033[93m{:<10}\033[0m".format(status)  # Yellow
            else:
                status = "\033[31m{:<10}\033[0m".format(status)  # Dark Red
            
            if monitored == 'yes':
                monitored = "\033[93m{:<3}\033[0m".format(monitored)  # Yellow
            else:
                monitored = "\033[31m{:<3}\033[0m".format(monitored)  # Dark Red
            
            # Add leading space for numbers under 10
            index_str = "{:2})".format(index)
            
            # Print the VM details
            print("{} Status: {} - Monit: {} - Name: {:<20} - UUID: {}".format(
                index_str, status, monitored, name, uuid))
    
    except Exception as e:
        # Print any exception that occurs during the process
        print("An error occurred while displaying VMs:", str(e))

def compare_json_files(old_file, new_file):
    """
    Compare the old and new JSON files and list any changes.
    
    Args:
        old_file (str): Path to the old JSON file.
        new_file (str): Path to the new JSON file.
    """
    try:
        # Check if the old file exists
        if not os.path.exists(old_file):
            print("Old file '{}' does not exist. Skipping comparison.".format(old_file))
            return
        
        # Load the old VM list from the JSON file
        with open(old_file, 'r') as old_json_file:
            old_vm_list = json.load(old_json_file)
        
        # Load the new VM list from the JSON file
        with open(new_file, 'r') as new_json_file:
            new_vm_list = json.load(new_json_file)
        
        # Create dictionaries for easy lookup by UUID
        old_vms = {vm['uuid']: vm for vm in old_vm_list}
        new_vms = {vm['uuid']: vm for vm in new_vm_list}
        
        # Identify added, removed, and modified VMs
        added_vms = [vm for uuid, vm in new_vms.items() if uuid not in old_vms]
        removed_vms = [vm for uuid, vm in old_vms.items() if uuid not in new_vms]
        modified_vms = [
            vm for uuid, vm in new_vms.items() if uuid in old_vms and vm != old_vms[uuid]
        ]
        
        print("\nChanges between old and new VM lists:")
        
        if added_vms:
            print("\nAdded VMs:")
            for vm in added_vms:
                print("  - Name: {:<20} - UUID: {}".format(vm['name'], vm['uuid']))
        
        if removed_vms:
            print("\nRemoved VMs:")
            for vm in removed_vms:
                print("  - Name: {:<20} - UUID: {}".format(vm['name'], vm['uuid']))
        
        if modified_vms:
            print("\nModified VMs:")
            for vm in modified_vms:
                print("  - Name: {:<20} - UUID: {}".format(vm['name'], vm['uuid']))
    
    except Exception as e:
        # Print any exception that occurs during the process
        print("An error occurred while comparing JSON files:", str(e))

def copy_old_vm_list():
    """Copy vm_list.json to vm_list_old.json if it exists."""
    if os.path.exists('vm_list.json'):
        shutil.copy('vm_list.json', 'vm_list_old.json')
        print("Copied vm_list.json to vm_list_old.json")
    else:
        print("vm_list.json does not exist. Skipping copy.")

def main():
    """Main function to run the VM monitor script."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="VM Monitor Script")
    parser.add_argument('--gui', action='store_true', help="Run the script with GUI")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    args = parser.parse_args()

    if args.gui:
        print("GUI mode is not implemented yet.")
    
    # Clear the terminal screen
    clear_screen()
    
    # Get the system name
    system_name = os.uname()[1]
    print("VMs Running on - {}".format(system_name))
    print("")
    
    # Copy the old VM list
    copy_old_vm_list()
    
    # List VMs and save to a temporary file
    list_vms(args.debug)
    
    # Parse the temporary VM list file and save to a JSON file
    parse_vms_to_json(args.debug)
    
    # Display the VMs from the JSON file
    display_vms()
    
    # Compare old and new JSON files
    compare_json_files('vm_list_old.json', 'vm_list.json')

if __name__ == "__main__":
    main()