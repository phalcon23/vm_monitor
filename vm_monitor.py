import subprocess

def list_vms():
    try:
        # Run the `xe vm-list` command
        process = subprocess.Popen(['xe', 'vm-list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        # Check if the command was successful
        if process.returncode != 0:
            print("Error running `xe vm-list`:", stderr)
            return
        
        # Parse the output
        vms = stdout.split('\n\n')
        for vm in vms:
            if vm.strip():
                print("VM Info:")
                for line in vm.split('\n'):
                    print(line.strip())
                print()
    
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
    list_vms()