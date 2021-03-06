# coding: utf-8

from __future__ import unicode_literals
import warnings

from django.apps import apps
from django.db import connection
from django.db.models import (
    CharField, ForeignKey, ManyToManyField, permalink, SmallIntegerField,
    DateField, PositiveSmallIntegerField, Model)
from django.db.models.sql import EmptyResultSet
from django.template.defaultfilters import date
from django.utils.encoding import python_2_unicode_compatible, force_text
from django.utils.safestring import mark_safe
from django.utils.translation import (
    ungettext_lazy, ugettext_lazy as _, ugettext)
from common.utils.abbreviate import abbreviate
from common.utils.html import capfirst, href, date_html, sc
from common.utils.sql import get_raw_query
from common.utils.text import str_list
from .base import (CommonModel, LOWER_MSG, PLURAL_MSG, calc_pluriel,
                   UniqueSlugModel, AutoriteModel)
from .evenement import Evenement


__all__ = (
    'Profession', 'Membre', 'TypeDEnsemble', 'Ensemble')


# TODO: Songer à l’arrivée des Emplois.
@python_2_unicode_compatible
class Profession(AutoriteModel, UniqueSlugModel):
    nom = CharField(_('nom'), max_length=200, help_text=LOWER_MSG, unique=True,
                    db_index=True)
    nom_pluriel = CharField(_('nom (au pluriel)'), max_length=230, blank=True,
                            help_text=PLURAL_MSG)
    nom_feminin = CharField(
        _('nom (au féminin)'), max_length=230, blank=True,
        help_text=_('Ne préciser que s’il est différent du nom.'))
    parent = ForeignKey('self', blank=True, null=True,
                        related_name='enfants', verbose_name=_('parent'))
    classement = SmallIntegerField(_('classement'), default=1, db_index=True)

    class Meta(object):
        verbose_name = ungettext_lazy('profession', 'professions', 1)
        verbose_name_plural = ungettext_lazy('profession', 'professions', 2)
        ordering = ('classement', 'nom')
        permissions = (('can_change_status', _('Peut changer l’état')),)

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        relations = ('auteurs', 'elements_de_distribution',)
        if all_relations:
            relations += ('enfants', 'individus', 'parties',)
        return relations

    @permalink
    def get_absolute_url(self):
        return 'profession_detail', (self.slug,)

    @permalink
    def permalien(self):
        return 'profession_permanent_detail', (self.pk,)

    def pretty_link(self):
        return self.html(caps=True)

    def link(self):
        return self.html()

    def short_link(self):
        return self.short_html()

    def pluriel(self):
        return calc_pluriel(self)

    def feminin(self):
        f = self.nom_feminin
        return f or self.nom

    def html(self, tags=True, short=False, caps=False, feminin=False,
             pluriel=False):
        if pluriel:
            nom = self.pluriel()
            if feminin:
                warnings.warn("Pas de feminin pluriel pour l'instant")
        elif feminin:
            nom = self.feminin()
        else:
            nom = self.nom
        if caps:
            nom = capfirst(nom)
        if short:
            nom = abbreviate(nom, min_vowels=1, min_len=4, tags=tags)
        url = '' if not tags else self.get_absolute_url()
        return href(url, nom, tags)

    def short_html(self, tags=True, feminin=False, pluriel=False):
        return self.html(tags, short=True, feminin=feminin, pluriel=pluriel)

    def __hash__(self):
        return hash(self.nom)

    def __str__(self):
        return capfirst(self.html(tags=False))

    def individus_count(self):
        return self.individus.count()
    individus_count.short_description = _('nombre d’individus')

    def oeuvres_count(self):
        return self.auteurs.oeuvres().count()
    oeuvres_count.short_description = _('nombre d’œuvres')

    def get_children(self):
        return self.enfants.all()

    def is_leaf_node(self):
        return not self.enfants.exists()

    @staticmethod
    def autocomplete_search_fields():
        return 'nom__unaccent__icontains', 'nom_pluriel__unaccent__icontains',


