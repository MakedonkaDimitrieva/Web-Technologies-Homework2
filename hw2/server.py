"""An example of a simple HTTP server."""
import json
import mimetypes
import pickle
import socket
from os.path import isdir
from urllib.parse import unquote_plus

# Pickle file for storing data
PICKLE_DB = "db.pkl"

# Directory containing www data
WWW_DATA = "www-data"

# Header template for a successful HTTP request
HEADER_RESPONSE_200 = """HTTP/1.1 200 OK\r
Content-Type: %s\r
Content-Length: %d\r
connection: Close\r
\r
"""

# Represents a table row that holds user data
TABLE_ROW = """
<tr>
    <td>%d</td>
    <td>%s</td>
    <td>%s</td>
</tr>
"""

# Template for a 404 (Not found) error
RESPONSE_404 = """HTTP/1.1 404 Not found\r
content-type: text/html\r
connection: Close\r
\r
<!doctype html>
<h1>404 Page not found</h1>
<p>Page cannot be found.</p>
"""

# Template for a 405 Method not allowed
RESPONSE_405 = """HTTP/1.1 405 Method not allowed\r
Location: %s\r
Content-Type: %s\r
Content-Length: %d\r
Connection: Close\r
\r
<!doctype html>
<h1>405 Method not allowed</h1>
<p>Your browser requested a method that is not valid.</p>
"""

# Template for a 400 Bad request
RESPONSE_400 = """HTTP/1.1 400 Bad request\r
Location: %s\r
Connection: Close\r
\r
"""

# Template for a 301 Moved Permanently
RESPONSE_301 = """HTTP/1.1 301 Moved permanently\r
Location: %s\r
Connection: Close\r
\r
"""

# Template for GET app-index
RESPONSE_app_index = """HTTP/1.1 200 ok\r
Content-type: %s\r
Content-length: %d\r
html_contains: %s\r
Connection: Close\r
\r
"""

# Template for GET app-json
RESPONSE_app_json = """HTTP/1.1 200 ok
Content-type: application/json\r
Content-length: %d\r
json_contains: %s\r
Connection: Close\r
\r
"""


def save_to_db(first, last):
    """Create a new user with given first and last name and store it into
    file-based database.

    For instance, save_to_db("Mick", "Jagger"), will create a new user
    "Mick Jagger" and also assign him a unique number.

    Do not modify this method."""

    existing = read_from_db()
    existing.append({
        "number": 1 if len(existing) == 0 else existing[-1]["number"] + 1,
        "first": first,
        "last": last
    })
    with open(PICKLE_DB, "wb") as handle:
        pickle.dump(existing, handle)


def read_from_db(criteria=None):
    """Read entries from the file-based DB subject to provided criteria

    Use this method to get users from the DB. The criteria parameters should
    either be omitted (returns all users) or be a dict that represents a query
    filter. For instance:
    - read_from_db({"number": 1}) will return a list of users with number 1
    - read_from_db({"first": "bob"}) will return a list of users whose first
    name is "bob".

    Do not modify this method."""
    if criteria is None:
        criteria = {}
    else:
        # remove empty criteria values
        for key in ("number", "first", "last"):
            if key in criteria and criteria[key] == "":
                del criteria[key]

        # cast number to int
        if "number" in criteria:
            criteria["number"] = int(criteria["number"])

    try:
        with open(PICKLE_DB, "rb") as handle:
            data = pickle.load(handle)

        filtered = []
        for entry in data:
            predicate = True

            for key, val in criteria.items():
                if val != entry[key]:
                    predicate = False

            if predicate:
                filtered.append(entry)

        return filtered
    except (IOError, EOFError):
        return []


def parse_headers(client):
    headers = dict()
    while True:
        line = client.readline().decode("utf-8").strip()
        if not line:
            return headers
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()


def process_request(connection, address):
    """Process an incoming socket request.

    :param connection is a socket of the client
    :param address is a 2-tuple (address(str), port(int)) of the client
    """

    # Read and parse the request line
    # Read and parse headers
    # Read and parse the body of the request (if applicable)
    # create the response
    # Write the response back to the socket

    klient = connection.makefile("wrb")
    linija = klient.readline().decode("utf-8").strip()
    metod, uri, verzija = linija.split()

    if verzija != "HTTP/1.1":
        print("greshka verzija")
        lokacija = "http://"+uri
        print(lokacija)
        head = RESPONSE_400 % (
            lokacija
        )
        klient.write(head.encode("utf-8"))
        klient.close()

    if metod == "GET":

        uri_splitted = uri.split("/")
        print(uri_splitted)
        requested = uri_splitted[1]
        print(requested)

        if requested == "app-index":
            print("requested get app-index")
            chitaj = WWW_DATA + "/app_list.html"
            print(chitaj)
            with open(chitaj, "rb") as handle:
                telo = handle.read()
            head = RESPONSE_app_index % (
                "application/x-www-form-urlencoded",
                len(telo),
                read_from_db()
            )
            klient.write(head.encode("utf-8"))
            klient.write(telo)
            klient.close()

        elif requested == "app-json":
            print("requested get app-json")
            head = RESPONSE_app_json % (
                len(read_from_db()),
                json.dumps(read_from_db())
            )
            klient.write(head.encode("utf-8"))
            klient.close()

        elif uri is "/":
            try:
                print("not uri")
                hederi = parse_headers(klient)
                print(hederi)
                uri = '/index.html'
                chitaj = WWW_DATA + uri
                print(chitaj)
                with open(chitaj, "rb") as handle:
                    telo = handle.read()
                lokacija = "http://" + hederi["Host"] + uri
                head = RESPONSE_301 % (
                    lokacija
                )
                klient.write(head.encode("utf-8"))
                klient.write(telo)
                klient.close()
            except IOError:
                klient.write(RESPONSE_404.encode("utf-8"))
            finally:
                klient.close()

        else:
            try:
                hederi = parse_headers(klient)
                print(hederi)
                chitaj = WWW_DATA + uri
                print(chitaj)
                with open(chitaj, "rb") as handle:
                    telo = handle.read()
                mime_type, _ = mimetypes.guess_type(uri)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                head = HEADER_RESPONSE_200 % (
                    mime_type,
                    len(telo)
                )
                klient.write(head.encode("utf-8"))
                klient.write(telo)
                klient.close()
            except IOError:
                klient.write(RESPONSE_404.encode("utf-8"))
            finally:
                klient.close()
    else:
        hederi = parse_headers(klient)
        print(hederi)
        chitaj = WWW_DATA + uri
        print(chitaj)
        with open(chitaj, "rb") as handle:
            telo = handle.read()
        mime_type, _ = mimetypes.guess_type(uri)
        if mime_type is None:
            mime_type = "application/octet-stream"
        lokacija = "http://"+hederi["Host"]+uri
        print(lokacija)
        head = RESPONSE_405 % (
            lokacija,
            mime_type,
            len(telo)
        )
        klient.write(head.encode("utf-8"))
        klient.close()


def main(port):
    """Starts the server and waits for connections."""

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", port))
    server.listen(1)

    print("Listening on %d" % port)

    while True:
        connection, address = server.accept()
        print("[%s:%d] CONNECTED" % address)
        process_request(connection, address)
        connection.close()
        print("[%s:%d] DISCONNECTED" % address)


if __name__ == "__main__":
    main(8080)
