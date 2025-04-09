from import_export import resources
from .models import Program, Platform, Report

class ProgramResource(resources.ModelResource):
    class Meta:
        model = Program  # Define the model you're working with

    def before_import_row(self, row, **kwargs):
        # Look up the Platform object by its name
        platform_name = row.get('platform')
        if platform_name:
            try:
                # Get the Platform object by name
                platform = Platform.objects.get(name__iexact=platform_name)
                # Set the foreign key (platform) to the platform ID
                row['platform'] = platform.id  # Ensure the foreign key gets an integer ID
            except Platform.DoesNotExist:
                raise ValueError(f"Platform with name '{platform_name}' does not exist.")
        return row

class ReportResource(resources.ModelResource):
    class Meta:
        model = Report

    def before_import_row(self, row, **kwargs):
        # Look up the Program object by its name
        program_name = row.get('program')
        if program_name:
            try:
                # Get the Program object by name
                program = Program.objects.get(name__iexact=program_name)
                # Set the foreign key (program) to the program ID
                row['program'] = program.id  # Ensure the foreign key gets an integer ID
            
            except Program.DoesNotExist:
                raise ValueError(f"Program with name '{program_name}' does not exist.")
        return row