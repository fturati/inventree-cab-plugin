# inventree-cab-plugin

A label printing plugin for [InvenTree](https://inventree.org/), which provides support for the [Cab label printers](https://www.cab.de/en/marking/label-printer/).

This plugin supports printing to cab printers using FTP. It was only tested on the MACH 4S model but should work on other models with similar capabilities.

## Installation

Add the following line to `plugins.txt` for automatic installation using the `invoke install` command:

```text
install inventree-cab-plugin
```

Or install manually with:

```shell
pip install inventree-cab-plugin
```

For further development can also setup an editable install (see InvenTree [documentation](https://docs.inventree.org/en/latest/extend/how_to_plugin/#local-plugin-development)).

An example using the InvenTree docker (see InvenTree [documentation](https://docs.inventree.org/en/latest/start/docker_dev/#docker-development-server)):

```shell
# Setup InvenTree development docker
git clone https://github.com/inventree/InvenTree.git && cd InvenTree
docker compose run inventree-dev-server invoke update
docker compose run inventree-dev-server invoke setup-test --dev
docker compose up -d

# Install plugin inside docker container
docker ps 
# Note the `NAME` or `CONTAINER ID` unique prefix for inventree-dev-server container
docker exec -it inventree-inventree-dev-server-1 /bin/sh
# In shell inside docker
source data/env/bin/activate
source /home/inventree/data/env/bin/activate
# Copy plugin code to data/plugins/ folder on host (same folder is already mounted inside docker)
cd ./data/plugins/inventree-cab-plugin
pip install --editable .
```

## Configuration Options

In InvenTree web GUI (in development environment accessible on http://localhost:8000), go to the settings page and then to the plugin settings section.
If run InvenTree inside docker, should toggle the `Check plugins on startup` setting and restart (`docker compose restart`) if it was not enabled.

Afterward can enable the Cab Labels plugin and access its settings.
The IP Address of the printer should be entered for the plugin to work. The other settings should be modified according to the printer settings.

## Printing Options

When select stock items to print labels for, can select a label template.
On InvenTree administration page can upload new label template e.g., Stock Item Label (in dev environment at http://localhost:8000/admin/label/stockitemlabel/).

Here can click on `ADD STOCK ITEM LABEL`, give the label a name, select a file and configure the other desired parameters like the width and height then save.

An example jscript is shown below. Upload it to as html label file as described above. 

For other examples can refer to the Programming cab printer PDF that can be found online e.g. from cab [website](https://www.cab.de/media/pushfile.cfm?file=3963). There is also a jscript programming manual available from cab website.

The variables in `{{ }}` are from the django template language (see django [documentation](https://docs.djangoproject.com/en/5.0/topics/templates/)).

```html
; Set [m]easurements to [m]illimeters
m m

; Create a [J]ob
J

; [S]et Label Size
; S [start detection;] displacement to the right, displacement downwards, height, height + gap, width
; S l1; 0, 0, 30, 32, 60
; using {{ height }} {{ width }} params configured when uploaded template jscript
; S l1; 0, 0, {{ height }}, {{ height|add:2}}, {{ width }}

; W:[refrence;] , x position, y position, rotation, width, height, font, size; text
W:Titlebox; 1, 1, 0, {{ width }}, 6, 3, 3; <HTML>
<h2>Company</h2>
</HTML>


; Barcode
; B [name;] x, y, r, type[+options], size; content
; NOTE: IF write CODE128 will print text of barcode below, but not if write CODE128
; with code128 need to specify height, width smallest bar
B 1, 7, 0, code128, 8, 0.2; {{ qr_data }}

; W: x, y, rotation, width, height, font, size; text
W:Textbox; 1, 15, 0, {{ width }}, 12, 3, 2;<HTML>
<p>SN: {{ serial }}</p>
<p>PN: {{ part.IPN }}</p>
<p>{{ part.name }}</p>
</HTML>

; Print one label
; A 1
; Preview at https://PRINTER_IP/cgi-bin/bitmap
A [preview]
```

If use the preview command `A [preview]` toggle the preview option before printing in inventree.
