from pyscicat.client import ScicatClient
import json

ENERGY_SCAN_BUILDER = {
    "XAS-4.0.2": {
        "header": "Flying Beamline Energy (763, 813, 0.1, 0)",
        "subheader": "EPU\tPolarization",
        "body": "",
    },
    "XLD-4.0.2": {
        "header": "Flying Energy (763, 813, 0.1, 0)",
        "subheader": "EPU\tPolarization",
        "body": "",
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

# Prompt to direct users on how to use program
def display_prompt():
    print("Welcome to the LabView Scan Type Generator")

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
    
    # Create a client instance
    client = ScicatClient(
        base_url="http://localhost/api/v3", 
        username="admin", 
        password="2jf70TPNZsS", 
        auto_login=False
        )
    
    # client = ScicatClient(
    #     base_url="http://localhost/api/v3", 
    #     username=username_input, 
    #     password=password_input, 
    #     auto_login=False
    #     )

    # print(client._username)
    client._headers["Host"] = "backend.localhost"
    client.login()

    # When we deploy we should use this line of code so that users have to input a valid input
    # proposal_id = proposal_id_input
    proposal_id = "admin"
    # filter_group = {"where":{"ownerGroup": proposal_id, "sampleCharacteristics:als_sample_tracking:group_id":"402"}}
    filter_group = {"ownerGroup": proposal_id}
    scicat_results = client.samples_get_many(filter_fields=filter_group)
    # print(json.dumps(scicat_results, indent=2))
    return(scicat_results)

# Create Dictionary of {"bar_id": {"bar_parameters": data, "samples": samples}}
def filter_scicat_bars(user_credentials, scicat_results):
    # dictionary for filters dictionary {key : data}, key = bar ID, data = bar parameters and nested sample list
    barsById = {}
    for result in scicat_results:
        if (result.get("_id", {}) != ""
            and result.get("ownerGroup", {}) != user_credentials["proposal_id"]
            and result.get("sampleCharacteristics", {}).get("als_sample_tracking", {}).get("valid", {}) is True
            and result.get("sampleCharacteristics", {}).get("als_sample_tracking", {}).get("type", {}) == "set"):
            scicat_bar = {
                "bar_id": result["_id"],
                "bar_name": result["description"],
                "samples": []
            }
            barsById[scicat_bar["bar_id"]] = scicat_bar
        elif (result.get("_id", {}) != ""
              and result.get("ownerGroup", {}) != user_credentials["proposal_id"]
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
            barsById[shortcut["set_id"]]["samples"].append(scicat_sample)
    return barsById

def main():
    display_prompt()
    repeat = 'y'
    user_credentials = get_user_credentials()
    scicat_results = get_bars_from_scicat_server(proposal_id_input=user_credentials["proposal_id"], username_input=user_credentials["username"], password_input=user_credentials["password"])
    filtered_bars = filter_scicat_bars(user_credentials, scicat_results)
    print(json.dumps(filtered_bars, indent=2))
    
    
    
    while repeat[0] != 'n':
        repeat = input("Would you like to generate any more scan files? (Y/N): ").lower() # quits the loop
        if repeat[0] == 'y':
            user_credentials = get_user_credentials()
            scicat_results = get_bars_from_scicat_server(proposal_id_input=user_credentials["proposal_id"], username_input=user_credentials["username"], password_input=user_credentials["password"])
            filtered_bars = filter_scicat_bars(user_credentials, scicat_results)
        elif repeat[0] == 'n':
            print("Quitting program...")
            exit
        else:
            print("You made an invalid choice:")
    

if __name__ == "__main__":
    main()





    