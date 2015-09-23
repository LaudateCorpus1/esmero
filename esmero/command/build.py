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
from datetime import datetime
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


def gather_lexor_files(path, bfiles):
    """Get a dictionary of lexor files and configuration files. """
    files = list()
    web = list()
    cfg = config.read_config()
    if 'skip-dir' in cfg:
        rskip = re.compile(cfg['skip-dir'])
    else:
        rskip = re.compile(r'_.*|[.].*')
    if 'ignore-file' in cfg:
        rignore = re.compile(cfg['ignore-file'])
    else:
        rignore = re.compile(r'_.*|[.].*')
    for dirname, dirnames, filenames in os.walk(path):
        allowed = list()
        for subdir in dirnames:
            L.info("checking for %r", '%s/%s/esmero.config' % (dirname, subdir))
            esmero_config = pth.exists(
                '%s/%s/esmero.config' % (dirname, subdir)
            )
            if esmero_config:
                web.append('%s/%s' % (dirname, subdir))
            elif rskip.match(subdir) is None:
                allowed.append(subdir)

        if len(bfiles) == 0:
            for name in filenames:
                if rignore.match(name) is not None:
                    continue
                if name.endswith('.lex'):
                    files.append(pth.join(dirname, name))
        else:
            for name in filenames:
                if rignore.match(name) is not None:
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
    L.info("appended: (%r, %r)", cfg, files)
    for path in other:
        _append_queue(path, queue, files)


def build_lexor_list(path, files):
    """Use this function instead of `gather_lexor_files` to get a
    list of lexor files to transform along with the configuration
    files."""
    queue = list()
    _append_queue(path, queue, files)
    return queue


def get_theme_templates(root):
    """Obtain the theme documents. """
    theme_list = glob.glob('%s/*.lex' % root)
    theme = dict()
    redo = False
    for lex_file in theme_list:
        path = lex_file[:-4]
        name = pth.basename(path)
        html_file = path + '.html'
        theme[name], log = lexor(lex_file)
        # Print log here
        redo = False
        if pth.exists(html_file):
            date_lex = datetime.fromtimestamp(pth.getmtime(lex_file))
            date_html = datetime.fromtimestamp(pth.getmtime(html_file))
            if date_html < date_lex:
                redo = True
        else:
            date_html = datetime(1, 1, 1)
            redo = True
        aux = dict()
        for theme_file in glob.iglob('%s/*.lex' % path):
            file_name = pth.basename(theme_file)
            aux[file_name], log = lexor(theme_file)
            # Print log here
            date_lex = datetime.fromtimestamp(pth.getmtime(theme_file))
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


def build_file(lex_file, theme, parser, settings, docwriter, logwriter, arg, cfg):
    with open(lex_file, 'r') as tmpf:
        text = tmpf.read()
    parser.parse(text, lex_file)
    doc = parser.doc

    ver = settings['template']
    doc.meta['version'] = ver

    if 'usepackage' in doc.meta:
        pkg = ',' + doc.meta['usepackage']
    else:
        pkg = ''

    doc.meta['usepackage'] = ver + pkg
    doc.meta['__THEME__'] = theme[ver].clone_node(True)
    doc.meta['__ROOT__'] = cfg['esmero']['root']
    converter = core.Converter('lexor', 'html', 'default')
    #converter.convert(doc)
    #if parser.log:
    #    converter.update_log(parser.log, False)
    #doc, log = converter.pop()
    # if log:
    #     sys.stderr.write('\n')
    #     logwriter.write(log, sys.stderr)
    #     sys.stderr.write('... ')
    docwriter.write(doc, lex_file[:-4] + '.html', 'w')
    namespace = core.get_converter_namespace()
    namespace.clear()


def build_site(arg, cfg, settings, files):
    """Build the website. """
    theme, theme_redo = get_theme_templates(settings['theme-path'])
    parser = core.Parser('lexor', 'default')
    docwriter = core.Writer('html', 'default')
    logwriter = core.Writer('lexor', 'log')
    for fname in files:
        sys.stderr.write('Checking %s ... ' % fname)
        if theme_redo:
            sys.stderr.write(' [THEME CHANGE]: Building ... ')
            build_file(fname, theme, parser, settings, docwriter, logwriter, arg, cfg)
            sys.stderr.write('done.\n')
            continue
        if arg.force:
            sys.stderr.write(' [FORCE]: Building ... ')
            build_file(fname, theme, parser, settings, docwriter, logwriter, arg, cfg)
            sys.stderr.write('done.\n')
            continue
        redo = False
        html_file = fname[:-4] + '.html'
        if pth.exists(html_file):
            date_lex = datetime.fromtimestamp(pth.getmtime(fname))
            date_html = datetime.fromtimestamp(pth.getmtime(html_file))
            if date_html < date_lex:
                redo = True
        else:
            redo = True
        if redo:
            sys.stderr.write(' [FILE CHANGE]: Building ... ')
            build_file(fname, theme, parser, settings, docwriter, logwriter, arg, cfg)
        sys.stderr.write('done.\n')


def run():
    """Run the command. """
    lexor_inputs = os.environ.get('LEXORINPUTS', '')
    arg = config.CONFIG['arg']
    cfg = config.get_cfg(['build'])
    queue = build_lexor_list(arg.inputpath, arg.files)
    L.info("queue: %r", queue)
    for settings, files in queue:
        if lexor_inputs:
            os.environ['LEXORINPUTS'] = '%s:%s' % (
                settings['lexor-path'], lexor_inputs
            )
        else:
            os.environ['LEXORINPUTS'] = '%s' % settings['lexor-path']
        print os.environ['LEXORINPUTS']
        L.info('$LEXORINPUTS: %s', os.environ['LEXORINPUTS'])
        build_site(arg, cfg, settings, files)
