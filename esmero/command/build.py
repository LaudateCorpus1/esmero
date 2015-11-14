"""Build

Traverses through a path looking for lexor files and creates an html
file based on the latest configuration file read.

"""
import re
import os
import sys
import textwrap
import glob
import os.path as pth
from datetime import datetime as date
from lexor import core
from lexor import lexor
from lexor.command.to import language_style
from esmero.command import config
from esmero.util.logging import L


DESC = """Traverses trough the specified path looking for lexor files
and creates an html file based on the latest configuration file read.

You may build specific files by specifying their names after the path
is given. i.e.

    esmero build . file1 file2 file2

Note that the extension is not necessary.

"""


DEFAULTS = {
    'website_path': '.',
    'assets_path': '.',
    'lexor_inputs': '',
}


def add_parser(subp, fclass):
    """Add a parser to the main subparser. """
    tmpp = subp.add_parser('build',
                           help='create the website',
                           formatter_class=fclass,
                           description=textwrap.dedent(DESC))
    tmpp.add_argument('files', metavar='files', nargs='*',
                      type=str,
                      help='files to be converted')
    tmpp.add_argument('--log', type=language_style,
                      help='log language')
    tmpp.add_argument('--quiet', '-q', action='store_true',
                      help='suppress warning messages')
    tmpp.add_argument('--no-display', '-n', action='store_true',
                      help="suppress output")
    tmpp.add_argument('--force', '-f', action='store_true',
                      help="force page creation")


def cerr(msg):
    """Write messages to the stderr."""
    sys.stderr.write(msg)


def gather_lexor_files(path, bfiles):
    """Get a dictionary of lexor files and configuration files. """
    files = list()
    web = list()
    cfg = config.read_config()
    if 'skip-dir' in cfg:
        re_skip = re.compile(cfg['skip-dir'])
    else:
        re_skip = re.compile(r'_.*|[.].*')
    if 'ignore-file' in cfg:
        re_ignore = re.compile(cfg['ignore-file'])
    else:
        re_ignore = re.compile(r'_.*|[.].*')
    for dirname, dirnames, filenames in os.walk(path):
        allowed = list()
        for subdir in dirnames:
            L.info("looking for '%s/%s/esmero.json'", dirname, subdir)
            esmero_config = pth.exists(
                '%s/%s/esmero.json' % (dirname, subdir)
            )
            if esmero_config:
                web.append('%s/%s' % (dirname, subdir))
            elif re_skip.match(subdir) is None:
                allowed.append(subdir)

        if len(bfiles) == 0:
            for name in filenames:
                if re_ignore.match(name) is not None:
                    continue
                if name.endswith('.lex'):
                    files.append(pth.join(dirname, name))
        else:
            for name in filenames:
                if re_ignore.match(name) is not None:
                    continue
                name = pth.join(dirname, name)
                for bfile in bfiles:
                    if name.endswith('.lex') and bfile in name:
                        files.append(name)

        del dirnames[:]
        dirnames.extend(allowed)
    return cfg, files, web


def _append_queue(path, queue, files):
    """Recursive definition to gather the files in a path. """
    cfg, files, other = gather_lexor_files(path, files)
    queue.append((cfg, files))
    for path in other:
        _append_queue(path, queue, files)


def build_lexor_list(path, files):
    """Use this function instead of `gather_lexor_files` to get a
    list of lexor files to transform along with the configuration
    files."""
    queue = list()
    _append_queue(path, queue, files)
    return queue


def get_theme_templates(root, log_writer):
    """Obtain the theme documents. """
    theme_list = glob.glob('%s/*.lex' % root)
    theme = dict()
    redo = True
    for lex_file in theme_list:
        path = lex_file[:-4]
        name = pth.basename(path)
        html_file = path + '.html'
        theme[name], log = lexor(lex_file)
        if log:
            cerr('\n')
            log_writer.write(log, sys.stderr)
            cerr('... ')
        redo = False
        if pth.exists(html_file):
            date_lex = date.fromtimestamp(pth.getmtime(lex_file))
            date_html = date.fromtimestamp(pth.getmtime(html_file))
            if date_html < date_lex:
                redo = True
        else:
            date_html = date(1, 1, 1)
            redo = True
        aux = dict()
        for theme_file in glob.iglob('%s/*.lex' % path):
            cerr('loading theme file: `%s` ... ' % theme_file)
            L.info("loading theme file: '%s'", theme_file)
            file_name = pth.basename(theme_file)
            aux[file_name], log = lexor(theme_file)
            if log:
                L.info('found errors in %s', theme_file)
                cerr('\n')
                log_writer.write(log, sys.stderr)
            else:
                cerr('done\n')
            date_lex = date.fromtimestamp(pth.getmtime(theme_file))
            if date_html < date_lex:
                redo = True
        if redo:
            open(html_file, 'w').close()
        tagname = '%s:include' % name
        doc = theme[name]
        nodes = doc.get_nodes_by_name(tagname)

        for node in nodes:
            file_name = node[0].data
            if file_name in aux:
                node.parent.extend_before(
                    node.index, aux[file_name]
                )
                del node.parent[node.index]
    return theme, redo


