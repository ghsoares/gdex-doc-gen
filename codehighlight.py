
registered_languages = {}

def highlight_code(code, language, params = {}):
	if not language in registered_languages:
		# Default for text markup
		markup = registered_languages["text"]["markup"](code, params)
		language_name = language.upper()
	else:
		language_info = registered_languages[language]

		markup = language_info["markup"](code, params)
		language_name = language_info["name"]

	return {
		"markup": markup['highlighted'],
		"style_defs": markup['style_defs'],
		"language_name": language_name
	}

def register_language(language_id, language_name, markup_function):
	registered_languages[language_id] = {
		"name": language_name,
		"markup": markup_function
	}

def create_markup(language, lexer):
	from pygments.formatters import HtmlFormatter
	formatter = HtmlFormatter(nowrap=True, nobackground=True)

	style_preffix = f".codeblocks > .language.{language} > pre > code"
	style_defs = formatter.get_style_defs(arg=style_preffix)
	style_defs = style_defs.split("\n")

	# Remove style definitions which will be override by the custom style, anyway
	style_defs = [line for line in style_defs if line.startswith(style_preffix)]

	def markup(code, params):
		from pygments import highlight
		
		highlighted = highlight(code, lexer(), formatter)
		
		return {
			"highlighted": highlighted,
			"style_defs": style_defs
		}
	return markup

def create_and_register_markup(language, language_name, lexer):
	register_language(language, language_name, create_markup(language, lexer))

def get_supported_languages():
	return [lang for lang in iter(registered_languages.keys()) if lang != "text"]

import pygments.lexers

from syntax_highlight.gdscript import GDScriptLexer

create_and_register_markup("text", "Plain Text", pygments.lexers.TextLexer)
create_and_register_markup("html", "HTML", pygments.lexers.HtmlLexer)
create_and_register_markup("bash", "Bash", pygments.lexers.BashLexer)
create_and_register_markup("csharp", "C#", pygments.lexers.CSharpLexer)
create_and_register_markup("gdscript", "GDScript", GDScriptLexer)





