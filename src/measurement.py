import yaml
import re
import logging
from datetime import datetime, timezone

date_fmt = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger(__name__)


class InvalidMeasurement(Exception):
    pass


def convert_to_float(string):
    # Use regular expression to remove non-numeric characters
    numeric_string = re.sub(r"[^0-9.]+", "", string)
    result_float = float(numeric_string)
    return result_float


def convert_to_date(value, default_time=None):
    if default_time is None:
        default_time = datetime.now(timezone.utc)
    # Assuming value is a string representation of a datetime
    return datetime.strptime(value, date_fmt).strftime(date_fmt)


class Measurement:
    def __init__(self, name:str, value, category:str, time:datetime=None, source_id:str=None, tags:dict = None):
        self.name = name
        self.time = time or datetime.now(timezone.utc)
        self.category = category
        if value:
            self.value = value
        self.source_id = source_id or name
        self.tags = tags

    @property
    def value(self):
        try:
            return self._value
        except AttributeError:
            return None
    @property
    def fields(self):
        return dict(name=self.name, value=self.value)

    @value.setter
    def value(self, value):
        try:
            self._value = self.convert_value(value)
        except (ValueError, TypeError):
            logger.debug(f"Unable to convert '{value}' to type '{self.category}'")
            raise InvalidMeasurement

    def convert_value(self, value, category=None):
        category = category or self.category
        if category == "float":
            return convert_to_float(value)
        elif category == "datetime":
            return convert_to_date(value, default_time=self.time)
        elif category == "string":
            return str(value)
        else:
            # Handle other categories as needed
            return value

    def __repr__(self):
        return f"{self.name} ({self.category}) {self.value}"

    def __str__(self):
        return f"{self.name} ({self.category}) {self.value}"

    def create_copy(self):
        return self.__class__(
            name=self.name,
            value=self.value,
            category=self.category,
            time=self.time,
            source_id=self.source_id,
            tags=self.tags
        )


class Measurements(list):
    def __init__(self, *args, time=None, **kwargs):
        super().__init__(args)
        self.time = time or datetime.now()

    @property
    def ids(self):
        return [el.name for el in self]

    def update_values(self, values):
        self_copy = self.copy()
        for el in self:
            try:
                el.value = values[el.source_id]
            except (InvalidMeasurement, KeyError):
                self_copy.remove(el)
                logger.debug(f"removed: {el.source_id}")
        return Measurements(*self_copy)

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
        for name, params in names.items():
            try:
                source_id = params["source_id"]
            except (KeyError, TypeError):
                source_id = None
            try:
                tags = params["tags"]
            except (KeyError, TypeError):
                tags = None
            measurements.append(Measurement(name=name, value=None, category=category, source_id=source_id, tags=tags))

    return measurements


def load_data_from_csv(file_path, measurements):
    import csv

    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        populated_measurements = []

        for row in reader:
            time = row["_time"]
            time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").astimezone(timezone.utc)
            populated_measurement_set = Measurements(time=time)

            for measurement in measurements:
                populated_measurement = measurement.create_copy()
                try:
                    populated_measurement.value = row[measurement.name]
                    populated_measurement.time = time
                except (KeyError, InvalidMeasurement):
                    continue
                populated_measurement_set.append(populated_measurement)
            populated_measurements.append(populated_measurement_set)
    return populated_measurements


def main():
    # Example usage:
    file_path = "src/measurements.yaml"
    measurements = load_measurements_from_yaml(file_path)

    for measurement in measurements:
        print(
            f"Name: {measurement.name}, Value: {measurement.value}, Category: {measurement.category}, db_id: {measurement.source_id}"
        )


def main2():
    data_file_path = "measurement_data_20231201.csv"
    measurement_file_path = "measurements.yaml"

    measurements = load_measurements_from_yaml(measurement_file_path)
    measurements = load_data_from_csv(data_file_path, measurements)


if __name__ == "__main__":
    main()
