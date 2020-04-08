import dateparser

from tess.data.vulnerability import Vulnerability


class Utils:

    @staticmethod
    def get_available_feature_schema(data):
        capec_entries = []
        keywords_entries = []
        for el in data:
            capec_entries.extend([item[0].lower() for item in el.details.capec])
            keywords_entries.extend([item.lower() for item in el.details.keywords])
        return list(set(keywords_entries)) + list(set(capec_entries)) + ['__cvss_expl', '__ref_number', '__days_diff']

    @staticmethod
    def get_element_feature(schema, vulnerability, time):
        features = [0] * len(schema)
        for feature in (vulnerability.keywords + [item[0] for item in vulnerability.capec]):
            try:
                index = schema.index(feature.lower())
                features[index] = 1
            except ValueError:
                pass
        features[schema.index('__days_diff')] = (time - vulnerability.published_date.replace(tzinfo=None)).days
        features[schema.index('__ref_number')] = vulnerability.references_number
        features[schema.index('__cvss_expl')] = vulnerability.e_score
        return features

    @staticmethod
    def get_target_function_value(data, vuln_event):
        valid_events = []
        for item in data:
            if vuln_event.id != item.id:
                continue
            diff = (vuln_event.date - item.date).days
            if 0 <= diff <= 31 and item != vuln_event:
                valid_events.append(item)
        pos = len([item.outcome for item in valid_events if item.outcome == True])
        if len(valid_events) == 0:
            return vuln_event.details.e_score
        return vuln_event.details.e_score * (pos / (len(valid_events)))

    @staticmethod
    def get_filtered_schema(schema, filter):
        ret = []
        for i in range(len(schema)):
            if filter[i]:
                ret.append(schema[i])
        return ret

    @staticmethod
    def get_vulnerability(cve_id, cve_search, key_parser):
        info = cve_search.find_cve_by_id(cve_id)
        keywords = key_parser.parse(info['cve']['description']['description_data'][0]['value'])
        capec = [(item['id'], item['name']) for item in info['capec']]
        exploitability_score = info['impact']['baseMetricV3']['exploitabilityScore']
        cvss_vector = info['impact']['baseMetricV3']['cvssV3']['vectorString']
        vuln_details = Vulnerability(keywords, capec, exploitability_score, cvss_vector,
                                     len(info['cve']['references']['reference_data']),
                                     dateparser.parse(info['publishedDate']))
        return vuln_details


"""
    @staticmethod
    def batch(iterable, size):
        it = iter(iterable)
        while item := list(itertools.islice(it, size)):
            yield item
"""