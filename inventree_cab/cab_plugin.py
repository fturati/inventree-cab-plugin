"""CAB label printing plugin for InvenTree.

Supports direct printing of labels to networked label printers, using the custom library.
"""

from django.db import models
# from django.db.models import QuerySet
# from django.http import JsonResponse
# from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

# from typing import Union

# printing options
from rest_framework import serializers
# from rest_framework.request import Request

from inventree_cab.version import CAB_PLUGIN_VERSION
from inventree_cab.cab_printer import CabPrinter

# InvenTree plugin libs
from report.models import LabelTemplate
from plugin import InvenTreePlugin
# from plugin.mixins import LabelPrintingMixin, SettingsMixin
from plugin.machine import BaseMachineType
from plugin.machine.machine_types import LabelPrinterBaseDriver, LabelPrinterMachine



# from label.models import LabelOutput, LabelTemplate

# from PIL import Image
# import io

## Changed and moved inside CabLabelPrinterDriver class
# class CabLabelSerializer(serializers.Serializer):
#     """Custom serializer class for CabLabelPlugin.

#     Used to specify printing parameters at runtime
#     """
#     preview = serializers.BooleanField(
#         default=False,
#         help_text=_('Selected label template is for preview instead of printing.')
#     )

#     # copies = serializers.IntegerField(
#     #     default=1,
#     #     label=_('Copies'), 
#     #     help_text=_('Number of copies to print'),
#     # )

# Backwards compatibility imports
try:
    from plugin.mixins import MachineDriverMixin
except ImportError:

    class MachineDriverMixin:
        """Dummy mixin for backwards compatibility."""

        pass


class CabLabelPlugin(MachineDriverMixin, InvenTreePlugin): # LabelPrintingMixin, SettingsMixin
    """
    A plugin which provides support for cab printers.
    """

    AUTHOR = "Florian Turati"
    DESCRIPTION = "Label printing plugin for Cab printers"
    VERSION = CAB_PLUGIN_VERSION

    # Machine registry was added in InvenTree 0.14.0, use inventree-cab-plugin 0.1.x for older versions
    # Machine driver interface was fixed with 0.16.0 to work inside of inventree workers
    MIN_VERSION = "0.16.0"

    NAME = "Cab Labels"
    SLUG = "cab"
    TITLE = "Cab Label Printer"

    # PrintingOptionsSerializer = CabLabelSerializer

    # Set BLOCKING_PRINT to false to return immediately (background printing)
    BLOCKING_PRINT = False # Constant, not used since change based on Preview toggle.

    def get_machine_drivers(self) -> list:
        """Register machine drivers."""
        return [CabLabelPrinterDriver]
    

