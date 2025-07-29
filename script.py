import json

JSON_COOKIE_PATH = 'linkedin_cookies.json'


def convert_cookie(raw):
    samesite_map = {
        "no_restriction": "None",
        "lax": "Lax",
        "strict": "Strict",
        None: "None"
    }
    cookie = {
        "name": raw["name"],
        "value": raw["value"],
        "domain": raw["domain"],
        "path": raw.get("path", "/"),
        "secure": raw.get("secure", False),
        "httpOnly": raw.get("httpOnly", False),
        "sameSite": samesite_map.get(raw.get("sameSite"), "None"),
    }
    if "expirationDate" in raw:
        cookie["expires"] = int(float(raw["expirationDate"]))
    return cookie


# Read JSON file and convert cookies
def load_and_convert_cookies(json_file_path):
    try:
        # Open and read the JSON file
        with open(json_file_path, 'r') as file:
            raw_cookies = json.load(file)

        # Ensure raw_cookies is a list
        if not isinstance(raw_cookies, list):
            raise ValueError("JSON file must contain a list of cookies")

        # Convert each cookie using the convert_cookie function
        cookies = [convert_cookie(c) for c in raw_cookies]
        return cookies

    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file_path}'")
        return []
    except KeyError as e:
        print(f"Error: Missing required key {e} in cookie data")
        return []
