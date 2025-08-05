from pyscicat.client import ScicatClient
import json
import sys
import os
from pathlib import Path

ENERGY_SCAN_TEMPLATE = {
    "XAS-4.0.2": {
        "header": "Flying Beamline Energy (763, 813, 0.1, 0)\t",
        "subheader": "EPU\tPolarization",
        "body": {
            "epu": [f"100\t", f"190\t"],
        },
    },
    "XLD-4.0.2": {
        "header": "Flying Beamline Energy (763, 813, 0.1, 0)",
        "subheader": "EPU\tPolarization",
        "body": {
            "epu": [f"100\t", f"190\t"],
        },
    },
    "XAS-6.3.1": {
        "header": "Flying Energy (763, 813, 0.1, 0)",
        "subheader": "Theta\tY_samples\tZ_samples\tMagnet Field\tPolarization",
        "body": "",
    },
    "XLD-6.3.1": {
        "header": "Flying Energy (500, 600, 0.1, 1)", # does it matter that these are different?
        "subheader": "Theta\tY_samples\tZ_samples\tMagnet\tField Polarization",
        "body": "",
    },
    "XMCD-6.3.1": {
        "header": "Flying Energy (763, 813, 0.1, 1)",
        "subheader": "Theta\tY_samples\tZ_samples\tMagnet\tField Polarization",
        "body": "",
    },
    "constants": {
        "zero_input": f"0\t",
        "neg_one": f"-1\t",
        "save": f"File\n", 
    }
}

ELEMENT_ENERGY_RANGE = {
    "O": "flying(533.1, 553.1, 0.1, 1)", # K edges: 543.1 EV
    "Al": "(1549.6, 1569.6, 0.1, 1)", # K edges: 1559.6 EV
    "Si": "(1829, 1839, 0.1, 1)", # 1839 EV
    "Ti": "(433.8, 480.2, 0.1, 1)", # L edges: 453.8 EV - 460.2 EV
    "V": "(492.1, 539.8, 0.1, 1)", # L edges: 512.1 EV - 519.8 EV
    "Cr": "(554.1, 593.8, 0.1, 1)", # L edges: 574.1 EV - 583.8 EV
    "Mn": "(618.7, 669.9, 0.1, 1)", # L edges: 638.7 EV - 649.9 EV
    "Fe": "(686.8, 739.9, 0.1, 1)", # L edges: 706.8 EV - 719.9 EV
    "Co": "(758.1, 823.2, 0.1, 1)", # L eddges: 778.1 EV - 793.2 EV
    "Ni": "(832.7, 890.0, 0.1, 1)", # L edges: 852.7 EV - 870.0 EV
    "Cu": "(912.7, 972.3, 0.1, 1)", # L edges: 932.7 EV - 952.3 EV
}

def build_XAS_402_body(config, scan_body, zero, energy_element_tag, repititions, save):
    epu = ENERGY_SCAN_TEMPLATE["XAS-4.0.2"]["body"]["epu"]
    for n in range(repititions):
        scan_body.extend([
            epu[0], energy_element_tag, epu[1], energy_element_tag, save,
            epu[1], energy_element_tag, epu[0], energy_element_tag, save
        ])
    return "".join(scan_body)

def build_XLD_402_body(config, scan_body, zero, energy_element_tag, repititions, save):
    epu = ENERGY_SCAN_TEMPLATE["XLD-4.0.2"]["body"]["epu"]
    for n in range(repititions):
        scan_body.extend([
            epu[0], energy_element_tag, epu[1], energy_element_tag, save,
            epu[1], energy_element_tag, epu[0], energy_element_tag, save
        ])
    return "".join(scan_body)

def build_XAS_631_body(config, scan_body, zero, energy_element_tag, repititions, neg_one, save):
    angle = f"{config["incident_angles"]}\t"
    mag_field = [f"{config["magnetic_field"]}\t", f"-{config["magnetic_field"]}\t"]
    for n in range(repititions):
        scan_body.extend([
            angle, zero, zero, mag_field[0], neg_one, energy_element_tag,
            angle, zero, zero, mag_field[1], neg_one, energy_element_tag, save,
            angle, zero, zero, mag_field[1], neg_one, energy_element_tag, 
            angle, zero, zero, mag_field[0], neg_one, energy_element_tag, save            
        ])
    return "".join(scan_body)

