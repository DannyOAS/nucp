# Creating a management command for documentation
# mysite/api/management/commands/generate_api_docs.py
from django.core.management.base import BaseCommand
from api.documentation import generate_api_docs
import os

class Command(BaseCommand):
    help = 'Generate API documentation'
    
    def add_arguments(self, parser):
        parser.add_argument('--app', type=str, help='App name to document')
        parser.add_argument('--output', type=str, help='Output file path')
    
    def handle(self, *args, **options):
        app_name = options.get('app')
        output_file = options.get('output')
        
        if not app_name:
            self.stdout.write(self.style.ERROR('Please provide an app name.'))
            return
        
        docs = generate_api_docs(app_name)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(docs)
            self.stdout.write(self.style.SUCCESS(f'Documentation written to {output_file}'))
        else:
            self.stdout.write(docs)
