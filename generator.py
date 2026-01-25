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
gen.base_url = os.getenv('PROJECT_BASE_URL', '').rstrip('/')
gen.src_folder = os.path.abspath(os.path.join(os.getcwd(), gen.args.src_folder))
gen.dst_folder = os.path.abspath(os.path.join(os.getcwd(), gen.args.dst_folder))
gen.dist_folder = os.path.join(gen.dst_folder, 'dist')
gen.gen_folder = os.path.dirname(os.path.abspath(__file__))
gen.favicon_path = None

gen.godot_docs_url = "https://docs.godotengine.org/en/stable"
gen.templates = {}
gen.classes = []
gen.class_index = {}
gen.pages = []
gen.page_index = {}
gen.sidebar = []
gen.icon_list = []
gen.copyright_info = ""
gen.build_info = """<p>Built with <a href="https://github.com/ghsoares/gdex-doc-gen">GDExDocGen</a>.</p>"""

def ensure_dir(gen, path):
	if not os.path.exists(path):
		os.makedirs(path)

def dst_path(gen, path):
	return os.path.join(gen.dst_folder, path)

def dist_path(gen, path):
	return os.path.join(gen.dist_folder, path)

def relative_path(gen, path):
	path = path.split("/")
	path = [loc for loc in path if loc]
	return "/".join(path)

def get_page_href(gen, location):
	path = gen.relative_path(location)
	if not path.endswith(".html") and not path.endswith("/"):
		path += "/"
	return f"$BASE_URL/{path}"

def set_copyright_info(gen, info):
	gen.copyright_info = info

def set_build_info(gen, info):
	gen.build_info = info

def set_favicon_path(gen, path):
	gen.favicon_path = path

def add_icon_declaration(gen, icon_name):
	if isinstance(icon_name, list):
		gen.icon_list += icon_name
	else:
		gen.icon_list.append(icon_name)
	gen.icon_list.sort()

def get_file_str(gen, path):
	with open(path, 'r') as f:
		template_content = f.read()

	return template_content

def add_html_template_from_path(gen, name, path):
	gen.templates[name] = gen.get_file_str(path)

def add_all_html_templates_from_path(gen, folder):
	html_files = glob.glob(os.path.join(folder, '*.template'))
	for p in html_files:
		basename = os.path.basename(p)
		name, extension = os.path.splitext(basename)
		gen.add_html_template_from_path(name, p)

def get_template(gen, template_name):
	return gen.templates[template_name]

