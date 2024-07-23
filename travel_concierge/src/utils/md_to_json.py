import json

from loguru import logger


def convert_md_to_json(input_md_path, output_json_path):
    # Read the content of the input Markdown file
    with open(input_md_path, "r") as file:
        content = file.readlines()

    # Initialize variables to store item information
    items = {}
    first_level_key = None
    second_level_key = None
    second_level_value = ""

    # Parse the content to extract item information
    for line_num, line in enumerate(content):

        line = line.strip()
        if line == "":
            continue

        if line.startswith("# "):
            if first_level_key:
                # handle the last second level key and value
                if second_level_key:
                    item_details[second_level_key] = second_level_value.strip()
                second_level_key = None
                items[first_level_key] = item_details

            first_level_key = line.replace("# ", "").strip()
            item_details = {}
        elif line.startswith("## "):
            if second_level_key:
                if second_level_key in item_details:
                    item_details[second_level_key] += "\n" + second_level_value.strip()
                else:
                    item_details[second_level_key] = second_level_value.strip()
            second_level_key = line.replace("## ", "").strip()
            second_level_value = ""
        elif line:  # Skip blank lines
            if second_level_key:
                second_level_value += line + " "

    # Add the last item
    if first_level_key:
        if second_level_key:
            if second_level_key in item_details:
                item_details[second_level_key] += "\n" + second_level_value.strip()
            else:
                item_details[second_level_key] = second_level_value.strip()
        items[first_level_key] = item_details

    # Convert the dictionary of items to JSON format
    json_data = json.dumps(items, indent=4)

    # Write the JSON data to the output JSON file
    with open(output_json_path, "w") as json_file:
        json_file.write(json_data)

    print(f"Conversion completed. JSON data written to '{output_json_path}'.")


if __name__ == "__main__":
    convert_md_to_json("template.md", "template.json")