class PeriodeDActivite(Model):
    YEAR = 0
    MONTH = 1
    DAY = 2
    PRECISIONS = (
        (YEAR, _('Année')),
        (MONTH, _('Mois')),
        (DAY, _('Jour')),
    )
    debut = DateField(_('début'), blank=True, null=True)
    debut_precision = PositiveSmallIntegerField(
        _('précision du début'), choices=PRECISIONS, default=0)
    fin = DateField(_('fin'), blank=True, null=True)
    fin_precision = PositiveSmallIntegerField(
        _('précision de la fin'), choices=PRECISIONS, default=0)

    class Meta(object):
        abstract = True

    def _smart_date(self, attr, attr_precision, tags=True):
        d = getattr(self, attr)
        if d is None:
            return
        precision = getattr(self, attr_precision)
        if precision == self.YEAR:
            return force_text(d.year)
        if precision == self.MONTH:
            return date(d, 'F Y')
        if precision == self.DAY:
            return date_html(d, tags=tags)

    def smart_debut(self, tags=True):
        return self._smart_date('debut', 'debut_precision', tags=tags)

    def smart_fin(self, tags=True):
        return self._smart_date('fin', 'fin_precision', tags=tags)

    def smart_period(self, tags=True):
        debut = self.smart_debut(tags=tags)
        fin = self.smart_fin(tags=tags)
        # TODO: Rendre ceci plus simple en conservant les possibilités
        # d’internationalisation.
        if fin is None:
            if debut is None:
                return ''
            if self.debut_precision == self.DAY:
                t = ugettext('depuis le %(debut)s')
            else:
                t = ugettext('depuis %(debut)s')
        else:
            if debut is None:
                if self.fin_precision == self.DAY:
                    t = ugettext('jusqu’au %(fin)s')
                else:
                    t = ugettext('jusqu’à %(fin)s')
            else:
                if self.debut_precision == self.DAY:
                    if self.fin_precision == self.DAY:
                        t = ugettext('du %(debut)s au %(fin)s')
                    else:
                        t = ugettext('du %(debut)s à %(fin)s')
                else:
                    if self.fin_precision == self.DAY:
                        t = ugettext('de %(debut)s au %(fin)s')
                    else:
                        t = ugettext('de %(debut)s à %(fin)s')
        return t % {'debut': debut, 'fin': fin}
    smart_period.short_description = _('Période d’activité')


def limit_choices_to_instruments():
    return {'type': apps.get_model('libretto', 'Partie').INSTRUMENT}


@python_2_unicode_compatible
class Membre(CommonModel, PeriodeDActivite):
    ensemble = ForeignKey('Ensemble', related_name='membres',
                          verbose_name=_('ensemble'))
    # TODO: Ajouter nombre pour les membres d'orchestre pouvant être saisi
    #       au lieu d'un individu.
    individu = ForeignKey('Individu', related_name='membres',
                          verbose_name=_('individu'))
    instrument = ForeignKey(
        'Partie', blank=True, null=True, related_name='membres',
        limit_choices_to=limit_choices_to_instruments,
        verbose_name=_('instrument'))
    classement = SmallIntegerField(_('classement'), default=1)

    class Meta(object):
        verbose_name = _('membre')
        verbose_name_plural = _('membres')
        ordering = ('instrument', 'classement', 'debut')

    def html(self, tags=True):
        l = [self.individu.html(tags=tags)]
        if self.instrument:
            l.append('[%s]' % self.instrument.html(tags=tags))
        if self.debut or self.fin:
            l.append('(%s)' % self.smart_period(tags=tags))
        return mark_safe(' '.join(l))

    def __str__(self):
        return self.html(tags=False)

    def link(self):
        return self.html()


@python_2_unicode_compatible
class TypeDEnsemble(CommonModel):
    nom = CharField(_('nom'), max_length=30, help_text=LOWER_MSG)
    nom_pluriel = CharField(_('nom pluriel'), max_length=30, blank=True,
                            help_text=PLURAL_MSG)
    parent = ForeignKey('self', null=True, blank=True,
                        related_name='enfants', verbose_name=_('parent'))

    class Meta(object):
        verbose_name = ungettext_lazy('type d’ensemble', 'types d’ensemble', 1)
        verbose_name_plural = ungettext_lazy('type d’ensemble',
                                             'types d’ensemble', 2)
        ordering = ('nom',)

    def __str__(self):
        return self.nom

    @staticmethod
    def autocomplete_search_fields():
        return 'nom__unaccent__icontains', 'nom_pluriel__unaccent__icontains'


