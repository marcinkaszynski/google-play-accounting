#!/usr/bin/python

import csv
import pycountry
import sys

from decimal import Decimal
from pprint import pprint


DOC = """Read in a set of Google Play sales reports, generate HTML with summary.

Usage:

   ./summarize-sales-reports.py file1.csv [file2.csv ...] > summary.html
"""


EU_VAT = {"AT": 20,
          "BE": 21,
          "BG": 20,
          "CY": 19,
          "CZ": 21,
          "DE": 19,
          "DK": 25,
          "EE": 20,
          "EL": 23,
          "ES": 21,
          "FI": 24,
          "FR": 20,
          "GB": 20,
          "HR": 25,
          "HU": 27,
          "IE": 23,
          "IT": 22,
          "LT": 21,
          "LU": 17,
          "LV": 21,
          "MT": 18,
          "NL": 21,
          "PL": 23,
          "PT": 23,
          "RO": 24,
          "SE": 25,
          "SI": 22,
          "SK": 20}


def die(reason):
    sys.stderr.write(DOC)
    exit(1)


def read_data(files):
    google_fees = {'cnt': 0, 'sum': Decimal(0)}
    by_country = {}
    for f in files:
        reader = csv.DictReader(open(f))
        for row in reader:
            tt = row['Transaction Type']
            amount = Decimal(row['Amount (Merchant Currency)'])
            if tt == 'Google fee':
                google_fees['cnt'] += 1
                google_fees['sum'] += amount
            elif tt == 'Charge':
                country = row['Buyer Country']
                name = pycountry.countries.get(alpha2=country).name
                vat = EU_VAT.get(country, 0)
                by_country.setdefault(country, {'code': country,
                                                'name': name,
                                                'vat': vat,
                                                'vat_pln': Decimal(0),
                                                'cnt': 0,
                                                'sum': Decimal(0)})
                by_country[country]['cnt'] += 1
                by_country[country]['sum'] += amount
                if vat:
                    v = Decimal(0.01) * vat
                    vat_pln = v * amount / (Decimal(1) + v)
                    by_country[country]['vat_pln'] += vat_pln
            else:
                die("Unknown transaction type: '%s'\n" % tt)

    return by_country, google_fees


def generate_html(by_country, google_fees):
    total = {'cnt': 0, 'sum': Decimal(0)}
    for c in by_country.values():
        total['cnt'] += c['cnt']
        total['sum'] += c['sum']
    eu = [c for (code, c) in by_country.items() if c['vat']]
    non_eu = [c for (code, c) in by_country.items() if not c['vat']]
    h = (["<html>",
          "<style>"
          " table { border-spacing: 0; border-collapse: collapse }"
          " td { border: 1px #aaa solid; margin: 0 }"
          "</style>"
          "<body>",
          " <table>",
          " <p>Based on files:</p>",
          " <ul>",
          "".join("<li>%s</li>" % f for f in files),
          " </ul>",
          # EU
          " <tr><th colspan=3>EU</td></tr>",
          " <tr><th>entry</th><th>transaction count</th><th>PLN</th><th>VAT %</th><th>VAT PLN</th></tr>"] +
         [" <tr><td>%(name)s</td><td>%(cnt)s</td><td>%(sum)s</td><td>%(vat)s</td><td>%(vat_pln)s</td></tr>" % c
          for c in sorted(eu, key=lambda c: c['name'])] +
          # non-EU
         [" <tr><th colspan=3>non-EU</td></tr>"] +
         [" <tr><td>%(name)s</td><td>%(cnt)s</td><td>%(sum)s</td></tr>" % c
          for c in sorted(non_eu, key=lambda c: c['name'])] +
         [" <tr><td>TOTAL</td><td>%(cnt)s</td><td>%(sum)s</td></li>" % total,
          " <tr><th colspan=3></td></tr>",
          " <tr><td>Google fees</td><td>%(cnt)s</td><td>%(sum)s</td></tr>" % google_fees,
          " </table>",
          "</body>"
          "</html>"])
    return "\n".join(h)


files = sys.argv[1:]
if len(files) < 2:
    die(DOC)


by_country, google_fees = read_data(files)
print generate_html(by_country, google_fees)
