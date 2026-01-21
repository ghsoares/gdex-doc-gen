#!/usr/bin/env python

# This script generates a static HTML page from .xml GDExtension documentation files
# Usage:
# generator -project_name "Project Name" -src_folder ../doc_classes -dst_folder ../docs/

import argparse
import glob
import os
import shutil
import sys

class Generator: pass

arguments_parser = argparse.ArgumentParser("generator")
arguments_parser.add_argument("-project_name", help="The name of the project", type=str)
arguments_parser.add_argument("-src_folder", help="The source folder which contains .xml class files", type=str)
arguments_parser.add_argument("-dst_folder", help="The destiny folder which will contain the generated static site on dist/", type=str)

gen = Generator()
gen.args = arguments_parser.parse_args()

gen.project_name = gen.args.project_name

# Get absolute paths
gen.base_url = os.getenv('PROJECT_BASE_URL', '')
gen.src_folder = os.path.abspath(gen.args.src_folder)
gen.dst_folder = os.path.abspath(gen.args.dst_folder)
gen.dist_folder = os.path.join(gen.dst_folder, 'dist')
gen.gen_folder = os.path.abspath('.')

gen.godot_docs_url = "https://docs.godotengine.org/en/stable"
gen.templates = {}
gen.classes = []
gen.class_index = {}
gen.pages = []
gen.page_index = {}
gen.sidebar = []

def ensure_dir(gen, path):
	if not os.path.exists(path):
		os.makedirs(path)

def dist_path(gen, path):
	return os.path.join(gen.dist_folder, path)

def get_html_template(gen, path):
	with open(path, 'r') as f:
		template_content = f.read()

	return template_content

def add_html_template(gen, path):
	basename = os.path.basename(path)
	name, extension = os.path.splitext(basename)
	gen.templates[name] = gen.get_html_template(path)

def add_all_html_templates(gen, folder):
	html_files = glob.glob(os.path.join(folder, '*.template'))
	for p in html_files:
		gen.add_html_template(p)

def get_template(gen, template_name):
	return gen.templates[template_name]

def get_class_info_from_xml(gen, xml_path):
	import xml.etree.ElementTree as ET
	tree = ET.parse(xml_path)
	root = tree.getroot()

	name = root.attrib['name']
	inherits = root.attrib['inherits']

	brief_description = root.find('brief_description').text.strip()
	description = root.find('description').text.strip()

	methods = []
	methods_root = root.find('methods')
	for method_node in methods_root.findall('method'):
		method_name = method_node.attrib['name']
		method_return = method_node.find('return').attrib['type']
		method_description = method_node.find('description').text.strip()
		method_params = []

		for param in method_node.findall('param'):
			param_name = param.attrib['name']
			param_type = param.attrib['type']
			method_params.append({
				"name": param_name,
				"type": param_type
			})

		methods.append({
			"name": method_name,
			"return": method_return,
			"params": method_params,
			"description": method_description
		})
	
	return {
		"name": name,
		"location": f"/classes/class_{name.lower()}",
		"href": f"$BASE_URL/classes/class_{name.lower()}.html",
		"inherits": inherits,
		"brief_description": brief_description,
		"description": description,
		"methods": methods,
		"filename": gen.dist_path(f"classes/class_{name.lower()}.html")
	}

def add_class_information(gen, xml_path):
	info = gen.get_class_info_from_xml(xml_path)
	gen.classes.append(info)
	gen.class_index[info['name']] = info
	gen.classes.sort(key = lambda i: i['name'])

def add_all_class_informations(gen, folder):
	xml_files = glob.glob(os.path.join(folder, '*.xml'))
	for p in xml_files:
		gen.add_class_information(p)

def add_page(gen, page_info):
	gen.pages.append(page_info)
	gen.page_index[page_info['location']] = page_info

def add_sidebar_item(gen, item):
	gen.sidebar.append(item)

def markup_type(gen, text):
	if text == "void":
		return "<abbr title=\"No return value.\">void</abbr>"
	if text in gen.class_index:
		return f"<a href=\"$BASE_URL/classes/{text}.html\"><span>{text}</span></a>"
	
	if text.startswith("Array["):
		actual_text = text[len("Array["):text.find("]")]
		return gen.markup_type("Array") + "[" + gen.markup_type(actual_text) + "]"
 
	class_url = os.path.join(gen.godot_docs_url, f"classes/class_{text.lower()}.html")
	return f"<a href=\"{class_url}\"><span>{text}</span></a>"

