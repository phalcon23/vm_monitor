import subprocess
import argparse
import json
import os

def clear_screen():
    os.system('clear')

def list_vms(debug):
    try:
        # Run the `xe vm-list` command
        process = subprocess.Popen(['xe', 'vm-list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        # Check if the command was successful
        if process.returncode != 0:
            print("Error running `xe vm-list`:", stderr)
            return
        
        if debug:
            # Debug: Print the raw output
            print("Raw output from `xe vm-list` command:")
            print(stdout)
        
        # Open the file in write mode
        with open('vm_list.tmp', 'w') as file:
            # Parse the output
            vms = stdout.split('\n\n')
            for vm in vms:
                if vm.strip():
                    for line in vm.split('\n'):
                        file.write(line.strip() + '\n')
                    file.write('\n')
        
        if debug:
            # Debug: Confirm file creation
            print("vm_list.tmp file created successfully.")
    
    except Exception as e:
        print("An error occurred:", str(e))

def parse_vms_to_json(debug):
    try:
        with open('vm_list.tmp', 'r') as file:
            content = file.read()
        
        vms = content.split('\n\n')
        vm_list = []
        
        for vm in vms:
            if vm.strip():
                vm_info = {}
                for line in vm.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        vm_info[key.strip()] = value.strip()
                
                name = vm_info.get("name-label ( RW)")
                if name and "Control domain" not in name:
                    vm_json = {
                        "uuid": vm_info.get("uuid ( RO)"),
                        "name": name,
                        "status": vm_info.get("power-state ( RO)"),
                        "monitored": "no"
                    }
                    vm_list.append(vm_json)
        
        with open('vm_list.json', 'w') as json_file:
            json.dump(vm_list, json_file, indent=4)
        
        if debug:
            print("vm_list.json file created successfully.")
    
    except Exception as e:
        print("An error occurred while parsing VMs to JSON:", str(e))

def display_vms():
    try:
        with open('vm_list.json', 'r') as json_file:
            vm_list = json.load(json_file)
        
        if not vm_list:
            print("No VMs found in vm_list.json.")
            return
        
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
            
            print("{} Status: {} - Monit: {} - Name: {:<20} - UUID: {}".format(
                index_str, status, monitored, name, uuid))
    
    except Exception as e:
        print("An error occurred while displaying VMs:", str(e))

def main():
    parser = argparse.ArgumentParser(description="VM Monitor Script")
    parser.add_argument('--gui', action='store_true', help="Run the script with GUI")
    parser.add_argument('--debug', action='store_true', help="Enable debug output")
    args = parser.parse_args()

    if args.gui:
        print("GUI mode is not implemented yet.")
    
    clear_screen()
    system_name = os.uname()[1]
    print("VMs Running on - {}".format(system_name))
    print("")
    
    list_vms(args.debug)
    parse_vms_to_json(args.debug)
    display_vms()

if __name__ == "__main__":
    main()