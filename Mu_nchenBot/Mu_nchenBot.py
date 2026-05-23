import time
import requests
from secrets import secrets

# CONFIG

SEARCH_TERM = 'Mu nchen'
SUBST_TERM = 'München'
EDIT_DELAY = 2

offset = 0
limit = 100

# LOGIN

session = requests.Session()

login_response = session.post("https://openlibrary.org/account/login", data=secrets)

if "Invalid username or password" in login_response.text:
    raise Exception("Login failed")

if "account/logout" not in login_response.text:
    raise Exception("Login probably failed")

print("Logged in.")

# SEARCH EDITIONS

while True:
    search_url = f"https://openlibrary.org/search.json?q=publish_place:{SEARCH_TERM}&fields=edition_key&limit={limit}&offset={offset}"

    response = session.get(search_url)
    data = response.json()

    docs = data.get("docs", [])

    if not docs:
        print("No more results.")
        break

    for doc in docs:
        edition_keys = doc.get("edition_key", [])

        for edition_key in edition_keys:
            olid = edition_key

            edition_url = f"https://openlibrary.org/books/{olid}.json"

            try:
                edition_response = session.get(edition_url)
                edition = edition_response.json()

                publish_places = edition.get("publish_places")

                if not publish_places:
                    continue

                changed = False
                new_publish_places = []

                for place in publish_places:
                    # Handle both string entries and dict entries
                    if isinstance(place, str):
                        new_place = place.replace(SEARCH_TERM, SUBST_TERM)

                        if new_place != place:
                            changed = True

                        new_publish_places.append(new_place)

                    elif isinstance(place, dict):
                        name = place.get("name", "")
                        new_name = name.replace(SEARCH_TERM, SUBST_TERM)

                        if new_name != name:
                            changed = True

                        new_place = dict(place)
                        new_place["name"] = new_name
                        new_publish_places.append(new_place)

                    else:
                        new_publish_places.append(place)

                if not changed:
                    continue

                edition["publish_places"] = new_publish_places

                edition["_comment"] = 'Fix encoding in publish_places: "' + SEARCH_TERM + '" → "' + SUBST_TERM + '"'

                save_response = session.put(edition_url, json=edition)

                if save_response.status_code in (200, 201):
                    print(f"Updated {olid}")
                else:
                    print(f"Failed {olid}: {save_response.status_code}")
                    print(save_response.text)

                time.sleep(EDIT_DELAY)

            except Exception as e:
                print(f"Error processing {olid}: {e}")

    offset += limit
