import csv
import os
from datetime import datetime, timezone

import dateparser
from RAKE import RAKE

from cve_search.api import CVESearch
from tess.data.vulnerability import VulnerabilityEvent, Vulnerability
from tess.utils import Utils


class HistoryParser:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = None
        self.exceptions = None

    def load(self):
        if self.data is not None:
            return self.data
        self.data = []
        key_parser = KeywordsParser()
        cve = CVESearch()

        with open(self.data_path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            today = datetime.now(timezone.utc)
            for row in csv_reader:
                info = cve.find_cve_by_id(row['id'])
                published = dateparser.parse(info['publishedDate'])
                if (today - published).days < 365:
                    print('Ignoring event for {}'.format(row['id']))
                    continue
                vuln_details = None
                for item in self.data:
                    if item.id == row['id']:
                        vuln_details = item.details
                if vuln_details is None:
                    vuln_details = Utils.get_vulnerability(row['id'], cve, key_parser)
                vuln_event = VulnerabilityEvent(row['id'], row['data'], row['outcome'], vuln_details)
                self.data.append(vuln_event)


class KeywordsParser:
    def __init__(self):
        self.rake = RAKE.Rake(os.path.dirname(os.path.abspath(__file__)) + '/../data/stopwords.csv')
        self.exceptions = []
        with open(os.path.dirname(os.path.abspath(__file__)) + '/../data/exceptions.csv', mode='r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                row = [el.lower() for el in row]
                self.exceptions.append(row)

    def parse(self, text):
        keywords = self.rake.run(text)
        keywords = [item[0] for item in keywords if item[1] > 1.0]
        return self._transform_keywords(keywords)

    def _transform_keywords(self, keywords):
        ret = []
        for keyword in keywords:
            low_keyword = keyword.lower()
            to_append = None
            ignore = False
            for ex in self.exceptions:
                type_ex = ex[0]
                lcheck = ex[1].lower()
                if type_ex == 'm' and low_keyword == lcheck:
                    if len(ex) == 2:
                        ignore = True
                    else:
                        to_append = ex[2].lower()
                elif type_ex == 'c' and lcheck in low_keyword:
                    if len(ex) == 2:
                        ignore = True
                    else:
                        to_append = low_keyword.replace(lcheck, ex[2].lower())

                if ignore:
                    break
                if to_append is not None:
                    to_append = to_append.strip()
                    while '  ' in to_append:
                        to_append = to_append.replace('  ', ' ')
                    ret.append(to_append)
                    break
            if to_append is None and not ignore:
                ret.append(keyword.lower())
        return ret