def get_class_info_from_xml(gen, xml_path):
	import xml.etree.ElementTree as ET
	tree = ET.parse(xml_path)
	root = tree.getroot()

	name = root.get('name')
	inherits = root.get('inherits')

	brief_description = root.find('brief_description').text.strip()
	description = root.find('description').text.strip()

	methods = []
	methods_root = root.find('methods')
	for method_node in methods_root.findall('method'):
		method_name = method_node.get('name')
		method_return = method_node.find('return').get('type')
		method_qualifiers = method_node.get('qualifiers') or ''
		method_description = method_node.find('description').text.strip()
		method_params = []

		for param in method_node.findall('param'):
			param_name = param.get('name')
			param_type = param.get('type')
			method_params.append({
				"name": param_name,
				"type": param_type
			})

		methods.append({
			"name": method_name,
			"return": method_return,
			"params": method_params,
			"qualifiers": method_qualifiers.split(" "),
			"description": method_description
		})
	
	return {
		"name": name,
		"location": f"/classes/class_{name.lower()}.html",
		"inherits": inherits,
		"brief_description": brief_description,
		"description": description,
		"methods": methods
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

def add_documentation_page(gen, page):
	content = gen.get_template('generic.html')
	content = content.replace("{{page_content}}", page['content'])
	page = page.copy()
	page['content'] = content
	gen.add_page(page)

def add_sidebar_item(gen, item):
	gen.sidebar.append(item)

def get_class_url(gen, cname):
	if cname in gen.class_index:
		return f"$BASE_URL/classes/class_{cname.lower()}.html"
	
	return os.path.join(gen.godot_docs_url, f"classes/class_{cname.lower()}.html")

def markup_type(gen, text):
	if text == "void":
		return "<abbr title=\"No return value.\">void</abbr>"
	
	if text.startswith("Array["):
		actual_text = text[len("Array["):text.find("]")]
		return gen.markup_type("Array") + "[" + gen.markup_type(actual_text) + "]"
	
	if text.endswith("[]"):
		actual_text = text[:len(text) - 2]
		return gen.markup_type(actual_text) + "[]"
 
	class_url = gen.get_class_url(text)
	return f"<a href=\"{class_url}\">{text}</a>"

def markup_member(gen, text, type):
	splitted = text.split(".")

	# Member is in this page
	if len(splitted) == 1:
		url = f"#{type}-{splitted[0]}"
		return f"<a href=\"{url}\">{text}</a>"
	# Referencing other class
	elif len(splitted) == 2:
		class_url = gen.get_class_url(splitted[0])
		url = f"{class_url}#{type}-{splitted[1]}"
		return f"<a href=\"{url}\">{text}</a>"

	return text

def markup_bbcode(gen, text):
	import bbcode
	import codehighlight

	parser = bbcode.Parser()

	def render_class_tag(tag_name, value, options, parent, content):
		assert len(options) == 1, "'class' tag can only be called with a single value"
		val = next(iter(options.keys()))
		return gen.markup_type(val)

	def render_member_tag(tag_name, value, options, parent, content):
		assert len(options) == 1, "'member' tag can only be called with a single value"
		val = next(iter(options.keys()))
		return gen.markup_member(val, "property")

	def render_method_tag(tag_name, value, options, parent, content):
		assert len(options) == 1, "'method' tag can only be called with a single value"
		val = next(iter(options.keys()))
		return gen.markup_member(val, "method")

	def render_param_tag(tag_name, value, options, parent, content):
		assert len(options) == 1, "'param' tag can only be called with a single value"
		val = next(iter(options.keys()))
		return f"<code class=\"literal notranslate\">{val}</code>"

	def render_section_tag(tag_name, value, options, parent, content):
		assert len(options) == 1, "'section' tag can only be called with a single value"
		val = next(iter(options.values()))
		return f"<section id={val}>{value}</section>"

	def render_img_tag(tag_name, value, options, parent, content):
		if len(options) == 0:
			return f"""<img src="{value}"></img>"""
		if len(options) == 1:
			val = next(iter(options.values()))
			return f"""<img width={val} src="{value}"></img>"""
		raise Exception("not implemented")

	def render_list_tag(tag_name, value, options, parent, content):
		list_type = options["list"] if (options and "list" in options) else "*"
		css_opts = {
			"1": "decimal",
			"01": "decimal-leading-zero",
			"a": "lower-alpha",
			"A": "upper-alpha",
			"i": "lower-roman",
			"I": "upper-roman",
		}
		tag = tag_name
		css = (
			' style="list-style-type:%s;"' % css_opts[list_type]
			if list_type in css_opts
			else ""
		)
		return "<%s%s>%s</%s>" % (tag, css, value, tag)

	def render_list_item(name, value, options, parent, content):
		if not parent or not parent.tag_name in ["ul", "ol"]:
			return "[*]%s<br />" % value

		return "<li>%s</li>" % value

	def make_render_codeblock(language):
		def inner(tag_name, value, options, parent, content):
			filename = None
			if len(options) == 1:
				filename = next(iter(options.values()))

			code = codehighlight.highlight_code(value.strip(), language)
			code_markup = code['markup']
			code_language_name = code['language_name']

			filename_el = f"""<button title="Click to copy the code" class="filename">{filename}</button>""" if filename else ""

			code_markup = f"""<div class="language {language}" language-name="{code_language_name}">{filename_el}<pre><code>{code_markup}</code></pre></div>"""

			return code_markup
		return inner
			
	parser.add_simple_formatter('codeblocks', '<div class="codeblocks">%(value)s</div>', transform_newlines=False)
	parser.add_simple_formatter('kbd', '<kbd>%(value)s</kbd>')
	parser.add_simple_formatter('code', '<code class="literal notranslate">%(value)s</code>')
	parser.add_simple_formatter('br', '<br>%(value)s</br>', standalone=True)

	for i in range(0, 6):
		parser.add_simple_formatter(f"section_title{i+1}", f"<h{i+1} link-section>%(value)s</h{i+1}>")
		parser.add_simple_formatter(f"h{i+1}", f"<h{i+1}>%(value)s</h{i+1}>")

	for lang in codehighlight.get_supported_languages():
		parser.add_formatter(f"{lang}", make_render_codeblock(lang), escape_html=False)

	parser.add_formatter("section", render_section_tag)
	parser.add_formatter("img", render_img_tag)
	parser.add_formatter("ul", render_list_tag, transform_newlines=False, strip=True, swallow_trailing_newline=True)
	parser.add_formatter("ol", render_list_tag, transform_newlines=False, strip=True, swallow_trailing_newline=True)
	parser.add_formatter("*", render_list_item, newline_closes=True, transform_newlines=False, same_tag_closes=True, strip=True)
	parser.add_formatter("class", render_class_tag, standalone=True)
	parser.add_formatter("member", render_member_tag, standalone=True)
	parser.add_formatter("method", render_method_tag, standalone=True)
	parser.add_formatter("param", render_param_tag, standalone=True)

	return parser.format(text)

def markup_qualifier(gen, qualifier):
	match qualifier:
		case "const":
			return """<abbr title="This method has no side effects. It doesn't modify any of the instance's member variables.">const</abbr>"""
		case "virtual":
			return """<abbr title="This method should typically be overridden by the user to have any effect.">virtual</abbr>"""
		case "static":
			return """<abbr title="This method doesn't need an instance to be called, so it can be called directly using the class name.">static</abbr>"""
		case "vararg":
			return """<abbr title="This method accepts any number of arguments after the ones described here.">vararg</abbr>"""
		case "required":
			return """<abbr title="This method is required to be overridden when extending its base class.">required</abbr>"""
	return qualifier

def generate_method_params(gen, params):
	generated = []
	for i in range(len(params)):
		param = params[i]
		generated.append(f"{param['name']}:&nbsp;{gen.markup_type(param['type'])}")
	return ", ".join(generated)

def generate_method_qualifiers(gen, qualifiers):
	generated = []
	for i in range(len(qualifiers)):
		generated.append(gen.markup_qualifier(qualifiers[i]))
	return " ".join(generated)

def generate_class_html(gen, class_info):
	name = class_info['name']

	generated = gen.get_template('class.html')
	generated = generated.replace("{{class_name}}", name)
	generated = generated.replace("{{brief_description}}", gen.markup_bbcode(class_info['brief_description']))
	generated = generated.replace("{{description}}", gen.markup_bbcode(class_info['description']))

	method_reference_items = []

	methods = class_info['methods']
	for i in range(len(methods)):
		method = methods[i]
		method_item = gen.get_template('method_ref')
		method_item = method_item.replace("{{odd_even_row}}", 'row-odd' if i % 2 == 0 else 'row-even')
		method_item = method_item.replace("{{return_type}}", gen.markup_type(method['return']))
		method_item = method_item.replace("{{method_name}}", method['name'])
		method_item = method_item.replace("{{method_params}}", gen.generate_method_params(method['params']))
		method_item = method_item.replace("{{method_qualifiers}}", gen.generate_method_qualifiers(method['qualifiers']))

		method_reference_items.append(method_item)

	generated = generated.replace("{{method_reference_items}}", "".join(method_reference_items))

	method_description_items = []
	for i in range(len(methods)):
		method = methods[i]
		method_item = gen.get_template('method_description')
		method_item = method_item.replace("{{return_type}}", gen.markup_type(method['return']))
		method_item = method_item.replace("{{method_name}}", method['name'])
		method_item = method_item.replace("{{method_params}}", gen.generate_method_params(method['params']))
		method_item = method_item.replace("{{method_description}}", gen.markup_bbcode(method['description']))
		method_item = method_item.replace("{{method_qualifiers}}", gen.generate_method_qualifiers(method['qualifiers']))

		method_description_items.append(method_item)
		if i < len(methods) - 1:
			method_description_items.append("<hr>")

	generated = generated.replace("{{method_description_items}}", "".join(method_description_items))

	return generated

def generate_sidebar_items(gen, items, depth = 1):
	generated = []

	for i in range(len(items)):
		item = items[i]
		item_generated = gen.get_template("sidebar_item")

		item_generated = item_generated.replace("{{depth}}", str(depth))
		if 'location' in item:
			href = gen.get_page_href(item['location'])
			if 'hash' in item:
				href += f"#{item['hash']}"
			item_generated = item_generated.replace(
				"{{content}}", 
				f"""<a href="{href}">{item['name']}</a>"""
			)
		else:
			item_generated = item_generated.replace(
				"{{content}}", 
				f"""{item['name']}"""
			)

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
	generated = generated.replace("{{project_sidebar_header}}", gen.get_template('project_sidebar_header'))
	generated = generated.replace("{{items}}", gen.generate_sidebar_items(gen.sidebar))
	return generated

def generate_doc_header(gen, current_location):
	generated = gen.get_template('doc_header')

	items = []

	items.append("""<li><a href="$BASE_URL/" class="material-symbols-outlined" aria-label="Home">home</a></li>""")

	current_location = current_location.split("/")[1:]

	for i in range(len(current_location)):
		location = current_location[:i+1]
		item = current_location[i]
		page = gen.page_index["/" + "/".join(location)]

		active_class = 'current' if i == len(current_location) - 1 else ''

		nav = f"""{page['name']}"""
		if i < len(current_location) - 1:
			nav = f"""<a href="{gen.get_page_href(page['location'])}">{nav}</a>"""

		items.append(f"""<li class="breadcrumb-item {active_class}">{nav}</li>""")

	generated = generated.replace("{{navigation_items}}", "".join(items))

	return generated

def build_page_navigation(gen):
	navigation_items = []
	def add_nav(curr_item):
		if 'location' in curr_item and not curr_item['location'] in navigation_items:
			navigation_items.append(curr_item['location'])
		if 'items' in curr_item:
			for item in curr_item['items']:
				add_nav(item)
	
	navigation_items.append("/")

	for item in gen.sidebar:
		add_nav(item)
	for i in range(len(navigation_items)):
		curr_location = navigation_items[i]
		prev_location = navigation_items[i - 1] if i > 0 else None
		next_location = navigation_items[i + 1] if i < len(navigation_items) - 1 else None
		page = gen.page_index[curr_location]
		page['prev_page'] = prev_location
		page['next_page'] = next_location

def copy_file(gen, src, dst):
	dirname = os.path.dirname(dst)
	gen.ensure_dir(dirname)

	shutil.copyfile(src, dst)

def copy_folder(gen, src, dst, dirs_exist_ok=True):
	gen.ensure_dir(dst)

	shutil.copytree(
		src,
		dst,
		dirs_exist_ok=dirs_exist_ok
	)

def make_file(gen, filename, content):
	dirname = os.path.dirname(filename)
	gen.ensure_dir(dirname)
	with open(filename, 'w+') as f:
		f.write(content)

def make_page(gen, page):
	page['content'] = page['content'].replace("{{sidebar}}", gen.generate_sidebar())
	page['content'] = page['content'].replace("{{doc_header}}", gen.generate_doc_header(page['location']))

	page['content'] = page['content'].replace("{{project_title}}", gen.project_name)
	page['content'] = page['content'].replace("{{default_header}}", gen.get_template("default_header"))
	page['content'] = page['content'].replace("{{default_footer}}", gen.get_template("default_footer"))

	page['content'] = page['content'].replace("{{icon_list}}", ",".join(gen.icon_list))

	prev_btn = ""
	next_btn = ""
	if page.get('prev_page'):
		prev_btn = f"""<a class="prev" href="{gen.get_page_href(page['prev_page'])}"><span class="material-symbols-outlined">arrow_back</span>Previous</a>"""
	if page.get('next_page'):
		next_btn = f"""<a class="next" href="{gen.get_page_href(page['next_page'])}">Next<span class="material-symbols-outlined">arrow_forward</span></a>"""

	page['content'] = page['content'].replace("{{prev_page_btn}}", prev_btn)
	page['content'] = page['content'].replace("{{next_page_btn}}", next_btn)

	page['content'] = page['content'].replace("{{copyright_info}}", gen.copyright_info)
	page['content'] = page['content'].replace("{{build_info}}", gen.build_info)

	favicon = ""
	if gen.favicon_path:
		if gen.favicon_path.endswith(".svg"):
			favicon = f"""<link rel="icon" type="image/svg+xml" href="{gen.favicon_path}"/>"""
		if gen.favicon_path.endswith(".ico"):
			favicon = f"""<link rel="icon" type="image/x-icon" href="{gen.favicon_path}"/>"""
	page['content'] = page['content'].replace("{{favicon}}", favicon)

	page['content'] = page['content'].replace("$BASE_URL", gen.base_url)

	filename = gen.relative_path(page['location'])
	if not filename.endswith(".html"):
		filename = os.path.join(filename, "index.html")
	filename = gen.dist_path(filename)
	folder = os.path.dirname(filename)
	gen.ensure_dir(folder)
	with open(filename, 'w+') as f:
		f.write(page['content'])

def call_custom_function(gen, function_name):
	if not gen.custom_module: return
	if hasattr(gen.custom_module, function_name):
		getattr(gen.custom_module, function_name)(gen)

gen.__class__.ensure_dir = ensure_dir
gen.__class__.dst_path = dst_path
gen.__class__.dist_path = dist_path
gen.__class__.relative_path = relative_path
gen.__class__.get_page_href = get_page_href
gen.__class__.set_copyright_info = set_copyright_info
gen.__class__.set_build_info = set_build_info
gen.__class__.set_favicon_path = set_favicon_path
gen.__class__.add_icon_declaration = add_icon_declaration
gen.__class__.get_file_str = get_file_str
gen.__class__.add_html_template_from_path = add_html_template_from_path
gen.__class__.add_all_html_templates_from_path = add_all_html_templates_from_path
gen.__class__.get_template = get_template
gen.__class__.get_class_info_from_xml = get_class_info_from_xml
gen.__class__.add_class_information = add_class_information
gen.__class__.add_all_class_informations = add_all_class_informations
gen.__class__.add_page = add_page
gen.__class__.add_documentation_page = add_documentation_page
gen.__class__.add_sidebar_item = add_sidebar_item
gen.__class__.get_class_url = get_class_url
gen.__class__.markup_type = markup_type
gen.__class__.markup_member = markup_member
gen.__class__.markup_bbcode = markup_bbcode
gen.__class__.markup_qualifier = markup_qualifier
gen.__class__.generate_method_params = generate_method_params
gen.__class__.generate_method_qualifiers = generate_method_qualifiers
gen.__class__.generate_class_html = generate_class_html
gen.__class__.generate_sidebar_items = generate_sidebar_items
gen.__class__.generate_sidebar = generate_sidebar
gen.__class__.generate_doc_header = generate_doc_header
gen.__class__.build_page_navigation = build_page_navigation
gen.__class__.copy_folder = copy_folder
gen.__class__.copy_file = copy_file
gen.__class__.make_file = make_file
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

gen.call_custom_function("generation_setup")

gen.add_icon_declaration([
	'add',
	'home',
	'remove',
	'search',
	'link_2',
	'arrow_back',
	'arrow_forward',
])

gen.add_all_html_templates_from_path(os.path.join(gen.gen_folder, 'templates'))
gen.add_all_class_informations(gen.src_folder)

gen.call_custom_function("configure_html_templates")
gen.call_custom_function("configure_classes")

class_list_content = []
for class_info in gen.classes:
	href = gen.get_page_href(class_info['location'])
	class_list_content.append(f"""<li><a href="{href}">{class_info["name"]}</a></li>""")

gen.add_page({
	"name": "All classes",
	"location": "/classes",
	"content": gen.get_template('all_classes.html').replace("{{class_list}}", "".join(class_list_content))
})

sidebar_class_referece = {
	"name": "CLASS REFERENCE",
	"items": [{
		"location": "/classes",
		"name": "All classes"
	}]
}
for class_info in gen.classes:
	location = class_info["location"]
	gen.add_page({
		"name": class_info["name"],
		"location": location,
		"content": gen.generate_class_html(class_info)
	})
	sidebar_class_items = [{
		"location": location,
		"hash": "description",
		"name": "Description"
	}, {
		"location": location,
		"hash": "methods",
		"name": "Methods"
	}, {
		"location": location,
		"hash": "method-descriptions",
		"name": "Method Descriptions"
	}]

	sidebar_class_referece['items'].append({
		"location": location,
		"name": class_info['name'],
		"items": sidebar_class_items
	})

gen.call_custom_function("configure_pages")
gen.call_custom_function("configure_sidebar")

# Class reference is added last, always
gen.add_sidebar_item(sidebar_class_referece)

gen.build_page_navigation()

for page in gen.pages:
	gen.make_page(page)

# Make stylesheets
for style_path in glob.glob(os.path.join(gen.gen_folder, 'styles/*.css')):
	basename = os.path.basename(style_path)
	with open(style_path, 'r') as f:
		style_content = f.read()
	style_content = style_content.replace('$BASE_URL', gen.base_url)
	gen.make_file(
		os.path.join(gen.dist_folder, "resources/styles", basename),
		style_content
	)

# Copy fonts and scripts

gen.copy_folder(
	os.path.join(gen.gen_folder, 'fonts'),
	os.path.join(gen.dist_folder, 'resources/fonts'),
)
gen.copy_folder(
	os.path.join(gen.gen_folder, 'scripts'),
	os.path.join(gen.dist_folder, 'resources/scripts'),
)

gen.call_custom_function("generation_finished")