def build_file(
        lex_file, theme, parser, settings,
        doc_writer, log_writer, arg, cfg
        ):
    with open(lex_file) as fp:
        text = fp.read()
    parser.parse(text, lex_file)
    doc = parser.doc

    ver = settings.get('theme', '')
    doc.meta['version'] = ver

    if ver in theme:
        doc.meta['__THEME__'] = theme[ver].clone_node(True)
    doc.meta['__ROOT__'] = cfg['esmero']['root']
    converter = core.Converter('lexor', 'html', 'default')
    converter.packages = [ver]
    converter.convert(doc)
    if parser.log:
        converter.update_log(parser.log, False)
    doc, log = converter.pop()
    if log:
        cerr('\n')
        log_writer.write(log, sys.stderr)
        cerr('... ')
    doc_writer.write(doc, lex_file[:-4] + '.html', 'w')


def build_site(arg, cfg, settings, files):
    """Build the website. """
    L.info('... COMPILING FILES')
    theme_path = settings.get('theme-path', '')
    parser = core.Parser('lexor', 'default')
    doc_writer = core.Writer('html', 'default')
    log_writer = core.Writer('lexor', 'log')
    theme, theme_redo = get_theme_templates(theme_path, log_writer)
    for fname in files:
        cerr('Checking %s ... ' % fname)
        L.info('checking %s ... ', fname)
        redo = False
        html_file = fname[:-4] + '.html'
        if theme_redo:
            cerr('[THEME CHANGE]: Building ... ')
            L.info('  [theme-change]: building ... ')
            redo = True
        elif arg.force:
            cerr('[FORCE]: Building ... ')
            L.info('  [force]: building ... ')
            redo = True
        elif pth.exists(html_file):
            date_lex = date.fromtimestamp(pth.getmtime(fname))
            date_html = date.fromtimestamp(pth.getmtime(html_file))
            if date_html < date_lex:
                cerr('[FILE CHANGE]: Building ... ')
                L.info('  [file-change]: building ... ')
                redo = True
        else:
            redo = True
        if redo:
            build_file(
                fname,
                theme,
                parser,
                settings,
                doc_writer,
                log_writer,
                arg,
                cfg
            )
        cerr('done.\n')


def run():
    """Run the command.

    The configuration file accepts:

    theme-path: The path where all the themes reside, these are lex
                files and they may have a folder that goes by the
                same name (without the lex extension). In this
                folder we put the other templates for the theme as
                well as python files which can help in the creation
                of the theme.

    theme: The name of the theme that we want to select from the
           theme-path.

    lexor-path: Path from where we can load python modules that are
                general enough for the whole site.

    """
    if 'LEXORINPUTS' not in os.environ:
        os.environ['LEXORINPUTS'] = ''
    lexor_inputs = os.environ['LEXORINPUTS']
    arg = config.CONFIG['arg']
    cfg = config.get_cfg(['build'])
    queue = build_lexor_list(arg.inputpath, arg.files)
    for settings, files in queue:
        if L.on:
            L.info('-----------------------')
            L.info('using configuration ...')
            for key in settings:
                L.info('   %s: %s', key, settings[key])
            L.info('on ...')
            for item in files:
                L.info('     %s', item)
        if lexor_inputs:
            os.environ['LEXORINPUTS'] = '%s:%s' % (
                settings['lexor-path'], lexor_inputs
            )
        elif 'lexor-path' in settings:
            os.environ['LEXORINPUTS'] = '%s' % settings['lexor-path']
        L.info('- $LEXORINPUTS: %s', os.environ['LEXORINPUTS'])
        build_site(arg, cfg, settings, files)
