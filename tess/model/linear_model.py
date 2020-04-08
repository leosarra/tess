from joblib import dump, load
from sklearn.linear_model import LinearRegression

from tess.utils import Utils


class TessLinearModel:

    def __init__(self, data=None, schema=None):
        self.data = data
        self.schema = schema
        self.model = LinearRegression()

    def learn_by_data(self):
        if self.data is None or self.schema is None:
            raise ValueError("You can't fit the model without having a data and schema")
        schema = Utils.get_available_feature_schema(self.data)
        X = [Utils.get_element_feature(schema, event.details, event.date) for event in self.data]
        Y = [Utils.get_target_function_value(self.data, event) for event in self.data]
        self.model.fit(X, Y)

    def learn(self, X, Y):
        self.model.fit(X, Y)

    def predict(self, elem):
        return self.model.predict(elem)

    def get_exploitability(self, vulnerability, time):
        return vulnerability.e_score * self.model.predict([Utils.get_element_feature(self.schema, vulnerability, time)])

    def save(self, filename_model, filename_schema):
        dump(self.model, filename_model)
        dump(self.schema, filename_schema)

    def load(self, filename_model, filename_schema):
        self.model = load(filename_model)
        self.schema = load(filename_schema)
        return self.model, self.schema

    def get_coeff(self):
        return self.model.coef_