def build_XLD_631_body(config, scan_body, zero, energy_element_tag, repititions, save):
    angle = f"{config["incident_angles"]}\t"
    mag_field = [f"{config["magnetic_field"]}\t", f"-{config["magnetic_field"]}\t"]
    polarization = f"0\t"
    for n in range(repititions):
        scan_body.extend([
            zero, zero, zero, mag_field[0], polarization, energy_element_tag,
            angle, zero, zero, mag_field[1], polarization, energy_element_tag, save,
            angle, zero, zero, mag_field[1], polarization, energy_element_tag,
            zero, zero, zero, mag_field[0], polarization, energy_element_tag, save
        ])
    return "".join(scan_body)

def build_XMCD_631_body(config, scan_body, zero, energy_element_tag, repititions, save):
    angle = f"{config["incident_angles"]}\t"
    mag_field = [f"{config["magnetic_field"]}\t", f"-{config["magnetic_field"]}\t"]
    polarization = f"-1\t"
    for n in range(repititions):
        scan_body.extend([
            angle, zero, zero, mag_field[0], polarization,
            angle, zero, zero, mag_field[1], polarization, save,
            angle, zero, zero, mag_field[1], polarization,
            angle, zero, zero, mag_field[0], polarization, save
        ])


SCAN_BODY_BULIDERS = {
    "XAS-4.0.2": build_XAS_402_body,
    "XLD-4.0.2": build_XLD_402_body,
    "XAS-6.3.1": build_XAS_631_body,
    "XLD-6.3.1": build_XLD_631_body,
    "XMCD-6.3.1": build_XMCD_631_body,

}
# Prompt to direct users on how to use program
def display_prompt():
    print("\nWelcome to the LabView Scan File Generator\n")

# Collects user credentials to login
def get_user_credentials():
    proposal_id = input("Enter your proposal-ID: ")
    beamline = input("Enter the beamline you are at: ")
    username = input("Enter your Scicat username: ")
    password = input("Enter your Scicat password: ")
    user = {
        "proposal_id": proposal_id,
        "beamline": beamline,
        "username": username,
        "password": password,
        }
    return user
# Retrieve bar / sample configurations from Scicat Server
def get_bars_from_scicat_server(proposal_id_input=None, username_input=None, password_input=None): 
    if not proposal_id_input or not username_input or not password_input:
        print("Error: Missing required credentials.")
        return None
    
    try:
        # Create a client instance
        # client = ScicatClient(
        #     base_url="http://localhost/api/v3", 
        #     username="admin", 
        #     password="2jf70TPNZsS", 
        #     auto_login=False
        #     )
        client = ScicatClient(
            base_url="http://localhost/api/v3", 
            username=username_input, 
            password=password_input, 
            auto_login=False
            )
        print(f"\nAttempting to login as {client._username}...")

        # Temporarily redirect stderr to suppress library output
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        client._headers["Host"] = "backend.localhost"
        client.login()

        # Restor stderr
        sys.stderr.close()
        sys.stderr = old_stderr
        print("\nLogin successful.")
    except Exception:
        # print(f"Login failed due to incorrect credentials.")
        return None
    
    # When we deploy we should use this line of code so that users have to input a valid input
    # proposal_id = proposal_id_input
    proposal_id = "admin"
    # filter_group = {"where":{"ownerGroup": proposal_id, "sampleCharacteristics:als_sample_tracking:group_id":"402"}}
    filter_group = {"ownerGroup": proposal_id}
    try:
        scicat_results = client.samples_get_many(filter_fields=filter_group)
        print("Downloading data...\n")
        # print(json.dumps(scicat_results, indent=2))
        return(scicat_results)
    except Exception:
        print(f"Failed to retrieve data:")
        return None

# Create Dictionary of {"bar_id": {"bar_parameters": data, "samples": samples}}
def filter_scicat_bars(user_credentials, scicat_results):
    # dictionary for filters dictionary {key : data}, key = bar ID, data = bar parameters and nested sample list
    barsById = {}
    for result in scicat_results:
        # Filter for valid sets
        if (result.get("_id", {}) != ""
            and result.get("ownerGroup", {}) == user_credentials["proposal_id"]
            and result.get("sampleCharacteristics", {}).get("als_sample_tracking", {}).get("valid", {}) is True
            and result.get("sampleCharacteristics", {}).get("als_sample_tracking", {}).get("type", {}) == "set"):
            scicat_bar = {
                "bar_id": result["_id"],
                "bar_name": result["description"],
                "proposal_id": result["ownerGroup"],
                "sample_configs": []
            }
            barsById[scicat_bar["bar_id"]] = scicat_bar
        # Filter for valid samples
        elif (result.get("_id", {}) != ""
              and result.get("ownerGroup", {}) == user_credentials["proposal_id"]
              and result.get("sampleCharacteristics", {}).get("als_sample_tracking", {}).get("valid", {}) is True
              and result.get("sampleCharacteristics", {}).get("als_sample_tracking", {}).get("type", {}) == "configuration"):
            shortcut = result["sampleCharacteristics"]["als_sample_tracking"]
            sample_params = shortcut["parameters"]
            scicat_sample = {
                "sample_id": result["_id"],
                "sample_name": result["description"],
                "set_id": shortcut["set_id"],
                "scan_type": shortcut["scan_type"],
                "scan_parameters": sample_params,
            }
            # Add samples to barsById sample list key
            barsById[shortcut["set_id"]]["sample_configs"].append(scicat_sample)
    return barsById

