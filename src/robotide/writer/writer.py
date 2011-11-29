#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import csv
import os
import re
from robotide.writer.tablewriter import TableWriter
import template

from StringIO import StringIO
from robot.parsing.settings import Documentation
from robotide import utils


def FileWriter(output, format, name=None, template=None, pipe_separated=False, line_separator=os.linesep):
    try:
        Writer = {'tsv': TsvFileWriter, 'txt': TxtFileWriter(pipe_separated)}[format]
        return Writer(output, line_separator)
    except KeyError:
        return HtmlFileWriter(output, name, template)


class _WriterHelper(object):

    def __init__(self, output, cols):
        self._output = output
        self._cols = cols
        self._tc_name = self._uk_name = ''
        self._in_tcuk = False
        self._in_setting_table = False
        self._in_for_loop = False

    def _write(self, data):
        self._output.write(data)

    def close(self, close_output=True):
        if close_output:
            self._output.close()

    def start_settings(self):
        self._write_header(self._setting_titles)
        self._in_setting_table = True

    def end_settings(self):
        self._write_empty_row()
        self._in_setting_table = False

    def start_variables(self):
        self._write_header(self._variable_titles)

    def end_variables(self):
        self._write_empty_row()

    def start_testcases(self, testcase_table):
        self._write_header(self._testcase_titles, testcase_table.header)

    def end_testcases(self):
        pass

    def start_keywords(self):
        self._write_header(self._keyword_titles)

    def end_keywords(self):
        pass

    def start_testcase(self, tc):
        self._tc_name = tc.name
        self._in_tcuk = True

    def end_testcase(self):
        if self._tc_name:
            self._write_data([self._get_tcuk_name()])
        self._write_empty_row()
        self._in_tcuk = False

    def start_keyword(self, uk):
        self._uk_name = uk.name
        self._in_tcuk = True

    def end_keyword(self):
        if self._uk_name:
            self._write_data([self._get_tcuk_name()])
        self._write_empty_row()
        self._in_tcuk = False

    def start_for_loop(self, loop):
        self.element(loop)
        self._in_for_loop = True

    def end_for_loop(self):
        self._in_for_loop = False

    def element(self, element):
        content = self._get_element_as_list(element)
        if self._in_tcuk:
            self._write_data([self._get_tcuk_name()]+content, indent=1)
        else:
            self._write_data(content)

    def _get_element_as_list(self, element):
        if not self._in_for_loop:
            return element.as_list()
        else:
            return element.as_list(indent=True)

    def _split_data(self, data, indent=0):
        rows = []
        firstrow = True
        while data or firstrow:
            if firstrow:
                current = data[:self._cols]
                data = data[self._cols:]
                firstrow = False
            else:
                current = ['']*indent + ['...'] + data[:self._cols-indent-1]
                data = data[self._cols-indent-1:]
            if current and current[-1].strip() == '':
                current[-1] = '${EMPTY}'
            rows.append(current)
        return rows

    def _add_padding(self, row, padding=''):
        return row + [padding] * (self._cols - len(row))

    def _encode(self, row):
        return [ cell.encode('UTF-8').replace('\n', ' ') for cell in row ]

    def _write_empty_row(self):
        self._write_data([])


class TsvFileWriter(_WriterHelper):
    _setting_titles = ['Setting']
    _variable_titles = ['Variable']
    _testcase_titles = ['Test Case']
    _keyword_titles = ['Keyword']

    def __init__(self, output, line_separator):
        _WriterHelper.__init__(self, output, 8)
        self._writer = csv.writer(self._output, dialect='excel-tab',
                                  lineterminator=line_separator)

    def _get_tcuk_name(self):
        name = self._tc_name or self._uk_name
        self._tc_name = self._uk_name = ''
        return name

    def _write_header(self, row, headers=None):
        self._writer.writerow(['*%s*' % cell for cell in row])

    def _write_data(self, data, indent=0):
        data = self._encode(data)
        for row in self._split_data(data, indent):
            self._writer.writerow(self._add_padding(row))

def TxtFileWriter(pipe_separator=False):
    return PipeSeparatedTxtWriter if pipe_separator else SpaceSeparatedTxtWriter

