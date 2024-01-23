from flask import Flask
import json
import time
import logging
import string
import random
from flask import Flask, request, jsonify
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.resources import SERVICE_NAME, Resource


resource = Resource(attributes={
    SERVICE_NAME: "service-2 Flask"
})

tracer_provider = TracerProvider(resource=resource)
span_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://34.173.206.57:4318/v1/traces"))
tracer_provider.add_span_processor(span_processor)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("test-tracer")

metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint="http://34.173.206.57:4318/v1/metrics"), export_interval_millis=3000)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter("test-meter")

logger_provider = LoggerProvider(resource=resource)

set_logger_provider(logger_provider)
exporter = OTLPLogExporter(endpoint="http://34.173.206.57:4318/v1/logs")
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
handler = LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider)


logging.getLogger().addHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console_handler)


request_counter = meter.create_counter(
    name="http_server_requests_counts",
    description="Count of incoming HTTP requests",
    unit="1"
)

response_time_metric = meter.create_histogram(
    name="http_server_response_time",
    description="Response time of HTTP requests",
    unit="ms"
)

# Defifnig the metrics counter
# Error Counter
error_counter = meter.create_counter(
    name="lambda_errors",
    description="Count of Lambda errors",
    unit="1"
)
# Input Request Counter
input_requests = meter.create_counter(
    name="lambda_input_requests",
    description="Count of Lambda input resuests",
    unit="1"
)
# Success Events Counter
success_counter = meter.create_counter(
    name="lambda_success_events",
    description="Count of total success events",
    unit="1"
)

# Defining different error types
# kinesisErrorType = {
#     "errorType":"Kinesis"
# }
# ingestionErrorType ={
#     "errorType":"Ingestion"
# }
# Error Counters can be added whenever the error is encountered depending on the error type
# error_counter.add(1,kinesisErrorType)
# error_counter.add(1,ingestionErrorType)

# Whenever the lambda is invoked we can add input request in input_request counter. It will automatically add job name.
# input_requests.add(1,{})
 
# On completion of event successfully we can increase success event counter. It will automatically add job name.
# success_counter.add(1,{})


app = Flask(__name__)

def create_metrics(metric_name, labels, value):
    custom_metric = meter.create_counter(
        name=metric_name,
        description=f"A custom counter for {metric_name}",
        unit="1",
    )
    custom_metric.add(value, labels)

def input_req():
    data1 = json.loads('{ "status":200, "id":"xyz", "store_id":"store_123"}')
    data2 = json.loads('{ "status":500, "id":"xyz", "store_id":"store_123", "error_msg":"Internal Error"}')
    input_requests.add(1,data1)
    input_requests.add(1,data2)

@app.route('/python/test')
def getAPI():

    with tracer.start_as_current_span("span1") as span:
        # start_time = time.time()
        # time.sleep(0.1)  # Simulating some work
        # end_time = time.time()
        # response_time_metric.record(end_time - start_time, {"http_status": "200"})
        # logging.error("some error span1")
        # request_counter.add(1, {"http_status": "200"})
        # with tracer.start_as_current_span("span2") as span:
        #     logging.error("some error span2")
        res = ''.join(random.choices(string.ascii_uppercase +
                                string.digits, k=8))
        
        x = {
            "connectType": "TrackerData",
            "merchantID": "GED",
            "channel": "shopee-2",
            "reportDate": "2023-12-12",
            "event_name": "page_viewd",
            "event_id": "1234567890",
            "session_id": "1234567890",
            "event_time": "2023-12-12 11:22:00",
            "message": "Event did not validated successfully"
        }
        err1 = {
            "errorType":"Kinesis"
        }
        err2 ={
            "errorType":"Ingestion"
        }
        error_counter.add(1,err1)
        error_counter.add(1,err1)
        error_counter.add(1,err1)
        error_counter.add(1,err2)
        error_counter.add(1,err2)
        error_counter.add(1,err1)
        error_counter.add(1,err2)
        input_requests.add(1,{})
        current_span = trace.get_current_span()
        current_span.set_attributes(x)
        current_span.set_status(Status(StatusCode.OK))
        current_span.add_event("Success Event")
        logging.error("Some error from Flask Application")
        success_counter.add(1,{})
        return 'Flask app is working fine'

@app.route('/test', methods=['POST'])
def shopifypixel():
    try:
        # Assuming the payload is in JSON format
        payload = request.get_json()

        # Do something with the payload
        print("Received payload:", payload)

        # Return a response if needed
        response = {"message": "Payload received successfully"}
        return jsonify(response), 200

    except Exception as e:
        print("Error processing payload:", str(e))
        # Return an error response if something goes wrong
        response = {"error": "Failed to process payload"}
        return jsonify(response), 500

@app.route("/error")
def error_endpoint():
    with tracer.start_as_current_span("error_span") as span:
        current_span = trace.get_current_span()
        current_span.add_event("Error Event")
        try:
        # something that might fail
            raise Exception("Dummy exception")
        # Consider catching a more specific exception in your code
        except Exception as ex:
            current_span.set_status(Status(StatusCode.ERROR))
            current_span.record_exception(ex)
    

if __name__ == '__main__':
    app.run()


    
# arn:aws:lambda:eu-north-1:901920570463:layer:aws-otel-python-x86_64-ver-1-20-0:3