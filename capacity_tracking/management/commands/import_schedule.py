import os
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime, parse_date
from django.utils.timezone import make_aware
from datetime import datetime
from capacity_tracking.models import Vessel, Service, Port, VesselSchedule, PortOfCall
from capacity_tracking.utils.schedule_parser import parse_schedule_image, process_schedule_data

class Command(BaseCommand):
    help = 'Import vessel schedule from an image file'

    def add_arguments(self, parser):
        parser.add_argument('image_path', type=str, help='Path to the schedule image file')
        parser.add_argument('--api-key', type=str, help='Google Gemini API Key', required=False)

    def handle(self, *args, **options):
        image_path = options['image_path']
        api_key = options.get('api_key')

        if api_key:
            os.environ['GOOGLE_API_KEY'] = api_key
        
        if not os.path.exists(image_path):
            self.stdout.write(self.style.ERROR(f'File not found: {image_path}'))
            return

        self.stdout.write(f'Processing {image_path}...')
        
        try:
            schedules_data = parse_schedule_image(image_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error parsing image: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Successfully parsed {len(schedules_data)} schedules.'))

        for schedule_data in schedules_data:
            # Pass self.stdout as logger
            process_schedule_data(schedule_data, logger=self.stdout)