def markup_text(gen, text):
	import re

	generated = text.split("\n")
	for i in range(len(generated)):
		generated[i] = "<p>" + generated[i].strip() + "</p>"
	generated = "".join(generated)

	generated = re.sub(r"\[b\]", "<b>", generated)
	generated = re.sub(r"\[/b\]", "</b>", generated)
	generated = re.sub(r"\[i\]", "<i>", generated)
	generated = re.sub(r"\[/i\]", "</i>", generated)
	generated = re.sub(r"\[u\]", "<u>", generated)
	generated = re.sub(r"\[/u\]", "</u>", generated)
	generated = re.sub(r"\[s\]", "<s>", generated)
	generated = re.sub(r"\[/s\]", "</s>", generated)
	generated = re.sub(r"\[kbd\]", "<kbd>", generated)
	generated = re.sub(r"\[/kbd\]", "</kbd>", generated)
	generated = re.sub(r"\[url\](.+?)\[/url\]", r"""<a href="\1">\1</a>""", generated)
	generated = re.sub(r"\[url=(.+?)\](.+?)\[/url\]", r"""<a href="\1">\2</a>""", generated)
	generated = re.sub(r"\[code\](.+?)\[/code\]", r"""<code class="literal notranslate">\1</code>""", generated)
	generated = re.sub(r"\[param (.+?)\]\[/param\]", r"""<code class="literal notranslate">\1</code>""", generated)

	generated = re.sub(
		r"\[class (.+?)\]", 
		lambda m: gen.markup_type(m.group(1)),
		generated
	)

	return generated

def generate_method_params(gen, params):
	generated = []
	for i in range(len(params)):
		param = params[i]
		generated.append(f"{param['name']}: {gen.markup_type(param['type'])}")
	return ", ".join(generated)

def generate_class_html(gen, class_info):
	name = class_info['name']

	generated = gen.get_template('class.html')
	generated = generated.replace("{{class_name}}", name)
	generated = generated.replace("{{brief_description}}", gen.markup_text(class_info['brief_description']))
	generated = generated.replace("{{description}}", gen.markup_text(class_info['description']))

	method_reference_items = []

	methods = class_info['methods']
	for i in range(len(methods)):
		method = methods[i]
		method_item = gen.get_template('method_ref')
		method_item = method_item.replace("{{odd_even_row}}", 'row-odd' if i % 2 == 0 else 'row-even')
		method_item = method_item.replace("{{return_type}}", gen.markup_type(method['return']))
		method_item = method_item.replace("{{method_name}}", method['name'])
		method_item = method_item.replace("{{method_params}}", gen.generate_method_params(method['params']))

		method_reference_items.append(method_item)

	generated = generated.replace("{{method_reference_items}}", "".join(method_reference_items))

	method_description_items = []
	for i in range(len(methods)):
		method = methods[i]
		method_item = gen.get_template('method_description')
		method_item = method_item.replace("{{return_type}}", gen.markup_type(method['return']))
		method_item = method_item.replace("{{method_name}}", method['name'])
		method_item = method_item.replace("{{method_params}}", gen.generate_method_params(method['params']))
		method_item = method_item.replace("{{method_description}}", gen.markup_text(method['description']))

		method_description_items.append(method_item)

	generated = generated.replace("{{method_description_items}}", "".join(method_description_items))

	return generated

def generate_sidebar_items(gen, items, depth = 1):
	generated = []

	for i in range(len(items)):
		item = items[i]
		item_generated = gen.get_template("sidebar_item")

		item_generated = item_generated.replace("{{depth}}", str(depth))
		item_generated = item_generated.replace("{{href}}", str(item['href']))
		item_generated = item_generated.replace("{{name}}", str(item['name']))

		item_class = ""

		if "items" in item:
			item_generated = item_generated.replace("{{items}}", gen.generate_sidebar_items(item["items"], depth + 1))
			item_class = "item"
		else:
			item_generated = item_generated.replace("{{items}}", "")
			item_class = "leaf"

		if depth == 1:
			item_class = "category"
		
		item_generated = item_generated.replace("{{item-classes}}", item_class)

		generated.append(item_generated)

	return "".join(generated)

def generate_sidebar(gen):
	generated = gen.get_template("sidebar")
	generated = generated.replace("{{items}}", gen.generate_sidebar_items(gen.sidebar))
	return generated

def generate_doc_header(gen, current_location):
	generated = gen.get_template('doc_header')

	items = []

	items.append("""<li><a href="$BASE_URL/index.html" class="material-symbols-outlined" aria-label="Home">home</a></li>""")

	current_location = current_location.split("/")[1:]

	for i in range(len(current_location)):
		location = current_location[:i+1]
		item = current_location[i]
		page = gen.page_index["/" + "/".join(location)]

		active_class = 'current' if i == len(current_location) - 1 else ''

		nav = f"""{page['name']}"""
		if i < len(current_location) - 1:
			nav = f"""<a href="{page['href']}">{nav}</a>"""

		items.append(f"""<li class="breadcrumb-item {active_class}">{nav}</li>""")

	generated = generated.replace("{{navigation_items}}", "".join(items))

	return generated

def copy_folder(gen, src, dst, dirs_exist_ok=True):
	gen.ensure_dir(dst)

	shutil.copytree(
		src,
		dst,
		dirs_exist_ok=dirs_exist_ok
	)