def build_scan_file(filtered_bars):
    scan_files = {}

    for bar_id, bar_data in filtered_bars.items():
        count = 0
        proposal_id = bar_data["proposal_id"]
        bar_name = bar_data["bar_name"]
        bar_id = bar_data["bar_id"]

        scan_files[bar_id] = {
            "proposal": proposal_id,
            "bar_name": bar_name,
            "bar_id": bar_id,
            "scan_files": []
        }
        for config in bar_data["sample_configs"]:
            scan_type = config["scan_type"]
            if (scan_type in ENERGY_SCAN_TEMPLATE
                and scan_type in SCAN_BODY_BULIDERS):
                sample_name = config["sample_name"]
                sample_id = config["sample_id"]
                scan_file_info = f"# Sample Info: sample name: {sample_name} | bar name: {bar_name} | scan type: {scan_type}\n\n"
                header = f"{ENERGY_SCAN_TEMPLATE[scan_type]["header"]}\n"
                subheader = f"{ENERGY_SCAN_TEMPLATE[scan_type]["subheader"]}\n"
                zero = ENERGY_SCAN_TEMPLATE["constants"]["zero_input"]
                element_energy_tag = f"{ELEMENT_ENERGY_RANGE[config["scan_parameters"]["element_template"]]}\n"
                repititions = int(int(config["scan_parameters"]["repititions"]) / 2)
                save = ENERGY_SCAN_TEMPLATE["constants"]["save"]
                scan_body = []
                scan_body.append(f"{scan_file_info}{header}{subheader}")
                build_file = SCAN_BODY_BULIDERS[scan_type](config, scan_body, zero, element_energy_tag, repititions, save)
 
                scan_files[bar_id]["scan_files"].append({
                    "sample_id": sample_id,
                    "sample_name": sample_name,
                    "scan_type": scan_type,
                    "bar_id": bar_id,
                    "bar_name": bar_name,
                    "build_file": build_file,
                })
    return scan_files

def save_files(scan_files, proposal_id):
    main_dir = f"{proposal_id}"
    os.makedirs(main_dir, exist_ok=True)
    print(f"Main dir:\n\t{main_dir}")
    for bar_id, bar_data in scan_files.items():
        bar_name = bar_data["bar_name"]
        bar_dir = os.path.join(main_dir, bar_name)
        os.makedirs(bar_dir, exist_ok=True)
        print(f"Bar folder:\n\t{bar_dir}")
        for sample in bar_data["scan_files"]:
            safe_sample_name = "".join(c for c in sample["sample_name"] if c.isalnum() or c in (" ", "_")).rstrip()
            sample_file = os.path.join(bar_dir, f"{safe_sample_name}.txt")
            print(f"Sample file locations:\n\t{sample_file}")
            with open(sample_file, 'w') as f:
                f.write("".join(sample["build_file"]))

def run_file_generator():
    user_credentials = get_user_credentials()
    # user_credentials = {
    #     "proposal_id": "admin",
    #     "beamline": "",
    #     "username": "admin",
    #     "password": "2jf70TPNZsS",
    #     }
    scicat_results = get_bars_from_scicat_server(proposal_id_input=user_credentials["proposal_id"], username_input=user_credentials["username"], password_input=user_credentials["password"])
    if scicat_results is None:
        print("Failed to retrieve data from Scicat. Please try again.\n")
        return
    filtered_bars = filter_scicat_bars(user_credentials, scicat_results)
    scan_files = build_scan_file(filtered_bars)
    save_files(scan_files, user_credentials["proposal_id"])

def main():
    display_prompt()
    repeat = "y"
    run_file_generator()
    while repeat[0] != 'n':
        repeat = input("Would you like to generate any more scan files? (Y/N): ").lower() # quits the loop
        print("\n")
        if repeat[0] == 'y':
            run_file_generator()
        elif repeat[0] == 'n':
            print("Quitting program...")
            exit
        else:
            print("You made an invalid choice:")
    

if __name__ == "__main__":
    main()