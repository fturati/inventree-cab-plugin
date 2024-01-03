from ftplib import FTP_TLS, FTP
import requests
import io

class CabPrinter:
    """Class for CAB Printer
    """

    def __init__(self, host, web_service_auth='digest', web_credential=('admin', 'admin'), ftpcard_credential=('ftpcard', 'card'), ftpprint_credential=('ftpprint', 'print'), use_tls=True, verify_printer_tls_cert=False):
        """Create a CabPrinter object

        :param host: How to reach the printer. Could be an IP address, a DNS name etc.
        :type host: _type_
        :param use_tls: Wether to use TLS for communicating with the printer using FTP
        :type use_tls: _type_
        """
        self.host = host
        self.use_tls = use_tls
        if web_service_auth == 'digest':
            # TODO It seems even when changed settings in printer web gui, /cgi-bin/bitmap only worked with Digest Auth. 
            self.web_service_auth_req = requests.auth.HTTPDigestAuth(*web_credential)
        elif web_service_auth == 'basic':
            self.web_service_auth_req = requests.auth.HTTPBasicAuth(*web_credential)
        elif web_service_auth == 'none':
            self.web_service_auth_req = None
        else:
            raise Exception(f'Unsupported Web Service Authentication Scheme: {web_service_auth} not one of (digest, auth, none)')
        
        self.verify_cert = verify_printer_tls_cert

        self.ftpcard_creds = ftpcard_credential
        self.ftpprint_creds = ftpprint_credential

        
    def connect_ftp(self, credentials, dbg_lvl=0):
        """_summary_
        :param credentials: Iterable containing username, password, unwrapped with *credentials
        :type credentials: _type_
        :param use_tls: If open FTP_TLS or FTP
        :type use_tls: Boolean
        :param dbg_lvl: 0 for no debug, 1 for one line per command, 2 for maximum
        :type dbg_lvl: int, optional
        :return: FTP object
        :rtype: _type_
        """
        if self.use_tls:
            printer_ftp = FTP_TLS(self.host)
        else: 
            # Disabled on printer the use of cleartext session or weak ciphers 
            printer_ftp = FTP(self.host)

        printer_ftp.set_debuglevel(dbg_lvl) 

        printer_ftp.login(*credentials) 

        printer_ftp.prot_p() 

        return printer_ftp

    ## TODO Adapt to inventree plugin for printing PDF converted to PNG
    # def save_img_to_memory(self, local_img_path):
    #     """Save local image to printer with name output.png in the images folder using memory FTP user credentials

    #     :param local_img_path: _description_
    #     :type local_img_path: _type_
    #     :param mem_credentials: _description_, defaults to ('ftpcard', 'card')
    #     :type mem_credentials: tuple, optional
    #     """
        
    #     printer_ftp = self.connect_ftp(self.ftpcard_creds)
    #     printer_ftp.cwd('images')

    #     with open(f'{local_img_path}.png', 'rb') as fp:
    #         printer_ftp.storbinary('STOR output.png', fp) 

    #     dir_ls = printer_ftp.retrlines('LIST') 
    #     print('dir', dir_ls)

    #     printer_ftp.quit()


    def get_preview(self):
        """Get the preview of the label from the printer using web credentials.
        """
        preview_url = f'https://{self.host}/cgi-bin/bitmap' 

        r = requests.get(preview_url, auth=self.web_service_auth_req, verify=self.verify_cert)
        
        if r.status_code != 200:
            raise Exception(f'Unexpected status code: {r.status_code}. Could not get preview.')

        bmp_preview = r.content

        return bmp_preview


    ## TODO Adapt to inventree plugin for printing PDF converted to PNG
    # def print_png(self, path_to_jscript_preview, path_to_rendered_file):

    #     self.save_img_to_memory(path_to_rendered_file)

    #     printer_ftp = self.connect_ftp(self.ftpprint_creds)

    #     with open(f'{path_to_jscript_preview}', 'rb') as fp:
    #         printer_ftp.storbinary('STOR preview-jscript.txt', fp)

    #     printer_ftp.quit()

    #     self.get_preview(path_to_rendered_file)


    def print_jscript(self, jscript):
        """Send jscript to printer

        :param jscript: _description_
        :type jscript: _type_
        """
        printer_ftp = self.connect_ftp(self.ftpprint_creds)
        
        fp = io.BytesIO(jscript.encode('utf-8')) 
        printer_ftp.storbinary('STOR jscript.txt', fp)
        fp.close()

        printer_ftp.quit()
