#! /usr/bin/python

# A script to convert the Buildbot Texinfo documentation into rst as a first
# step for #189

# TODO:
#  xrefs

import re
import sys
import textwrap
import cStringIO

INDENT = 4

# ref handling

class Ref(object):
    instances = {}

    @classmethod
    def get(cls, name):
        if name in cls.instances:
            return cls.instances[name]
        else:
            return cls(name)

    def __init__(self, name):
        self.instances[name] = self
        self.label = re.sub('[^a-zA-Z]', '-', name).lower()
        self.referenced = False

    def reference(self):
        self.referenced = True

# paras

class BasePara(object):

    def finalize(self, footnotes):
        pass

class HeadingPara(BasePara):

    def __init__(self, header, character):
        super(HeadingPara, self).__init__()
        self.header = header
        self.character = character
        self.ref = Ref.get(header)

    def __str__(self):
        pre = ''
        if self.ref.referenced:
            pre = '.. _%s:\n\n' % self.ref.label
        return pre + "%s\n%s" % (self.header, self.character * len(self.header))

class FootnotesPara(BasePara):

    def __init__(self, footnotes):
        super(FootnotesPara, self).__init__()
        self.footnotes = footnotes

    def __str__(self):
        dst = cStringIO.StringIO()

        dst.write(".. rubric:: footnotes\n\n")
        for fn in self.footnotes:
            dst.write(textwrap.fill(fn, 78, subsequent_indent="   ") + '\n')

        return dst.getvalue()

class IndexPara(BasePara):

    def __init__(self):
        self.entries = []

    def add_index(self, args):
        idxtype, term = args[0], ' '.join(args[1:])
        self.entries.append(term)

    def __str__(self):
        return '.. index::\n' + '\n'.join([ '%ssingle: %s' % (' '*INDENT, e)
                                            for e in self.entries ])

class Para(BasePara):

    verbatim_inlines = [
        (re.compile(r"@@"), '@'),
        (re.compile(r"@{"), '{'),
        (re.compile(r"@}"), '}'),
    ]

    inlines = [
        (re.compile(r"``"), '"'),
        (re.compile(r"''"), '"'),
        (re.compile(r'@(?:file|code|var|command){((?:[^}]|@})*)}'), r'``\1``'),
        (re.compile(r'@(?:i|emph){((?:[^}]|@})*)}'), r'*\1*'),
        (re.compile(r'@(?:url|uref){((?:[^}]|@})*),([^}]*)}'), r'`\2 <\1>`_'),
        (re.compile(r'@url{((?:[^}]|@})*)}'), r'\1'),
    ] + verbatim_inlines

    footnote_re = re.compile('@footnote{((?:[^}]|@})*)}')
    ref_re = re.compile('@(p?x?ref){((?:[^}]|@})*)}')

    def __init__(self, indent):
        super(Para, self).__init__()
        self.indent = indent
        self.text = ''

    def __iadd__(self, text):
        self.text += text
        return self

    def __nonzero__(self):
        return bool(self.text.strip())

    def __str__(self):
        return '%s' % textwrap.fill(self.text, 78,
                                    initial_indent=' '*self.indent,
                                    subsequent_indent=' '*self.indent,
                                    replace_whitespace=True)

    def finalize(self, footnotes):
        text = self.text
        for pat, repl in self.inlines:
            text = pat.sub(repl, text)

        def footnote_repl(mo):
            num = len(footnotes)+1
            footnotes.append('.. [%d] %s' % (num, mo.group(1)))
            return " [%d]_" % num
        text = self.footnote_re.sub(footnote_repl, text)

        def ref_repl(mo):
            ref = Ref.get(mo.group(2))
            ref.reference()
            pre = ''
            if mo.group(1) == 'pxref':
                pre = 'see '
            elif mo.group(1) == 'xref':
                pre = 'See '
            return "%s:ref:`%s`" % (pre, ref.label)
        text = self.ref_re.sub(ref_repl, text)

        mo = re.search('@[a-z]+{[^}]*}', text)
        if mo:
            print "WARNING: @..{..} still remain:", mo.group(0)
        self.text = text

class VerbatimPara(Para):

    # only do the verbatim inlines
    inlines = Para.verbatim_inlines

    def __str__(self):
        indented = '\n'.join([ ' '*(INDENT+self.indent) + l
                               for l in self.text.strip().split('\n')])
        return '::\n\n%s' % indented

class IgnorePara(Para):

    def __iadd__(self, other):
        return self

    def __str__(self):
        return ''

class ListPara(Para):

    def __init__(self, indent, env):
        super(ListPara, self).__init__(indent)
        self.env = env

    def __iadd__(self, other):
        self.env.list_element_got_text()
        return super(ListPara, self).__iadd__(other)

class BulletedPara(ListPara):

    def __init__(self, indent, env, char):
        super(BulletedPara, self).__init__(indent, env)
        self.char = char

    def __str__(self):
        return textwrap.fill('%-*s %s' % (INDENT-1, self.char, self.text),
                initial_indent=' ' * (self.indent - INDENT),
                subsequent_indent=' ' * (self.indent))

