# GDExDocGen

A simple static website generator for your GDExtension.

This tool uses .xml files for your classes documentation.

It also support further website customization through `custom.py` file in your destination folder.

## Requirements

tools:
- Python 3
- pip

pip packages:
- Pygments 2.19.2
- bbcode 1.1.0

You can also install pip packages with:

`pip install -r requirements.txt`

## Usage

To run the generator script:

`./generator.py -project_name "My GDExtension" -src_folder ../doc_classes -dst_folder ../docs`

In the destination folder passed on `-dst_folder` argument, you will find a `dist/` folder with the website files, including `classes/` folder with the class reference, `resources/` with fonts, javascripts, styles, etc.

On the destination folder you can add a `custom.py` file with further documentation pages generation.

By default, the generator doesn't generate a `index.html`, you are required to add one in `custom.py`, for example:

```python
# ../docs/custom.py
def configure_pages(gen):
	gen.add_documentation_page({
		"name": "My GDExtension",
		"href": "$BASE_URL/",
		"location": "/",
		"filename": gen.dist_path("index.html"),
		"content": "Hello!"
	})
```

## custom.py

The generator calls some functions on `custom.py` for each stage of generation:

- `generation_setup`: Called to configure basic information about the documentation website;
- `configure_html_templates`: Called to get template files used to generate the website;
- `configure_classes`: Called to further configure class informations;
- `configure_pages`: Called to configure the pages of the documentation;
- `configure_sidebar`: Called to configure the sidebar, which is displayed on the left;
- `generation_finished`: Called to finalize the generation;

Each function is passed a `Generator` parameter, with functions to generate the HTML of the pages, see [the source file](https://github.com/ghsoares/gdex-doc-gen/blob/1e675934a9de0a0a246f6a0e68b4e705f7eaa439/generator.py#L470) to see the available functions.

