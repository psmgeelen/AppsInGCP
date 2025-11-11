"""
Apache Beam pipeline that reads from Pub/Sub Eventarc events,
groups and counts items by a key field.
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import json
import argparse
import logging


class ParsePubSubMessage(beam.DoFn):
    """Parse Pub/Sub message and extract relevant fields."""

    def process(self, element):
        try:
            # Decode the Pub/Sub message
            message_data = element.decode('utf-8')
            event = json.loads(message_data)

            # Extract fields from the event
            # Adjust these fields based on your Eventarc event structure
            event_type = event.get('type', 'unknown')
            source = event.get('source', 'unknown')

            # Return tuple (key, 1) for counting
            yield (event_type, 1)

        except Exception as e:
            logging.error(f"Error parsing message: {e}")


class FormatOutput(beam.DoFn):
    """Format the aggregated results."""

    def process(self, element):
        key, count = element
        result = {
            'event_type': key,
            'count': count
        }
        yield json.dumps(result)


def run_pipeline(argv=None):
    """Main pipeline execution."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_subscription',
        required=True,
        help='Pub/Sub subscription to read from (e.g., projects/PROJECT_ID/subscriptions/SUBSCRIPTION_NAME)'
    )
    parser.add_argument(
        '--output_topic',
        required=False,
        help='Pub/Sub topic to write results to (optional)'
    )
    parser.add_argument(
        '--window_size',
        type=int,
        default=60,
        help='Window size in seconds for aggregation (default: 60)'
    )

    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=pipeline_options) as pipeline:
        # Read from Pub/Sub subscription
        events = (
                pipeline
                | 'Read from Pub/Sub' >> beam.io.ReadFromPubSub(
            subscription=known_args.input_subscription
        )
        )

        # Parse messages
        parsed_events = (
                events
                | 'Parse Messages' >> beam.ParDo(ParsePubSubMessage())
        )

        # Apply windowing for aggregation
        windowed_events = (
                parsed_events
                | 'Apply Window' >> beam.WindowInto(
            beam.window.FixedWindows(known_args.window_size)
        )
        )

        # Group by key and count
        aggregated = (
                windowed_events
                | 'Group and Count' >> beam.CombinePerKey(sum)
        )

        # Format output
        formatted_output = (
                aggregated
                | 'Format Output' >> beam.ParDo(FormatOutput())
        )

        # Write to Pub/Sub topic (if specified) or print to console
        if known_args.output_topic:
            formatted_output | 'Write to Pub/Sub' >> beam.io.WriteToPubSub(
                topic=known_args.output_topic
            )
        else:
            formatted_output | 'Print Results' >> beam.Map(print)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run_pipeline()