def make_page(gen, page):
	import bs4

	page['content'] = page['content'].replace("{{sidebar}}", gen.generate_sidebar())
	page['content'] = page['content'].replace("{{doc_header}}", gen.generate_doc_header(page['location']))

	page['content'] = page['content'].replace("{{project_title}}", gen.project_name)
	page['content'] = page['content'].replace("{{default_header}}", gen.get_template("default_header"))
	page['content'] = page['content'].replace("{{default_footer}}", gen.get_template("default_footer"))

	page['content'] = page['content'].replace("$BASE_URL", gen.base_url)

	soup = bs4.BeautifulSoup(page['content'], features="html.parser")
	final_content = soup.prettify()

	filename = os.path.join(gen.dist_folder, page['filename'])
	folder = os.path.dirname(filename)
	gen.ensure_dir(folder)
	with open(filename, 'w+') as f:
		f.write(final_content)

def call_custom_function(gen, function_name):
	if not gen.custom_module: return
	if hasattr(gen.custom_module, function_name):
		getattr(gen.custom_module, function_name)(gen)

gen.__class__.ensure_dir = ensure_dir
gen.__class__.dist_path = dist_path
gen.__class__.get_html_template = get_html_template
gen.__class__.add_html_template = add_html_template
gen.__class__.add_all_html_templates = add_all_html_templates
gen.__class__.get_template = get_template
gen.__class__.get_class_info_from_xml = get_class_info_from_xml
gen.__class__.add_class_information = add_class_information
gen.__class__.add_all_class_informations = add_all_class_informations
gen.__class__.add_page = add_page
gen.__class__.add_sidebar_item = add_sidebar_item
gen.__class__.markup_type = markup_type
gen.__class__.markup_text = markup_text
gen.__class__.generate_method_params = generate_method_params
gen.__class__.generate_class_html = generate_class_html
gen.__class__.generate_sidebar_items = generate_sidebar_items
gen.__class__.generate_sidebar = generate_sidebar
gen.__class__.generate_doc_header = generate_doc_header
gen.__class__.copy_folder = copy_folder
gen.__class__.make_page = make_page
gen.__class__.call_custom_function = call_custom_function

gen.custom_module = None

if os.path.exists(os.path.join(gen.dst_folder, 'custom.py')):
	sys.path.append(gen.dst_folder)
	try:
		mod = __import__('custom')
		gen.custom_module = mod
	finally:
		sys.path.remove(gen.dst_folder)

# Firstly, create static folder and remove it's content if already exists
gen.ensure_dir(gen.dist_folder)
for name in os.listdir(gen.dist_folder):
	path = os.path.join(gen.dist_folder, name)
	if os.path.isfile(path) or os.path.islink(path):
		os.unlink(path)
	elif os.path.isdir(path):
		shutil.rmtree(path)

gen.add_all_html_templates(os.path.join(gen.gen_folder, 'templates'))
gen.add_all_class_informations(gen.src_folder)

gen.call_custom_function("configure_html_templates")
gen.call_custom_function("configure_classes")

gen.add_page({
	"name": "All classes",
	"href": "./classes/index.html",
	"location": "/classes",
	"filename": gen.dist_path('classes/index.html'),
	"content": gen.get_template('all_classes.html')
})

sidebar_class_referece = {
	"href": "./classes/index.html",
	"name": "CLASS REFERENCE",
	"items": []
}
for class_info in gen.classes:
	location = class_info["location"]
	href = class_info["href"]
	gen.add_page({
		"name": class_info["name"],
		"href": href,
		"location": location,
		"filename": class_info["filename"],
		"content": gen.generate_class_html(class_info)
	})
	sidebar_class_items = [{
		"href": f"{href}#description",
		"location": href,
		"name": "Description"
	}, {
		"href": f"{href}#methods",
		"location": href,
		"name": "Methods"
	}, {
		"href": f"{href}#method-descriptions",
		"location": href,
		"name": "Method Descriptions"
	}]

	sidebar_class_referece['items'].append({
		"href": href,
		"location": location,
		"name": class_info['name'],
		"items": sidebar_class_items
	})

gen.add_sidebar_item(sidebar_class_referece)

gen.call_custom_function("configure_pages")
gen.call_custom_function("configure_sidebar")

for page in gen.pages:
	gen.make_page(page)

# Copy styles, fonts and scripts
gen.copy_folder(
	os.path.join(gen.gen_folder, 'styles'),
	os.path.join(gen.dist_folder, 'resources/styles'),
)
gen.copy_folder(
	os.path.join(gen.gen_folder, 'fonts'),
	os.path.join(gen.dist_folder, 'resources/fonts'),
)
gen.copy_folder(
	os.path.join(gen.gen_folder, 'scripts'),
	os.path.join(gen.dist_folder, 'resources/scripts'),
)

gen.call_custom_function("generation_finished")
