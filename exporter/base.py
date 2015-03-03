# coding: utf-8

from __future__ import unicode_literals
from StringIO import StringIO

from collections import defaultdict
from math import isnan
from django.contrib.sites.models import Site
from django.db.models import IntegerField, ForeignKey, DateTimeField
from django.http import HttpResponse
from django.utils.encoding import force_text
import pandas
from slugify import slugify


class Exporter(object):
    model = None
    columns = ()
    verbose_overrides = {}
    CONTENT_TYPES = {
        'json': 'application/json',
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument'
                '.spreadsheetml.sheet',
    }

    def __init__(self, queryset=None):
        self.queryset = queryset
        if queryset is not None:
            if self.model is None:
                self.model = queryset.model
            elif self.model is not queryset.model:
                raise ValueError('`queryset` does not match '
                                 'the model defined in the exporter')

        if not self.columns:
            self.columns = [field.name for field in self.model._meta.fields]

        self.method_names = []
        self.lookups = []
        for column in self.columns:
            if hasattr(self, 'get_' + column):
                self.method_names.append(column)
            else:
                self.lookups.append(column)
        self.fields = {lookup: self.get_field(lookup)
                       for lookup in self.lookups}
        self.final_fields = {lookup: self.get_final_field(lookup)
                             for lookup in self.lookups}
        self.null_int_lookups = []
        self.datetime_lookups = []
        for lookup, field in self.final_fields.items():
            if isinstance(field, (IntegerField, ForeignKey)) and field.null:
                self.null_int_lookups.append(lookup)
            elif isinstance(field, DateTimeField):
                self.datetime_lookups.append(lookup)

    def get_field(self, lookup):
        return self.model._meta.get_field(lookup.split('__')[0])

    def get_final_field(self, lookup):
        model = self.model
        for part in lookup.split('__'):
            field = model._meta.get_field(part)
            if field.rel is not None:
                model = field.rel.to
        return field

    def get_verbose_name(self, column):
        if column in self.verbose_overrides:
            return self.verbose_overrides[column]
        if column in self.fields:
            return force_text(self.fields[column].verbose_name)
        return column

    def get_queryset(self):
        if self.queryset is not None:
            return self.queryset
        return self.model.objects.all()

    def to_dataframe(self):
        df = pandas.DataFrame.from_records(
            list(self.get_queryset().values_list(*self.lookups)),
            columns=self.lookups,
        )

        def clean_null_int(x):
            if x is None or isnan(x):
                return ''
            return int(x)

        # Avoids float representation of nullable integer fields
        for lookup in self.null_int_lookups:
            df[lookup] = df[lookup].apply(clean_null_int)

        def remove_timezone(dt):
            if dt is None:
                return ''
            return dt.replace(tzinfo=None)

        # Removes timezones to allow datetime serialization in some formats
        for lookup in self.datetime_lookups:
            df[lookup] = df[lookup].apply(remove_timezone)

        # Display verbose value of fields with `choices`
        for lookup, field in self.fields.items():
            if field.choices:
                df[lookup] = df[lookup].replace({k: force_text(v)
                                                 for k, v in field.choices})

        # Adds columns calculated from methods
        if self.method_names:
            methods_data = defaultdict(list)
            for obj in self.get_queryset():
                for method_name in self.method_names:
                    v = getattr(self, 'get_' + method_name)(obj)
                    methods_data[method_name].append(v)
            for method_name in self.method_names:
                df[method_name] = methods_data[method_name]

        # Reorders columns after adding those using methods
        df = df[list(self.columns)]
        # Adds verbose column names
        df.columns = [self.get_verbose_name(column) for column in df.columns]
        # Sets the first column (usually pk) as index
        df.set_index(df.columns[0], inplace=True)
        return df

    def to_json(self):
        return self.to_dataframe().to_json(None, orient='records',
                                           date_format='iso')

    def to_csv(self):
        return self.to_dataframe().to_csv(None, encoding='utf-8')

    def to_xlsx(self):
        f = StringIO()
        # We have to specify a temporary file name,
        # but no file will be created.
        writer = pandas.ExcelWriter('temp.xlsx', engine='xlsxwriter')
        writer.book.filename = f
        sheet_name = force_text(self.model._meta.verbose_name_plural)
        self.to_dataframe().to_excel(writer, sheet_name)
        writer.save()
        out = f.getvalue()
        f.close()
        return out

    def _to_response(self, content, extension, attachment=True):
        content_type = self.CONTENT_TYPES[extension]
        response = HttpResponse(content, content_type=content_type)
        filename = '[%s] %s %s' % (Site.objects.get_current().name,
                                   self.get_queryset().count(),
                                   self.model._meta.verbose_name_plural)
        disposition = 'filename="%s.%s"' % (slugify(filename), extension)
        if attachment:
            disposition += '; attachment'
        response['Content-Disposition'] = disposition
        return response

    def to_json_response(self):
        return self._to_response(self.to_json(), 'json')

    def to_csv_response(self):
        return self._to_response(self.to_csv(), 'csv')

    def to_xlsx_response(self):
        return self._to_response(self.to_xlsx(), 'xlsx')