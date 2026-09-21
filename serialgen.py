#!/usr/bin/env python3

import os
import json
import psycopg2
import argparse
import random
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer



def start_host():

    HOST = os.environ.get("SN_GENERATOR_HOST", "127.0.0.1")
    PORT = int(os.environ.get("SN_GENERATOR_PORT", "9001"))

    DB_HOST = os.environ["SN_DB_HOST"]
    DB_PORT = os.environ.get("SN_DB_PORT", "5432")
    DB_NAME = os.environ["SN_DB_NAME"]
    DB_USER = os.environ["SN_DB_USER"]
    DB_PASSWORD = os.environ["SN_DB_PASSWORD"]


def generate_sn(parameters):
    """
    Perform the privileged SN generation operation.
    """

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

    try:
        with conn:
            with conn.cursor() as cur:

                # Replace this with your actual SQL.
                cur.execute(
                    """
                    INSERT INTO serial_number_generation
                        (source)
                    VALUES
                        (%s)
                    RETURNING serial_number;
                    """,
                    (parameters["source"],)
                )

                serial_number = cur.fetchone()[0]

        return {
            "success": True,
            "serial_number": serial_number
        }

    finally:
        conn.close()


class Handler(BaseHTTPRequestHandler):

    def do_POST(self):

        if self.path != "/generate":
            self.send_error(404)
            return

        content_length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(content_length)

        try:
            parameters = json.loads(body)

            if "source" not in parameters:
                raise ValueError("Missing source")

            result = generate_sn(parameters)

            response = json.dumps(result).encode()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.send_header(
                "Content-Length",
                str(len(response))
            )
            self.end_headers()

            self.wfile.write(response)

        except Exception as e:

            response = json.dumps({
                "success": False,
                "error": str(e)
            }).encode()

            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.send_header(
                "Content-Length",
                str(len(response))
            )
            self.end_headers()

            self.wfile.write(response)

def SN_gen(PN, ver):
    FM = "414"
    prod = PN[1:-1]

    month = datetime.now().month
    now = datetime.now()
    year = str(now.year)
    quarter = ((month - 1) // 3) + 1

    quarter_code = {
        1: "A",
        2: "B",
        3: "C",
        4: "D"
    }[quarter]


    if prod == FM:
        with open("products.json", "r") as f:
            data = json.load(f)
            used_numbers = data.get(year, {}).get(quarter_code, [])
        while True:
            number = random.randint(0, 999)

            if number not in used_numbers:
                add_number(data, year, quarter_code, number)
                break
        # number is now a valid UUID
        generated = make_serial(PN, ver, quarter_code, number)

    return generated

def add_number(data, year, quarter_code, number):
    data.setdefault(year, {})
    data[year].setdefault(quarter_code, [])
    data[year][quarter_code].append(number)

def make_serial(PN, ver, quarter_code, number):
    serial_number = f"FM-{str(PN).zfill(5)}-{str(number).zfill(4)}-{str(ver).zfill(2)}{quarter_code}" #Per the stardards Sept 21st
    return serial_number 

if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--u", 
                        action="store_true",
                        help="Run in unit-test mode without starting the service"
                        )


    parser.add_argument(
                        "--pn",
                        type=str,
                        help="Part number"
                        )

    parser.add_argument(
                        "--version",
                        type=str,
                        help="Part version"
                        )

    args = parser.parse_args()

    pn = args.pn
    version = args.version

    if args.u:
        if pn is None:
            pn = input("Enter PN: ").strip()

        if version is None:
            version = input("Enter version: ").strip()

        serial_number = SN_gen(pn, version)
        print(f"Generated Serial Number: {serial_number}")

    else: 
        start_host()

        server = HTTPServer(
            (HOST, PORT),
            Handler
        )

        print(
            f"SN generator listening on "
            f"http://{HOST}:{PORT}"
        )

        server.serve_forever()