from nifiapi.flowfiletransform import (
    FlowFileTransform,
    FlowFileTransformResult
)
from nifiapi.properties import ProcessContext
import json

FIELD_MAP = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source"
]

RETURN_SCHEMA = [
    "icao24", "callsign", "origin_country",
    "reporting_time", "time_position", "last_contact",
    "longitude", "latitude", "on_ground"
]


class TransformOpenskyStates(FlowFileTransform):

    class Java:
        implements = ['org.apache.nifi.python.processor.FlowFileTransform']

    class ProcessorDetails:
        version = '0.0.1-SNAPSHOT'
        description = '''
        Transform the data returned by the OpenSky Network API.
        '''
        tags = ["opensky", "transform", "tutorial"]
        dependencies = []

    def __init__(self, **kwargs):
        super().__init__()

    def transform(
            self, context: ProcessContext, flow_file
    ) -> FlowFileTransformResult:
        '''
        Parameters:
            context (ProcessContext)
            flow_file

        Returns:
            FlowFileTransformResult
        '''
        contents = json.loads(flow_file.getContentsAsBytes())

        def sanitize_value(value):
            if isinstance(value, str):
                return value.strip()

            return value

        states = []
        for record in contents["states"]:
            record = dict(zip(FIELD_MAP, record))
            record["reporting_time"] = contents["time"]

            # Choose only fields listed in the RETURN_SCHEMA
            sanitized = {}
            for key, value in record.items():
                if key not in RETURN_SCHEMA:
                    continue

                sanitized[key] = sanitize_value(value)

            states.append(sanitized)

        return FlowFileTransformResult(
            "success",
            contents=json.dumps(states)
        )