class SpaceSeparatedTxtWriter(_WriterHelper):
    _setting_titles = 'Settings'
    _variable_titles = 'Variables'
    _testcase_titles = 'Test Cases'
    _keyword_titles = 'Keywords'
    _separator = ' '*4

    def __init__(self, output, line_separator):
        _WriterHelper.__init__(self, output, 8)
        self._line_separator = line_separator
        self._indent_separator = self._separator

    def end_testcases(self):
        _WriterHelper.end_testcases(self)
        self._table_writer.write()

    def end_keywords(self):
        _WriterHelper.end_keywords(self)
        self._table_writer.write()

    def end_variables(self):
        _WriterHelper.end_variables(self)
        self._table_writer.write()

    def end_settings(self):
        _WriterHelper.end_settings(self)
        self._table_writer.write()

    def start_testcase(self, tc):
        self._write_data([tc.name])
        self._in_tcuk = True

    def start_keyword(self, uk):
        self._write_data([uk.name])
        self._in_tcuk = True

    def element(self, element):
        content = self._get_element_as_list(element)
        if self._in_tcuk:
            self._write_data(content, indent=1)
        elif self._in_setting_table:
            self._write_data([content[0].ljust(14)] + content[1:])
        else:
            self._write_data(content)

    def _write_header(self, title, headers=None):
        additional_headers = headers or []
        self._table_writer = TableWriter(self._output, self._separator, self._line_separator)
        self._table_writer.add_headers(['*** %s ***' % title]+additional_headers[1:])

    def _write_data(self, data, indent=0):
        data = self._escape_space_separated_format_specific_data(data)
        for row in self._split_data(self._encode(data)):
            self._write_row(row, indent)

    def _escape_space_separated_format_specific_data(self, data):
        data[1:] = self._escape_empty_elements(data[1:])
        self._escape_empty_first_element(data)
        return self._escape_whitespaces(data)

    def _escape_empty_first_element(self, data):
        if data and data[0].strip() == '':
            data[0] = '\\' # support FOR and PARALLEL blocks

    def _escape_empty_elements(self, data):
        return [d.strip() or '${EMPTY}' for d in data]

    def _escape_whitespaces(self, data):
        return [re.sub('\s\s+(?=[^\s])', lambda match: '\\'.join(match.group(0)), item) for item in data]

    def _write_row(self, cells, indent=0):
        if indent:
            cells.insert(0,'')
        self._table_writer.add_row(cells)

    def _format_row(self, cells):
        return self._separator.join(cells)


class PipeSeparatedTxtWriter(SpaceSeparatedTxtWriter):

    _separator = ' | '

    def _write_header(self, title, headers=None):
        additional_headers = headers or []
        self._table_writer = TableWriter(self._output, self._separator,
                                         line_separator=self._line_separator,
                                         line_prefix='| ',
                                         line_postfix=' |')
        self._table_writer.add_headers(['*** %s ***' % title]+additional_headers[1:])

    def _escape_whitespaces(self, data):
        return data #FIXME: PipeSeparatedTxtWriter is not a SpaceSeparatedTxtWriter

    def _format_row(self, cells):
        if not cells:
            return ''
        return '| %s |' % (' | '.join(cells))


class HtmlFileWriter(_WriterHelper):
    _setting_titles = ['Setting']
    _variable_titles = ['Variable']
    _testcase_titles = ['Test Case']
    _keyword_titles = ['Keyword']
    compiled_regexp = re.compile(r'(\\+)n ')

    def __init__(self, output, name=None, tmpl=None):
        self._content = tmpl
        _WriterHelper.__init__(self, output, 5)
        self._writer = utils.HtmlWriter(StringIO())

    def close(self, close_output=True):
        self._output.write(self._content.encode('UTF-8'))
        _WriterHelper.close(self, close_output)

    def end_settings(self):
        _WriterHelper.end_settings(self)
        self._end_table(template.settings_table)

    def end_variables(self):
        _WriterHelper.end_variables(self)
        self._end_table(template.variables_table)

    def end_testcases(self):
        _WriterHelper.end_testcases(self)
        self._end_table(template.testcases_table)

    def end_keywords(self):
        _WriterHelper.end_keywords(self)
        self._end_table(template.keywords_table)

    def element(self, element):
        colspan = isinstance(element, Documentation)
        content = self._get_element_as_list(element)
        if self._in_tcuk:
            self._write_data([self._get_tcuk_name()]+content,
                             indent=1, colspan=colspan)
        else:
            self._write_data(content, colspan=colspan)

    def _end_table(self, table_replacer):
        table = self._writer.output.getvalue().decode('UTF-8')
        self._content = table_replacer(table, self._content)
        self._writer = utils.HtmlWriter(StringIO())

    def _write_header(self, titles, header=None):
        self._writer.start('tr')
        for i, cell in enumerate(titles):
            self._writer.element('th', cell, self._get_attrs(i, len(titles)))
        self._writer.end('tr')

    def _write_data(self, data, indent=0, colspan=False):
        for row in self._split_data(data, indent):
            if not colspan:
                row = self._add_padding(row)
            self._writer.start('tr', newline=True)
            for i, cell in enumerate(row):
                if i != 0:
                    cell = utils.html_escape(cell)
                cell = self._add_br_to_newlines(cell)
                attrs = self._get_attrs(i, len(row), colspan)
                self._writer.element('td', cell, attrs, escape=False)
            self._writer.end('tr')

    def _add_br_to_newlines(self, input):
        def replacer(match):
            blashes = len(match.group(1))
            if blashes % 2 == 1:
                return '%sn<br>\n' % match.group(1)
            return match.group()
        return self.compiled_regexp.sub(replacer, input)

    def _get_attrs(self, index, rowlength, colspan=True):
        if index == 0:
            return {'class': 'name'}
        if colspan and index == rowlength-1:
            return {'colspan': str(self._cols-index)}
        return {}

    def _get_tcuk_name(self):
        if self._tc_name:
            n, t = self._tc_name, 'test'
        elif self._uk_name:
            n, t = self._uk_name, 'keyword'
        else:
            return ''
        self._tc_name = self._uk_name = ''
        return '<a name="%s_%s">%s</a>' % (t, utils.html_attr_escape(n),
                                           utils.html_escape(n))