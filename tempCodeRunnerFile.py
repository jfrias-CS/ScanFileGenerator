    for n in range(repititions):
        scan_body.append(epu[0]).append(energy_element_tag)
        scan_body.append(epu[1]).append(energy_element_tag)
        scan_body.append(f"File\n")
        scan_body.append(epu[1]).append(energy_element_tag)
        scan_body.append(epu[0]).append(energy_element_tag)
        scan_body.append(f"File\n")