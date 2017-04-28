# Plugins

* Define folder for plugins by setting environment variable: `SAM__PLUGINS__ROOT`.
* Each plugin is a folder in the root plugin folder.
* Plugin names must not be equivalent to existing urls. (such as "map" or "links")
* Each plugin must have a file `<plugin>/__init__.py` that contains at least the line `import sam_installer`.
* Each plugin must have a file `<plugin>/sam_installer.py` that contains the function definition `def install()`.
* The install function must do everything needed to integrate your plugin with the core of SAM.

## Installing a plugin

* Plugins are installed based on the environment variable `SAM__PLUGINS__ENABLED` which defaults to `ALL`.
  * Use a comma-separated list to be explicit about which plugins to install. e.g. `plug1, plug2`. Plugin names mustn't start nor end with whitespace. 
  * `ALL` (the default) is a special keyword meaning to scan the plugin folder for subfolders and attempt to install each as a plugin.
  * If blank, no plugins are installed.

## Importers

* If your plugin adds an importer for a new format, include the following in your install script:
    * `sam.constants.plugin_importers.append('<plugin>')`
    * where `<plugin>` is the name of your plugin
* All importers must be in a subfolder called `importers` that is an importable python module. (has an `__init__.py`)
* All importers must have a global `class_` variable whose value is your importer class
* All importers should inherit from `sam.importers.import_base.BaseImporter`, often only needing to override the translate function

## Static files
* If your plugin defines static files, include the following in your install script:
    * `sam.constants.plugin_static.append('<plugin>')`
    * where `<plugin>` is the name of your plugin.
* Static files must be placed in a subfolder named `static` and link to them via `/<plugin>/static/...`. 
    * For example: `<script src="/my_plugin/static/js/composite.js">`.
* Static files can not overload existing static files. To replace existing content, change the path linking to it. 

## Template files
* If your plugin provides template files, include the following in your install script:
    * `sam.constants.plugin_templates.append(os.path.join('<plugin>', '<local-path-to-templates'))`
    * where `<plugin>` is the name of your plugin.
    * and the local path is generally just the string `templates`.
* Templates should be placed in a subfolder named `templates`. Render them from pages as normal.
    * For example: `/my_plugin/templates/composite-view.html`
    * And in your page: 
```python
class Composite(sam.pages.base.Headed):
    def GET(self):
        return self.render('composite')
```
* Note: templates can be used to override existing templates. Plugin folders are scanned for templates first in the order they are loaded.

## Endpoints
* If your plugin provides new endpoints, include the following in your install script for each endpoint:
    * `sam.constants.urls.extend([ '<url-pattern>', '<handler-class>' ])`
    * where `<url-pattern>` is the url pattern with any capturing groups needed. [Webpy url pattern-matching description](http://webpy.org/cookbook/url_handling)
    * and where `<handler-class>` is the plugin path to your class with appropriate HTTP methods.
    * for example: `constants.urls.extend([ '/composite', 'my_plugin.pages.composite.Composite'])`
* Each endpoint should inherit from one of `sam.pages.base.Headed`, `sam.pages.base.Headless`, `sam.pages.base.HeadlessPost`
    * Stylistically, each endpoint should be it's own class within a subfolder called pages
    * And an endpoint should server HTML or JSON but not both. 

#### Navbar
* To add a page to the navbar, include the following in your install script.
```python
sam.constants.navbar.append({
    "name": "Composite View",
    "icon": "pie chart",
    "link": "/composite",
    "group": "any"
})
```
* where `name` is the name shown on the nav bar
* and `icon` is the icon accompanying (selected from [this list](https://semantic-ui.com/elements/icon.html))
* and `link` is the url to your page.
* Note: `group` is reserved for future use.

## Overriding other features
* Overriding other features in SAM is done so at your own risk. 
* Simply import the relevant class and reassign it your replacement.
* For example, a complete plugin that disables all POST requests:
```python
# sam_installer.py
import json
import web
from sam.pages import base

class DisabledPost(base.HeadlessPost):
    def POST(self):
        web.header("Content-Type", "application/json")
        fail_case = {'result': 'failure', 'message': 'Post operations disabled.'}
        return json.dumps(fail_case, default=base.decimal_default)

def install():
    base.headless_post = DisabledPost
```
