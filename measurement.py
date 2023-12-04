import yaml
import re
import logging
from datetime import datetime

date_fmt = "%Y-%m-%d %H:%M:%S"


def convert_to_float(string):
    # Use regular expression to remove non-numeric characters
    try:
        numeric_string = re.sub(r"[^0-9.]+", "", string)
        result_float = float(numeric_string)
        return result_float
    except (ValueError, TypeError):
        logging.warning(
            f"Unable to convert '{string}' to a float. Assigning default value of 0.0"
        )
        return 0.0


class Measurement:
    def __init__(self, name, value, category, time=None):
        self.name = name
        self.time = time or datetime.now()
        self.category = category
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = self.convert_value(value)

    def convert_value(self, value, category=None):
        category = category or self.category
        if category == "temperature":
            return convert_to_float(value)
        elif category == "float":
            return convert_to_float(value)
        elif category == "datetime":
            try:
                # Assuming value is a string representation of a datetime
                return datetime.strptime(value, date_fmt).strftime(date_fmt)
            except TypeError:
                return self.time.strftime(date_fmt)
        elif category == "string":
            return str(value)
        else:
            # Handle other categories as needed
            return value

    def __repr__(self):
        return f"{self.name} ({self.category}) {self.value}"

    def __str__(self):
        return f"{self.name} ({self.category}) {self.value}"


class Measurements(list):
    @property
    def ids(self):
        return [el.name for el in self]

    def update_values(self, values):
        for el in self:
            el.value = values[el.name]

    def asdict(self):
        return {el.name: el.value for el in self}

    def __repr__(self):
        str_list = [str(el) for el in self]
        return "\n".join(str_list)


def load_measurements_from_yaml(file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)

    measurements = Measurements()

    for category, names in data.items():
        for name in names:
            measurements.append(Measurement(name, None, category))

    return measurements


def main():
    # Example usage:
    file_path = "path/to/your/file.yaml"
    measurements = load_measurements_from_yaml(file_path)

    for measurement in measurements:
        print(
            f"Name: {measurement.name}, Value: {measurement.value}, Category: {measurement.category}"
        )


if __name__ == "__main__":
    main()