class FieldPara(ListPara):

    def __init__(self, indent, env, fieldname):
        super(FieldPara, self).__init__(indent, env)
        self.fieldname = fieldname
        self.env.list_element_got_text()

    def __nonzero__(self):
        return True

    def __str__(self):
        return textwrap.fill(':%s: %s' % (self.fieldname.replace(':', r'\:'),
                                         self.text),
                initial_indent=' ' * (self.indent - INDENT),
                subsequent_indent=' ' * (self.indent))

# envs

class Env(object):

    def __init__(self, parent_env, args):
        self.parent_env = parent_env
        self.args = args
        if self.parent_env:
            self.indent = self.parent_env.indent
        else:
            self.indent = 0

    def set_item(self, remainder):
        pass

    def make_para(self):
        pass

class TextEnv(Env):

    def make_para(self):
        return Para(self.indent)

class IgnoreEnv(Env):

    def make_para(self):
        return IgnorePara(self.indent)

class VerbatimEnv(Env):

    def make_para(self):
        return VerbatimPara(self.indent)

class ListEnv(Env):

    BULLETS, NUMBERS, FIELDS, TABLE = range(4)

    def __init__(self, parent_env, args):
        super(ListEnv, self).__init__(parent_env, args)
        self.list_type = self.FIELDS
        if '@bullet' in args:
            self.list_type = self.BULLETS
        elif '@enumerate' in args:
            self.list_type = self.NUMBERS
        elif '@table' in args:
            self.list_type = self.TABLE
        self.indent += INDENT
        self.new_item = False

    def set_item(self, remainder):
        self.new_item = True
        if self.list_type in (self.FIELDS, self.TABLE):
            self.last_field = remainder

    def list_element_got_text(self):
        # called when a list item actually gets some content; this allows
        # us to keep giving out ListPara's until we get one that fills with
        # text
        self.new_item = False

    def make_para(self):
        if not self.new_item:
            return Para(self.indent)
        if self.list_type == self.BULLETS:
            return BulletedPara(self.indent, self, '*')
        elif self.list_type == self.NUMBERS:
            return BulletedPara(self.indent, self, '#')
        else: # TABLE or FIELDS
            return FieldPara(self.indent, self, self.last_field)

class File(object):

    envs = {
            '@menu' : IgnoreEnv,
            '@enumerate' : ListEnv,
            '@itemize' : ListEnv,
            '@example' : VerbatimEnv,
            '@verbatim' : VerbatimEnv,
            '@table' : ListEnv,
            '@copying' : IgnoreEnv,
            '@ifinfo' : IgnoreEnv,
            '@ifnottex' : IgnoreEnv,
            '@titlepage' : IgnoreEnv,
            '@direntry' : IgnoreEnv,
        }
    ignore_lines = set(['@node'])
    sectioning_headers = {
            '@chapter' : '*',
            '@section' : '=',
            '@subsection' : '-',
            '@subsubsection' : '^',
            '@heading' : '"',
            '@subheading' : "'",
        }
    index_re = re.compile('@..?index$')

    def __init__(self, filename):
        self.filename = filename
        self._footnotes = []
        self._paras = []
        self._para = None
        self._env_stack = [ TextEnv(None, []) ]
        self._flush_para()

        src = open(self.filename)

        for line in src.readlines():
            line = line.rstrip()
            print line
            split = line.split()
            if split:
                if split[0] in self.ignore_lines:
                    pass
                elif split[0] in self.envs:
                    self._flush_para()
                    env = self.envs[split[0]](self._env_stack[-1], split)
                    self._env_stack.append(env)
                    self._para = env.make_para()
                elif split[0] == '@end':
                    self._env_stack.pop()
                    self._flush_para()
                elif split[0] == '@item':
                    self._env_stack[-1].set_item(' '.join(split[1:]))
                    self._flush_para()
                elif split[0] in self.sectioning_headers:
                    c = self.sectioning_headers[split[0]]
                    hdr = " ".join(split[1:])
                    self._add_para(HeadingPara(hdr, c))
                elif self.index_re.match(split[0]):
                    if not self._paras or not isinstance(self._paras[-1], IndexPara):
                        self._flush_para()
                        self._paras.append(IndexPara())
                    self._paras[-1].add_index(split)
                else:
                    self._add_to_para(line + '\n')
            else:
                # newline
                if not isinstance(self._para, VerbatimPara):
                    self._flush_para()
                else:
                    self._add_to_para('\n')
        self._flush_para()

        # finish with footnotes (set from paras' finalize method)
        if self._footnotes:
            self._paras.append(FootnotesPara(self._footnotes))

    def _add_to_para(self, text):
        self._para += text

    def _flush_para(self):
        if self._para:
            self._para.finalize(self._footnotes)
            self._paras.append(self._para)
        self._para = self._env_stack[-1].make_para()

    def _add_para(self, para):
        self._flush_para()
        self._paras.append(para)

    def __str__(self):
        output = "\n\n".join([ str(p) for p in self._paras ])

        # shorten up intros to verbatim paras
        output = output.replace(':\n\n::\n\n', '::\n\n')
        output = output.replace('\n\n::\n\n', ' ::\n\n')
        output = re.sub(' +$', '', output, flags=re.M)

        return output


if __name__ == "__main__":
    files = [ (File(fn), fn) for fn in sys.argv[1:] ]
    for f, fn in files:
        open(fn.replace('texinfo', 'rst'), "w").write(str(f))