class CabLabelPrinterDriver(LabelPrinterBaseDriver):
    """Cab label printing driver for InvenTree."""

    SLUG = "cab"
    NAME = "Cab Label Printer Driver"
    DESCRIPTION = "Cab label printing driver for InvenTree"

    def __init__(self, *args, **kwargs):
        """Initialize the CabLabelPrinterDriver."""

        self.MACHINE_SETTINGS = {
            'MODEL': {
                'name': _('Printer Model'),
                'description': _('Select model of Cab printer'),
                # 'choices': get_model_choices,
                'default': 'MACH 4S',
                'required': True,
            },
            'IP_ADDRESS': {
                'name': _('IP Address'),
                'description': _('IP address of the cab label printer'),
                'default': '',
                # 'required': True,
            },
            'WEB_SERVICE_AUTHENTICATION': {
                'name': _('Web Service Authentication'),
                'description': _('Authentication mechanism configured to access the printer web service. E.g., to get a preview image before printing.'),
                'choices': [
                    ('digest', 'Digest'), # TODO It may be that for /bin-cgi/bitmap digest is required irrespective of settings choice on printer?
                    ('basic', 'Basic'),
                    ('none', 'None'),
                ],
                'default': 'digest',
            },
            'WEB_SERVICE_CREDENTIAL': {
                'name': _('Web Service Credential'),
                'description': _('Credential configured in the printer settings to access its web service.'),
                'protected': True,
                'default': 'admin', # Default user is admin and cannot be changed
            },
            'PRINTER_USE_TLS': {
                'name': _('Printer Uses TLS'),
                'description': _('Toggle if TLS is enabled in the printer security settings'),
                'validator': bool,
                'default': True,
            },
            'PRINTER_VERIFY_TLS': {
                'name': _('Verify Printer TLS Certificate'),
                'description': _('Toggle if verify the printer TLS certificate'),
                'validator': bool,
                'default': False,
            },
            'FTPPRINT_CREDENTIAL': {
                'name': _('Ftpprint user password'),
                'description': _('Credential configured in the printer for the ftpprint user to send print jobs.'),
                'protected': True,
                'default': 'print', # Default user is ftpprint and cannot be changed
            },
            'FTPCARD_CREDENTIAL': {
                'name': _('Ftpcard user password'),
                'description': _('Credential configured in the printer settings for the ftpcard user to access the memory of the printer.'),
                'protected': True,
                'default': 'card', # Default user is ftpcard and cannot be changed
            },
        }

        super().__init__(*args, **kwargs)
    
    class PrintingOptionsSerializer(LabelPrinterBaseDriver.PrintingOptionsSerializer):
        """Custom serializer class for CabLabelPrinterDriver.

        Used to specify printing parameters at runtime
        """
        
        ## Example
        # auto_cut = serializers.BooleanField(
        #     default=True,
        #     label=_('Auto cut'),
        #     help_text=_('Automatically cut the label after printing'),
        # )
        ## Used to specify printing parameters at runtime

        preview = serializers.BooleanField(
            default=False,
            label=_('Preview'),
            help_text=_('Selected label template is for preview instead of printing.')
        )

        ## Default in parent class
        # copies = serializers.IntegerField(
        #     default=1,
        #     label=_('Copies'),
        #     help_text=_('Number of copies to print for each label'),
        # )


    def init_machine(self, machine: BaseMachineType):
        """Machine initialize hook."""
        # static dummy setting for now, should probably be actively checked for USB printers
        # and maybe by running a simple ping test or similar for networked printers

        # TODO could define self.printer and instantiate CabPrinter here

        ## Machine not initialized and did not find how to initialize it
        # if machine.get_setting('IP_ADDRESS') == '':
        #     raise Exception('IP Address of printer must be defined in the plugin settings before printing.')

        machine.set_status(LabelPrinterMachine.MACHINE_STATUS.CONNECTED)
    
    # def _combine_image_vertically(self, preview_outputs):
    #     """Takes the PNG image preview for each labels and combines it into one bigger PNG image.

    #     Arguments:
    #         preview_outputs: The list of label preview PNG as bytes.
        
    #     Return: A byte array of the image
    #     """
        
    #     # NOTE: Omit some labels if preview is empty
    #     # TODO Better error handling if image is not received
    #     #       Currently filter if length is 0 but could check start byte \x89PNG\rn
    #     # PNG: `89 50 4E 47 0D 0A 1A 0A` b"\x89PNG\r\n\x1a\n"
    #     # print(f'{preview_outputs=}')
    #     images = [Image.open(io.BytesIO(label_preview)) for label_preview in preview_outputs if len(label_preview) != 0]
    #     widths, heights = zip(*(i.size for i in images))

    #     max_width = max(widths)
    #     total_height = sum(heights)

    #     # TODO: could use different Image Mode if label only use black and white color
    #     new_im = Image.new('RGB', (max_width, total_height))

    #     y_offset = 0
    #     for im in images:
    #         new_im.paste(im, (0, y_offset))
    #         y_offset += im.size[1]

    #     new_byte_array = io.BytesIO()

    #     new_im.save(new_byte_array, format='PNG')

    #     return new_byte_array.getvalue()

    # TODO still need to overwrite default function that calls print_label?
    ## def print_labels(self, label: LabelTemplate, items: list, request: Request, printing_options: dict, **kwargs):
    # def print_labels(
    #     self,
    #     machine: 'LabelPrinterMachine',
    #     label: LabelTemplate,
    #     items: QuerySet[models.Model],
    #     **kwargs,
    # ) -> Union[JsonResponse, None]:
    #     """Handle printing of multiple labels

    #     Print one or more labels with the provided template and items.

    #     Arguments:
    #         label: The LabelTemplate object to use for printing
    #         items: The list of database items to print (e.g. StockItem instances)
    #         request: The HTTP request object which triggered this print job

    #     Keyword arguments:
    #         printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

    #     Returns:
    #         A JSONResponse object which indicates outcome to the user

    #     The default implementation simply calls print_label() for each label, producing multiple single label output "jobs"
    #     but this can be overridden by the particular plugin.
    #     """

    #     ## Request not anymore in function parameters
    #     # try:
    #     #     user = request.user
    #     # except AttributeError:
    #     #     user = None

    #     ## Done in init_machine
    #     ## Verify printer IP Address has been entered in settings
    #     # if self.get_setting('IP_ADDRESS') == '':
    #     #     raise Exception('IP Address of printer must be defined in the plugin settings before printing.')
        
    #     printing_options = kwargs.get(printing_options)

    #     outputs = []
    #     output_file = None
         
    #     for item in items:
    #         label.object_to_print = item
    #         ## TODO replace request in parameters
    #         filename = label.generate_filename(request)
    #         # Print via jscript or PNG
    #         # Use html as proxy to use jscript template
    #         html_file = self.render_to_html(label, request, **kwargs)
    #         # Can also print PNG file
    #         pdf_file = self.render_to_pdf(label, request, **kwargs)
    #         pdf_data = pdf_file.get_document().write_pdf()
    #         png_file = self.render_to_png(label, request, pdf_data=pdf_data, **kwargs)

    #         print_args = { 
    #             'html_file': html_file,
    #             'pdf_file': pdf_file,
    #             'pdf_data': pdf_data,
    #             'png_file': png_file,
    #             'filename': filename,
    #             'label_instance': label,
    #             'item_instance': item,
    #             # 'user': user,
    #             'width': label.width,
    #             'height': label.height,
    #             'printing_options': printing_options,
    #         }

    #         # Uses  as a variable instead of constant self.BLOCKING_PRINT
    #         if printing_options.get('preview', False): 
    #             # Blocking print job
    #             output_label = self.print_label(**print_args)
    #             outputs.append(output_label)
    #         else:
    #             # Non-blocking print job
    #             # Offload the print job to a background worker
    #             # NOTE: No label preview if offload to worker. Return immediately, do not wait to get back the preview from worker.
    #             self.offload_label(**print_args) 
               
            
    #     if printing_options.get('preview', False):
    #         # Display generated preview
    #         output_file = ContentFile(self._combine_image_vertically(outputs), 'labels.png')
            
    #         output = LabelOutput.objects.create(
    #             label=output_file,
    #             user=request.user # TODO request not there anymore
    #         )

    #         return JsonResponse({
    #             'file': output.label.url,
    #             'success': True,
    #             'message': f'{len(items)} labels generated'
    #         })
        
    #     else:

    #         # Return a JSON response to the user
    #         return JsonResponse({
    #             'success': True,
    #             'message': f'{len(items)} labels printed',
    #         })


    # def print_label(self, **kwargs):
    def print_label(
            self, 
            machine: LabelPrinterMachine, 
            label: LabelTemplate, 
            item: models.Model, 
            **kwargs
        ) -> None:
        """
        Send the label to the printer

        Arguments:
            machine: The LabelPrintingMachine instance that should be used for printing
            label: The LabelTemplate object to use for printing
            item: The database item to print (e.g. StockItem instance)

        Keyword Arguments:
            html_file: Raw HTML data of the label
            pdf_file: The PDF file object of the rendered label (WeasyTemplateResponse object)
            pdf_data: Raw PDF data of the rendered label
            png_file: Raw PNG data of the rendered label
            filename: The filename of this PDF label
            label_instance: The instance of the label model which triggered the print_label() method
            item_instance: The instance of the database model against which the label is printed
            user: The user who triggered this print job
            width: The expected width of the label (in mm)
            height: The expected height of the label (in mm)
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

        Note that the supplied args/kwargs may be different if the driver overrides the print_labels() method.
                            
        Returns: 
            A preview of the label if the preview in printing_options is True.
        """

        if machine.get_setting('IP_ADDRESS') == '':
            raise Exception('IP Address of printer must be defined in the plugin settings before printing.')

        # width = kwargs['width']
        # height = kwargs['height']
        # ^ currently this width and height are those of the label template (before conversion to PDF
        # and PNG) and are of little use. 
        # They can be used in the JScript template used to make the label.

        # Printing options requires a modern-ish InvenTree backend, which supports the 'printing_options' keyword argument
        options = kwargs.get('printing_options', {})
        
        # TODO could support printing of multiple copies. Until now defined number of copies in jscript template.
        n_copies = int(options.get('copies', 1))
        preview = options.get('preview', False)

        # JScript should end with new line
        # jscript_file = kwargs['html_file'].replace('&quot;', '"') + '\n' 
        jscript_file = self.render_to_html(label, item).replace('&quot;', '"') + '\n'

        printer = CabPrinter(machine.get_setting('IP_ADDRESS', 'D'),
            web_service_auth=machine.get_setting('WEB_SERVICE_AUTHENTICATION', 'D'),
            web_credential=('admin', machine.get_setting('WEB_SERVICE_CREDENTIAL', 'D')),
            ftpcard_credential=('ftpcard', machine.get_setting('FTPCARD_CREDENTIAL', 'D')), 
            ftpprint_credential=('ftpprint', machine.get_setting('FTPPRINT_CREDENTIAL', 'D')), 
            use_tls=machine.get_setting('PRINTER_USE_TLS', 'D'), 
            verify_printer_tls_cert=machine.get_setting('PRINTER_VERIFY_TLS', 'D')
        )

        printer.print_jscript(jscript_file)

        # default offload_label has no return statement
        if preview:
            return printer.get_preview() 