@python_2_unicode_compatible
class Ensemble(AutoriteModel, PeriodeDActivite, UniqueSlugModel):
    particule_nom = CharField(
        _('particule du nom'), max_length=5, blank=True, db_index=True)
    nom = CharField(_('nom'), max_length=75, db_index=True)
    # FIXME: retirer null=True quand la base sera nettoyée.
    type = ForeignKey('TypeDEnsemble', null=True, related_name='ensembles',
                      verbose_name=_('type'))
    # TODO: Permettre deux villes sièges.
    siege = ForeignKey('Lieu', null=True, blank=True,
                       related_name='ensembles',
                       verbose_name=_('localisation'))
    # TODO: Ajouter historique d'ensemble.

    individus = ManyToManyField(
        'Individu', through=Membre, related_name='ensembles',
        verbose_name=_('individus'))

    class Meta(object):
        ordering = ('nom',)

    def __str__(self):
        return self.html(tags=False)

    def nom_complet(self):
        return ('%s %s' % (self.particule_nom, self.nom)).strip()

    def html(self, tags=True):
        nom = self.nom_complet()
        if tags:
            return href(self.get_absolute_url(),
                        sc(nom, tags=tags), tags=tags)
        return nom

    def link(self):
        return self.html()

    @permalink
    def get_absolute_url(self):
        return 'ensemble_detail', (self.slug,)

    @permalink
    def permalien(self):
        return 'ensemble_permanent_detail', (self.pk,)

    def membres_html(self):
        return str_list([
            membre.html() for membre in
            self.membres.select_related('individu', 'instrument')])
    membres_html.short_description = _('membres')

    def membres_count(self):
        return self.membres.count()
    membres_count.short_description = _('nombre de membres')

    def apparitions(self):
        sql = """
        SELECT DISTINCT COALESCE(distribution.evenement_id, programme.evenement_id)
        FROM libretto_elementdedistribution AS distribution
        LEFT JOIN libretto_elementdeprogramme AS programme
            ON (programme.id = distribution.element_de_programme_id)
        WHERE distribution.ensemble_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, (self.pk,))
            evenement_ids = [t[0] for t in cursor.fetchall()]
        return Evenement.objects.filter(id__in=evenement_ids)

    def evenements_par_territoire(self, evenements_qs=None):
        if self.siege is None:
            return ()
        if evenements_qs is None:
            evenements_qs = self.apparitions()
        try:
            evenements_sql, evenements_params = get_raw_query(
                evenements_qs.order_by().values('pk', 'debut_lieu_id'))
        except EmptyResultSet:
            return ()
        sql = """
        WITH evenements AS (
            %s
        )
        (
            SELECT %%s, COUNT(id) FROM evenements
        ) UNION ALL (
            SELECT ancetre.nom, COUNT(evenement.id)
            FROM libretto_lieu AS ancetre
            INNER JOIN libretto_lieu AS lieu ON (
                lieu.tree_id = ancetre.tree_id
                AND lieu.lft BETWEEN ancetre.lft AND ancetre.rght)
            INNER JOIN evenements AS evenement ON (
                evenement.debut_lieu_id = lieu.id)
            WHERE (
                ancetre.tree_id = %%s
                AND %%s BETWEEN ancetre.lft AND ancetre.rght)
            GROUP BY ancetre.id
            ORDER BY ancetre.level
        );
        """ % evenements_sql
        with connection.cursor() as cursor:
            cursor.execute(sql, evenements_params + (
                ugettext('Monde'), self.siege.tree_id, self.siege.lft))
            data = cursor.fetchall()
        new_data = []
        for i, (name, count) in enumerate(data):
            try:
                exclusive_count = count - data[i+1][1]
            except IndexError:
                exclusive_count = count
            if exclusive_count > 0:
                new_data.append((name, count, exclusive_count))
        return new_data

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('elements_de_distribution',)

    @staticmethod
    def autocomplete_search_fields():
        return ('particule_nom__unaccent__icontains',
                'nom__unaccent__icontains',
                'siege__nom__unaccent__icontains')
