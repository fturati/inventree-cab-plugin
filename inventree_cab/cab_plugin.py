"""CAB label printing plugin for InvenTree.

Supports direct printing of labels to networked label printers, using the custom library.
"""

from django.http import JsonResponse
from django.core.files.base import ContentFile

# printing options
from rest_framework import serializers
from rest_framework.request import Request

from inventree_cab.version import CAB_PLUGIN_VERSION
from inventree_cab.cab_printer import CabPrinter

# InvenTree plugin libs
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin


from django.utils.translation import gettext_lazy as _

from label.models import LabelOutput, LabelTemplate

from PIL import Image
import io


class PrintingOptionsSerializer(serializers.Serializer):
    """Custom serializer class for CabLabelPlugin.

    Used to specify printing parameters at runtime
    """
    preview = serializers.BooleanField(
        default=False,
        help_text=_('Selected label template is for preview instead of printing.')
    )

    # copies = serializers.IntegerField(
    #     default=1,
    #     label=_('Copies'), 
    #     help_text=_('Number of copies to print'),
    # )


class CabLabelPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):
    """
    A plugin which provides support for cab printers.
    """

    AUTHOR = "Florian Turati"
    DESCRIPTION = "Label printing plugin for CAB printers"
    VERSION = CAB_PLUGIN_VERSION

    NAME = "Cab Labels"
    SLUG = "cab"
    TITLE = "Cab Label Printer"

    PrintingOptionsSerializer = PrintingOptionsSerializer

    # Set BLOCKING_PRINT to false to return immediately (background printing)
    BLOCKING_PRINT = False # Constant, not used since change based on Preview toggle.

    SETTINGS = {
        'MODEL': {
            'name': _('Printer Model'),
            'description': _('Select model of cab printer'),
            # 'choices': get_model_choices,
            'default': 'MACH 4S',
        },
        'IP_ADDRESS': {
            'name': _('IP Address'),
            'description': _('IP address of the cab label printer'),
            'default': '',
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

    
    def _combine_image_vertically(self, preview_outputs):
        """Takes the PNG image preview for each labels and combines it into one bigger PNG image.

        Arguments:
            preview_outputs: The list of label preview PNG as bytes.
        
        Return: A byte array of the image
        """
        
        # NOTE: Omit some labels if preview is empty
        # TODO Better error handling if image is not received
        #       Currently filter if length is 0 but could check start byte \x89PNG\rn
        # PNG: `89 50 4E 47 0D 0A 1A 0A` b"\x89PNG\r\n\x1a\n"
        # print(f'{preview_outputs=}')
        images = [Image.open(io.BytesIO(label_preview)) for label_preview in preview_outputs if len(label_preview) != 0]
        widths, heights = zip(*(i.size for i in images))

        max_width = max(widths)
        total_height = sum(heights)

        # TODO: could use different Image Mode if label only use black and white color
        new_im = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += im.size[1]

        new_byte_array = io.BytesIO()

        new_im.save(new_byte_array, format='PNG')

        return new_byte_array.getvalue()


    def print_labels(self, label: LabelTemplate, items: list, request: Request, printing_options: dict, **kwargs):
        """Handle printing of multiple labels

        Print one or more labels with the provided template and items.

        Arguments:
            label: The LabelTemplate object to use for printing
            items: The list of database items to print (e.g. StockItem instances)
            request: The HTTP request object which triggered this print job

        Keyword arguments:
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer

        Returns:
            A JSONResponse object which indicates outcome to the user

        The default implementation simply calls print_label() for each label, producing multiple single label output "jobs"
        but this can be overridden by the particular plugin.
        """
        try:
            user = request.user
        except AttributeError:
            user = None

        # Verify printer IP Address has been entered in settings
        if self.get_setting('IP_ADDRESS') == '':
            raise Exception('IP Address of printer must be defined before printing.')
            
        outputs = []
        output_file = None
         
        for item in items:
            label.object_to_print = item
            filename = label.generate_filename(request)
            # Print via jscript or PNG
            # Use html as proxy to use jscript template
            html_file = self.render_to_html(label, request, **kwargs)
            # Can also print PNG file
            pdf_file = self.render_to_pdf(label, request, **kwargs)
            pdf_data = pdf_file.get_document().write_pdf()
            png_file = self.render_to_png(label, request, pdf_data=pdf_data, **kwargs)

            print_args = { 
                'html_file': html_file,
                'pdf_file': pdf_file,
                'pdf_data': pdf_data,
                'png_file': png_file,
                'filename': filename,
                'label_instance': label,
                'item_instance': item,
                'user': user,
                'width': label.width,
                'height': label.height,
                'printing_options': printing_options,
            }

            # Uses  as a variable instead of constant self.BLOCKING_PRINT
            if printing_options['preview']:
                # Blocking print job
                output_label = self.print_label(**print_args)
                outputs.append(output_label)
            else:
                # Non-blocking print job
                # Offload the print job to a background worker
                # NOTE: No label preview if offload to worker. Return immediately, do not wait to get back the preview from worker.
                self.offload_label(**print_args) 
               
            
        if printing_options['preview']:
            # Display generated preview
            output_file = ContentFile(self._combine_image_vertically(outputs), 'labels.png')
            
            output = LabelOutput.objects.create(
                label=output_file,
                user=request.user
            )

            return JsonResponse({
                'file': output.label.url,
                'success': True,
                'message': f'{len(items)} labels generated'
            })
        
        else:

            # Return a JSON response to the user
            return JsonResponse({
                'success': True,
                'message': f'{len(items)} labels printed',
            })


    def print_label(self, **kwargs):
        """
        Send the label to the printer

        kwargs:
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
        
        Returns: 
            A preview of the label if the preview in printing_options is True.
        """

        # width = kwargs['width']
        # height = kwargs['height']
        # ^ currently this width and height are those of the label template (before conversion to PDF
        # and PNG) and are of little use. 
        # They can be used in the JScript template use to make the label.

        # Printing options requires a modern-ish InvenTree backend, which supports the 'printing_options' keyword argument
        options = kwargs.get('printing_options', {})
        
        # TODO could support printing of multiple copies. Until now defined number of copies in jscript template.
        # n_copies = int(options.get('copies', 1))
        preview = options.get('preview', False)

        jscript_file = kwargs['html_file'].replace('&quot;', '"') + '\n' # JScript should end with new line

        printer = CabPrinter(self.get_setting('IP_ADDRESS'), web_service_auth=self.get_setting('WEB_SERVICE_AUTHENTICATION'),
                                  web_credential=('admin', self.get_setting('WEB_SERVICE_CREDENTIAL')),
                                  ftpcard_credential=('ftpcard', self.get_setting('FTPCARD_CREDENTIAL')), 
                                  ftpprint_credential=('ftpprint', self.get_setting('FTPPRINT_CREDENTIAL')), 
                                  use_tls=self.get_setting('PRINTER_USE_TLS'), verify_printer_tls_cert=self.get_setting('PRINTER_VERIFY_TLS'))

        printer.print_jscript(jscript_file)

        # default offload_label has no return statement
        if preview:  
            return printer.get_preview() 
