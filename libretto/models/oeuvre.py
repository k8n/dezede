# coding: utf-8

from __future__ import unicode_literals
from collections import OrderedDict
import re
from django.core.exceptions import ValidationError
from django.contrib.humanize.templatetags.humanize import apnumber
from django.core.validators import RegexValidator
from django.db.models import (
    CharField, ManyToManyField, ForeignKey, IntegerField, TextField,
    BooleanField, permalink, get_model, SmallIntegerField, PROTECT, Count,
    PositiveSmallIntegerField)
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import (
    ungettext_lazy, ugettext, ugettext_lazy as _)
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from polymorphic_tree.managers import PolymorphicMPTTModelManager, \
    PolymorphicMPTTQuerySet
from polymorphic_tree.models import PolymorphicMPTTModel, \
    PolymorphicTreeForeignKey
from tinymce.models import HTMLField
from cache_tools import model_method_cached
from .base import (
    CommonModel, AutoriteModel, LOWER_MSG, PLURAL_MSG, calc_pluriel, SlugModel,
    UniqueSlugModel, CommonQuerySet, CommonManager, PublishedManager,
    OrderedDefaultDict, PublishedQuerySet, CommonTreeManager,
    CommonTreeQuerySet, TypeDeParente, TypeDeCaracteristique, Caracteristique,
    AncrageSpatioTemporel)
from common.utils.html import capfirst, hlp, href, cite, em
from common.utils.text import str_list, str_list_w_last, to_roman
from .individu import Individu
from .personnel import Profession
from .source import Source


__all__ = (
    b'GenreDOeuvre', b'TypeDeCaracteristiqueDOeuvre',b'CaracteristiqueDOeuvre',
    b'Partie', b'Role', b'Instrument', b'Pupitre', b'TypeDeParenteDOeuvres',
    b'ParenteDOeuvres', b'Auteur', b'Oeuvre'
)


@python_2_unicode_compatible
class GenreDOeuvre(CommonModel, SlugModel):
    nom = CharField(_('nom'), max_length=255, help_text=LOWER_MSG, unique=True,
                    db_index=True)
    nom_pluriel = CharField(_('nom (au pluriel)'), max_length=430, blank=True,
        help_text=PLURAL_MSG)
    referent = BooleanField(
        _('référent'), default=False, db_index=True,
        help_text=_(
            'L’affichage d’une œuvre remonte jusqu’à l’œuvre référente '
            'la contenant. Exemple : le rendu d’une scène sera du type '
            '« Le jeune Henri, acte 2, scène 3 » car on remonte jusqu’à '
            'l’œuvre référente, ici choisie comme étant celle de nature '
            '« opéra »'))
    parents = ManyToManyField('GenreDOeuvre', related_name='enfants',
        blank=True, null=True)

    class Meta(object):
        verbose_name = ungettext_lazy('genre d’œuvre', 'genres d’œuvre', 1)
        verbose_name_plural = ungettext_lazy('genre d’œuvre',
                                             'genres d’œuvre', 2)
        ordering = ('slug',)
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        relations = ('oeuvres',)
        if all_relations:
            relations += ('enfants',)
        return relations

    def html(self, tags=True, caps=False, pluriel=False):
        nom = self.pluriel() if pluriel else self.nom
        if caps:
            nom = capfirst(nom)
        return hlp(nom, ugettext('genre'), tags)

    def pluriel(self):
        return calc_pluriel(self)

    def __str__(self):
        return strip_tags(self.html(False))

    @staticmethod
    def autocomplete_search_fields():
        return 'nom__istartswith', 'nom_pluriel__istartswith'


class TypeDeCaracteristiqueDOeuvre(TypeDeCaracteristique):
    class Meta(object):
        verbose_name = ungettext_lazy('type de caractéristique d’œuvre',
                                      'types de caracteristique d’œuvre', 1)
        verbose_name_plural = ungettext_lazy(
            'type de caractéristique d’œuvre',
            'types de caracteristique d’œuvre',
            2)
        ordering = ('classement',)
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('typedecaracteristique_ptr',)


class CaracteristiqueDOeuvre(Caracteristique):
    class Meta(object):
        verbose_name = ungettext_lazy('caractéristique d’œuvre',
                                      'caractéristiques d’œuvre', 1)
        verbose_name_plural = ungettext_lazy('caractéristique d’œuvre',
                                             'caractéristiques d’œuvre', 2)
        ordering = ('type', 'classement', 'valeur')
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('caracteristique_ptr', 'oeuvres',)


class PartieQuerySet(PolymorphicMPTTQuerySet, PublishedQuerySet,
                     CommonTreeQuerySet):
    pass


class PartieManager(CommonTreeManager, PolymorphicMPTTModelManager,
                    PublishedManager):
    queryset_class = PartieQuerySet


@python_2_unicode_compatible
class Partie(PolymorphicMPTTModel, AutoriteModel, UniqueSlugModel):
    """
    Partie de l’œuvre, c’est-à-dire typiquement un rôle ou un instrument pour
    une œuvre musicale.
    Pour plus de compréhensibilité, on affiche « rôle ou instrument » au lieu
    de « partie ».
    """

    nom = CharField(_('nom'), max_length=200, db_index=True,
                    help_text=_('Le nom d’une partie de la partition, '
                                'instrumentale ou vocale.'))
    nom_pluriel = CharField(_('nom (au pluriel)'), max_length=230, blank=True,
        help_text=PLURAL_MSG)
    # TODO: Changer le verbose_name en un genre de "types de voix"
    # pour les rôles, mais en plus générique (ou un help_text).
    professions = ManyToManyField('Profession', related_name='parties',
        verbose_name=_('professions'), db_index=True, blank=True, null=True,
        help_text=_('La ou les profession(s) capable(s) '
                    'de jouer ce rôle ou cet instrument.'))
    parent = PolymorphicTreeForeignKey(
        'self', related_name='enfant', blank=True, null=True, db_index=True,
        verbose_name=_('rôle ou instrument parent')
    )
    classement = SmallIntegerField(_('classement'), default=1, db_index=True)

    objects = PartieManager()

    weak_unique_constraint = ('nom', 'parent')

    class Meta(object):
        verbose_name = ungettext_lazy('rôle ou instrument',
                                      'rôles et instruments', 1)
        verbose_name_plural = ungettext_lazy('rôle ou instrument',
                                             'rôles et instruments', 2)
        ordering = ('classement', 'nom',)
        app_label = 'libretto'
        permissions = (('can_change_status', _('Peut changer l’état')),)

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('get_real_instance', 'pupitres',)

    class MPTTMeta(object):
        order_insertion_by = ['classement', 'nom']

    def _get_unique_checks(self, exclude=None):
        # Ajoute une contrainte faible, inexistante dans la base de données,
        # mais testée par l'administration Django.
        # On ne peut pas appliquer cette contrainte à la base de données car
        # les données sont réparties entre plusieurs tables à cause du
        # polymorphisme.
        # WARNING: cette contrainte n'est pas testée par l'ORM !  Attention aux
        # doublons lors de scripts !
        unique_checks, date_checks = super(
            Partie, self)._get_unique_checks(exclude=exclude)
        unique_checks.append((self.__class__, self.weak_unique_constraint))
        return unique_checks, date_checks

    def interpretes(self):
        return self.pupitres.elements_de_distribution().individus()

    def interpretes_html(self):
        return str_list(i.html() for i in self.interpretes())
    interpretes_html.short_description = _('interprètes')

    def evenements(self):
        return self.pupitres.elements_de_distribution().evenements()

    def repertoire(self):
        return self.pupitres.oeuvres()

    def pluriel(self):
        return calc_pluriel(self)

    @permalink
    def get_absolute_url(self):
        return b'partie_detail', (self.slug,)

    @permalink
    def permalien(self):
        return b'partie_permanent_detail', (self.pk,)

    def link(self):
        return self.html()

    def html(self, pluriel=False, tags=True):
        url = '' if not tags else self.get_absolute_url()
        if pluriel:
            out = self.pluriel()
        else:
            out = self.nom
        return href(url, out, tags=tags)

    def __str__(self):
        return self.html(tags=False)

    @staticmethod
    def autocomplete_search_fields():
        return ('nom__icontains', 'nom_pluriel__icontains',
                'professions__nom__icontains',
                'professions__nom_pluriel__icontains',)


class Role(Partie):
    # TODO: Ajouter automatiquement le rôle à l’effectif.
    oeuvre = ForeignKey('Oeuvre', verbose_name=_('œuvre'), blank=True,
                        null=True, related_name='roles')

    weak_unique_constraint = ('nom', 'oeuvre',)

    class Meta(object):
        verbose_name = ungettext_lazy('rôle', 'rôles', 1)
        verbose_name_plural = ungettext_lazy('rôle', 'rôles', 2)
        app_label = 'libretto'

    def related_label(self):
        txt = super(Role, self).related_label()
        if self.oeuvre is not None:
            txt += ' (' + smart_text(self.oeuvre) + ')'
        return txt

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('partie_ptr',)


class Instrument(Partie):
    class Meta(object):
        verbose_name = ungettext_lazy('instrument', 'instruments', 1)
        verbose_name_plural = ungettext_lazy('instrument', 'instruments', 2)
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('partie_ptr',)


class PupitreQuerySet(CommonQuerySet):
    def elements_de_distribution(self):
        return get_model(
            'libretto',
            'ElementDeDistribution'
        ).objects.filter(pupitre__in=self).distinct()

    def oeuvres(self):
        return (get_model('libretto', 'Oeuvre').objects
                .filter(pupitres__in=self).distinct()
                .order_by(*Oeuvre._meta.ordering))


class PupitreManager(CommonManager):
    queryset_class = PupitreQuerySet

    def elements_de_distribution(self):
        return self.all().elements_de_distribution()

    def oeuvres(self):
        return self.all().oeuvres()


# TODO: une fois les quantités déplacées en inline, ce modèle ne doit plus être
# registered dans l'admin.
@python_2_unicode_compatible
class Pupitre(CommonModel):
    partie = ForeignKey(
        'Partie', related_name='pupitres', verbose_name=_('partie'),
        db_index=True, on_delete=PROTECT)
    quantite_min = IntegerField(_('quantité minimale'), default=1,
                                db_index=True)
    quantite_max = IntegerField(_('quantité maximale'), default=1,
                                db_index=True)

    objects = PupitreManager()

    class Meta(object):
        verbose_name = ungettext_lazy('pupitre', 'pupitres', 1)
        verbose_name_plural = ungettext_lazy('pupitre', 'pupitres', 2)
        ordering = ('partie',)
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return ('oeuvres', 'elements_de_distribution')

    def __str__(self):
        out = ''
        partie = self.partie
        mi = self.quantite_min
        ma = self.quantite_max
        if ma > 1:
            partie = partie.pluriel()
        else:
            partie = smart_text(partie)
        mi_str = apnumber(mi)
        ma_str = apnumber(ma)
        if mi != ma:
            d = {'min': mi_str, 'max': ma_str}
            out += ugettext('%(min)s à %(max)s ') % d
        elif mi > 1:
            out += mi_str + ' '
        out += partie
        return out

    def get_absolute_url(self):
        return self.partie.get_absolute_url()

    def html(self, tags=True):
        return href(self.get_absolute_url(), smart_text(self), tags=tags)

    def related_label(self):
        out = smart_text(self)
        if isinstance(self.partie, Role) and self.partie.oeuvre is not None:
            out += ' (' + smart_text(self.partie.oeuvre) + ')'
        return out

    @staticmethod
    def autocomplete_search_fields():
        return ('partie__nom__icontains', 'partie__nom_pluriel__icontains',
                'partie__professions__nom__icontains',
                'partie__professions__nom_pluriel__icontains',)


class TypeDeParenteDOeuvres(TypeDeParente):
    class Meta(object):
        verbose_name = ungettext_lazy('type de parenté d’œuvres',
                                      'types de parentés d’œuvres', 1)
        verbose_name_plural = ungettext_lazy('type de parenté d’œuvres',
                                             'types de parentés d’œuvres', 2)
        ordering = ('classement',)
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        relations = ('typedeparente_ptr',)
        if all_relations:
            relations += ('parentes',)
        return relations


class ParenteDOeuvresManager(CommonManager):
    def meres_en_ordre(self):
        return self.all().order_by(
            'mere__creation_date', 'mere__creation_heure',
            'mere__creation_lieu', 'mere__creation_date_approx',
            'mere__creation_heure_approx', 'mere__creation_lieu_approx')

    def filles_en_ordre(self):
        return self.all().order_by(
            'fille__creation_date', 'fille__creation_heure',
            'fille__creation_lieu', 'fille__creation_date_approx',
            'fille__creation_heure_approx', 'fille__creation_lieu_approx')


@python_2_unicode_compatible
class ParenteDOeuvres(CommonModel):
    type = ForeignKey('TypeDeParenteDOeuvres', related_name='parentes',
                      verbose_name=_('type'), db_index=True, on_delete=PROTECT)
    mere = ForeignKey(
        'Oeuvre', related_name='parentes_filles', verbose_name=_('œuvre mère'),
        db_index=True)
    fille = ForeignKey(
        'Oeuvre', related_name='parentes_meres', verbose_name=_('œuvre fille'),
        db_index=True)

    objects = ParenteDOeuvresManager()

    class Meta(object):
        verbose_name = ungettext_lazy('parenté d’œuvres',
                                      'parentés d’œuvres', 1)
        verbose_name_plural = ungettext_lazy('parenté d’œuvres',
                                             'parentés d’œuvres', 2)
        ordering = ('type',)
        app_label = 'libretto'
        unique_together = ('type', 'mere', 'fille',)

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        if all_relations:
            return ('mere', 'fille',)
        return ()

    def __str__(self):
        return '%s %s %s' % (self.fille, self.type.nom, self.mere)

    def clean(self):
        try:
            type, mere, fille = self.type, self.mere, self.fille
            if mere == fille:
                raise ValidationError(_('Les deux champs de parenté ne '
                                        'peuvent pas être identiques'))
            if ParenteDOeuvres.objects.filter(mere=fille,
                                              fille=mere).exists():
                raise ValidationError(_('Une relation entre ces deux objets '
                                        'existe déjà dans le sens inverse'))
        except (Oeuvre.DoesNotExist, TypeDeParenteDOeuvres.DoesNotExist):
            pass


class AuteurQuerySet(CommonQuerySet):
    def __get_related(self, model):
        qs = model._default_manager.filter(auteurs__id__in=self)
        return qs.distinct().order_by(*model._meta.ordering)

    def individus(self):
        return self.__get_related(Individu)

    def professions(self):
        return self.__get_related(Profession)

    def oeuvres(self):
        return self.__get_related(Oeuvre)

    def sources(self):
        return self.__get_related(Source)

    def html(self, tags=True):
        auteurs = self
        d = OrderedDefaultDict()
        for auteur in auteurs:
            d[auteur.profession].append(auteur.individu)
        return mark_safe(str_list(
            '%s [%s]' % (str_list_w_last(i.html(tags=tags) for i in ins),
                         p.short_html(tags=tags, pluriel=len(ins) > 1))
                for p, ins in d.items()))


class AuteurManager(CommonManager):
    queryset_class = AuteurQuerySet

    def individus(self):
        return self.get_queryset().individus()

    def professions(self):
        return self.get_queryset().professions()

    def oeuvres(self):
        return self.get_queryset().oeuvres()

    def sources(self):
        return self.get_queryset().sources()

    def html(self, tags=True):
        return self.get_queryset().html(tags)


@python_2_unicode_compatible
class Auteur(CommonModel):
    oeuvre = ForeignKey(
        'Oeuvre', null=True, blank=True, on_delete=PROTECT,
        related_name='auteurs', verbose_name=_('œuvre'))
    source = ForeignKey(
        'Source', null=True, blank=True, on_delete=PROTECT,
        related_name='auteurs', verbose_name=_('source'))
    individu = ForeignKey('Individu', related_name='auteurs',
                          verbose_name=_('individu'), db_index=True,
                          on_delete=PROTECT)
    profession = ForeignKey('Profession', related_name='auteurs',
                            verbose_name=_('profession'), db_index=True,
                            on_delete=PROTECT)

    objects = AuteurManager()

    class Meta(object):
        verbose_name = ungettext_lazy('auteur', 'auteurs', 1)
        verbose_name_plural = ungettext_lazy('auteur', 'auteurs', 2)
        ordering = ('profession', 'individu__nom')
        app_label = 'libretto'

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        return (
            'oeuvre', 'source',
        )

    def html(self, tags=True):
        return '%s [%s]' % (self.individu.html(tags=tags),
                            self.profession.short_html(tags=tags))
    html.short_description = _('rendu HTML')
    html.allow_tags = True

    def clean(self):
        try:
            self.individu.professions.add(self.profession)
        except (Individu.DoesNotExist,
                Profession.DoesNotExist):
            pass

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.individu == other.individu \
            and self.profession == other.profession

    def __str__(self):
        return self.html(tags=False)


class OeuvreQuerySet(CommonTreeQuerySet, PublishedQuerySet):
    def html(self, *args, **kwargs):
        return str_list_w_last([o.html(*args, **kwargs) for o in self])


class OeuvreManager(CommonTreeManager, PublishedManager):
    queryset_class = OeuvreQuerySet

    def html(self, *args, **kwargs):
        return self.get_queryset().html(*args, **kwargs)


@python_2_unicode_compatible
class Oeuvre(MPTTModel, AutoriteModel, UniqueSlugModel):
    prefixe_titre = CharField(_('article'), max_length=20, blank=True,
                              db_index=True)
    titre = CharField(_('titre'), max_length=200, blank=True, db_index=True)
    coordination = CharField(_('coordination'), max_length=20, blank=True,
                             db_index=True)
    prefixe_titre_secondaire = CharField(
        _('article'), max_length=20, blank=True, db_index=True)
    titre_secondaire = CharField(_('titre secondaire'), max_length=200,
                                 blank=True, db_index=True)
    genre = ForeignKey('GenreDOeuvre', related_name='oeuvres', blank=True,
        null=True, verbose_name=_('genre'), db_index=True, on_delete=PROTECT)
    coupe = CharField(
        _('coupe'), max_length=100, blank=True,
        validators=[RegexValidator(
            r'^\D+$', _('Vous devez saisir les quantités '
                        'en toutes lettres.'))],
        help_text=_('Exemple : « trois actes » pour un opéra en trois actes.'))
    numero = CharField(
        _('numéro'), max_length=5, blank=True,
        validators=[RegexValidator(
            r'^[\d\w\-]+$', _('Vous ne pouvez saisir que des chiffres, '
                              'lettres non accentuées et tiret, '
                              'le tout sans espace.'))],
        help_text=_(
            'Exemple : « 5 » pour symphonie n° 5, « 7a » pour valse n° 7 a, '
            'ou encore « 3-7 » pour sonates n° 3 à 7. '
            '<strong>Ne pas confondre avec le sous-numéro d’opus.</strong>'))
    opus = CharField(
        _('opus'), max_length=5, blank=True,
        validators=[RegexValidator(
            r'^[\d\w\-/]+$', _('Vous ne pouvez saisir que des chiffres, '
                              'lettres non accentuées, tiret '
                              'et barre oblique, le tout sans espace.'))],
        help_text=_('Exemple : « 12 » pour op. 12, « 27/3 » pour op. 27 n° 3, '
                    '« 8b » pour op. 8 b, ou encore « 12-15 » pour '
                    'op. 12 à 15.'))
    # FIXME: Réduire la longueur maximale des tempi dès qu’un nettoyage y aura
    #        été fait
    tempo = CharField(max_length=92, blank=True)
    NOTES = OrderedDict((
        ('c', 'do'),
        ('d', 'ré'),
        ('e', 'mi'),
        ('f', 'fa'),
        ('g', 'sol'),
        ('a', 'la'),
        ('b', 'si'),
        ('u', 'ut'),  # C’est un do, mais on le déprécie.
    ))
    ALTERATIONS = OrderedDict((
        ('-', 'bémol'),
        ('0', ''),
        ('+', 'dièse'),
    ))
    GAMMES = OrderedDict((
        ('C', 'majeur'),
        ('A', 'mineur'),
        ('0', ''),
        # ('c', 'mode de do'),
        # ('d', 'mode de ré'),
        # ('e', 'mode de mi'),
        # ('f', 'mode de fa'),
        # ('g', 'mode de sol'),
        # ('a', 'mode de la'),
        # ('b', 'mode de si'),
    ))
    TONALITES = [
        (gamme_k + note_k + alter_k, str_list((note_v, alter_v, gamme_v), ' '))
        for gamme_k, gamme_v in GAMMES.items()
        for note_k, note_v in NOTES.items()
        for alter_k, alter_v in ALTERATIONS.items()
    ]
    tonalite = CharField(_('tonalité'), max_length=3, choices=TONALITES,
                         blank=True)
    ict = CharField(
        _('ICT'), max_length=25, blank=True,
        help_text='Indice Catalogue Thématique. Exemple : « RV 42 », '
                  '« K. 299d » ou encore « Hob. XVI:24 ».')
    surnom = CharField(
        _('surnom'), max_length=50, blank=True,
        help_text=_('Exemple : « Jupiter » pour la symphonie n° 41 '
                    'de Mozart.'))
    sujet = CharField(
        _('sujet'), max_length=80, blank=True,
        help_text=_(
            'Exemple : « un thème de Beethoven » pour une variation sur un '
            'thème de Beethoven, « des motifs de '
            '&lt;em&gt;Lucia di Lammermoor&lt;/em&gt; » pour une fantaisie '
            'sur des motifs de <em>Lucia di Lammermoor</em> '
            '(&lt;em&gt; et &lt;/em&gt; sont les balises HTML '
            'pour mettre en emphase).'))
    incipit = CharField(
        _('incipit'), max_length=100, blank=True,
        help_text=_('Exemple : « Belle nuit, ô nuit d’amour » pour le n° 13 '
                    'de l’acte III des <em>Contes d’Hoffmann</em> '
                    'd’Offenbach.'))
    nom_courant = CharField(
        _('nom courant'), max_length=70, blank=True,
        help_text=_('Exemple : « barcarolle » pour le n° 13 de l’acte III des '
                    '<em>Contes d’Hoffmann</em> d’Offenbach.'))
    caracteristiques = ManyToManyField(
        'CaracteristiqueDOeuvre', blank=True, null=True, db_index=True,
        verbose_name=_('autres caractéristiques'), related_name='oeuvres')
    creation = AncrageSpatioTemporel(short_description=_('création'))
    pupitres = ManyToManyField('Pupitre', related_name='oeuvres', blank=True,
        null=True, verbose_name=_('effectif'), db_index=True)
    extrait_de = TreeForeignKey(
        'self', null=True, blank=True,
        related_name='enfants', verbose_name=_('extrait de'))
    ACTE = 1
    TABLEAU = 2
    SCENE = 3
    MORCEAU = 4
    PARTIE = 5
    LIVRE = 6
    ALBUM = 7
    VOLUME = 8
    CAHIER = 9
    ORDRE = 10
    MOUVEMENT = 11
    TYPES_EXTRAIT_ROMAINS = (ACTE, LIVRE, ORDRE)
    TYPES_EXTRAIT_CACHES = (MORCEAU, MOUVEMENT)
    TYPES_EXTRAIT = (
        (ACTE,      _('acte')),
        (TABLEAU,   _('tableau')),
        (SCENE,     _('scène')),
        (MORCEAU,   _('morceau chanté')),
        (PARTIE,    _('partie d’oratorio')),
        (LIVRE,     _('livre')),
        (ALBUM,     _('album')),
        (VOLUME,    _('volume')),
        (CAHIER,    _('cahier')),
        (ORDRE,     _('ordre')),
        (MOUVEMENT, _('mouvement')),
    )
    type_extrait = PositiveSmallIntegerField(
        _('type d’extrait'), choices=TYPES_EXTRAIT, blank=True, null=True)
    NUMERO_EXTRAIT_PATTERN = r'^([1-9]\d*)([^\d\.\-]*)$'
    NUMERO_EXTRAIT_RE = re.compile(NUMERO_EXTRAIT_PATTERN)
    numero_extrait = CharField(
        _('numéro d’extrait'), max_length=5, blank=True,
        help_text=_(
            'Le numéro de l’extrait au sein de l’œuvre, par exemple « 3 » '
            'pour le 3<sup>e</sup> mouvement d’un concerto, « 4 » pour '
            'l’acte IV d’un opéra, ou encore « 12b ».'),
        validators=[RegexValidator(
            NUMERO_EXTRAIT_PATTERN,
            _('Vous devez saisir un nombre en chiffres arabes '
              'éventellement suivi de lettres.'))])
    filles = ManyToManyField('self', through='ParenteDOeuvres',
                             related_name='meres', symmetrical=False,
                             blank=True, null=True)
    lilypond = TextField(blank=True, verbose_name='LilyPond')
    description = HTMLField(blank=True)

    objects = OeuvreManager()

    class Meta(object):
        verbose_name = ungettext_lazy('œuvre', 'œuvres', 1)
        verbose_name_plural = ungettext_lazy('œuvre', 'œuvres', 2)
        ordering = ('type_extrait', 'numero_extrait', 'titre',
                    'genre', 'numero', 'coupe',
                    'tempo', 'tonalite',
                    'surnom', 'nom_courant', 'incipit',
                    'opus', 'ict')
        app_label = 'libretto'
        permissions = (('can_change_status', _('Peut changer l’état')),)

    @staticmethod
    def invalidated_relations_when_saved(all_relations=False):
        relations = ('enfants', 'elements_de_programme',)
        if all_relations:
            relations += ('dossiers', 'filles',)
        return relations

    class MPTTMeta(object):
        parent_attr = 'extrait_de'

    @permalink
    def get_absolute_url(self):
        return b'oeuvre_detail', [self.slug]

    @permalink
    def permalien(self):
        return b'oeuvre_permanent_detail', [self.pk]

    def link(self):
        return self.html(tags=True, auteurs=False, titre=True, descr=True,
                         ancestors=True)
    link.short_description = _('lien')
    link.allow_tags = True

    def get_extrait(self):
        if not self.type_extrait:
            return ''
        digits, suffix = self.NUMERO_EXTRAIT_RE.match(
            self.numero_extrait).groups()
        if self.type_extrait in self.TYPES_EXTRAIT_ROMAINS:
            digits = to_roman(int(digits))
        out = digits + suffix
        if self.type_extrait == self.MORCEAU:
            out = _('№ ') + out + ' '
        elif self.type_extrait == self.MOUVEMENT:
            out += '. '
        else:
            out = self.get_type_extrait_display() + ' ' + out
        return out

    def get_caracteristiques(self, tags=False):
        caracteristiques = []
        if self.coupe:
            caracteristiques.append(hlp(ugettext('en %s') % self.coupe,
                                        ugettext('coupe'), tags))
        if self.numero:
            caracteristiques.append(ugettext('n° %s') % self.numero)
        if self.opus:
            caracteristiques.append(hlp(ugettext('op. %s') % self.opus,
                                        ugettext('opus'), tags))
        if self.tonalite:
            gamme, note, alteration = self.tonalite
            if gamme == 'C':
                gamme = 'majeur'
            elif gamme == 'A':
                gamme = 'mineur'
            elif gamme == '0':
                gamme = ''
            note = self.NOTES[note]
            alteration = self.ALTERATIONS[alteration]
            tonalite = ugettext('en %s') % str_list(
                (em(note, tags), alteration, gamme), ' ')
            caracteristiques.append(hlp(tonalite, ugettext('tonalité'), tags))
        if self.ict:
            caracteristiques.append(
                hlp(self.ict, ugettext('Indice Catalogue Thématique'), tags))
        if self.surnom:
            caracteristiques.append(
                hlp(em(self.surnom, tags), ugettext('surnom'), tags))
        if self.incipit:
            caracteristiques.append(hlp(ugettext('« %s »') % self.incipit,
                                        ugettext('incipit'), tags))
        if self.nom_courant:
            caracteristiques.append(hlp(self.nom_courant,
                                        ugettext('nom courant'), tags))
        if self.sujet:
            caracteristiques.append(
                hlp(ugettext('sur %s') % self.sujet, ugettext('sujet'), tags))
        if self.pk:
            caracteristiques.extend(self.caracteristiques.html_list(tags=tags))
        return caracteristiques

    def caracteristiques_html(self, tags=True):
        return str_list(self.get_caracteristiques(tags=tags))
    caracteristiques_html.allow_tags = True
    caracteristiques_html.short_description = _('caractéristiques')

    def calc_pupitres(self, prefix=True, tags=False):
        if not self.pk:
            return ''
        pupitres = self.pupitres.select_related('partie')
        if not pupitres:
            return ''
        out = ugettext('pour ') if prefix else ''
        out += str_list_w_last(p.html(tags=tags) for p in pupitres)
        return out

    def pupitres_html(self, prefix=False, tags=True):
        return self.calc_pupitres(prefix=prefix, tags=tags)

    @model_method_cached()
    def auteurs_html(self, tags=True):
        return self.auteurs.html(tags)
    auteurs_html.short_description = _('auteurs')
    auteurs_html.allow_tags = True
    auteurs_html.admin_order_field = 'auteurs__individu__nom'

    def parentes_in_order(self, relation):
        return getattr(self, relation).order_by(
            'creation_date', 'creation_heure', 'creation_lieu',
            'creation_date_approx', 'creation_heure_approx',
            'creation_lieu_approx')

    def meres_in_order(self):
        return self.parentes_in_order('meres')

    def filles_in_order(self):
        return self.parentes_in_order('filles')

    @property
    def evenements(self):
        return get_model('libretto', 'Evenement').objects.filter(
            programme__oeuvre__in=self.get_descendants(include_self=True))

    def oeuvres_associees(self):
        # TODO: Limiter à ce que l’utilisateur peut voir.
        return (
            Oeuvre.objects.exclude(
                pk__in=self.get_descendants(include_self=True))
            .filter(elements_de_programme__evenement__programme__oeuvre=self)
            .annotate(n=Count('elements_de_programme__evenement'))
            .order_by('-n', *self._meta.ordering)).distinct()

    def _link_with_number(self):
        return ugettext('œuvre jouée %s fois avec : %s') % (
            self.n, self.link())

    def calc_referent_ancestors(self, tags=False, links=False):
        if not self.pk or self.extrait_de is None or \
                (self.genre and self.genre.referent):
            return ''
        return self.extrait_de.titre_html(tags=tags, links=links)

    def titre_complet(self):
        l = (self.prefixe_titre, self.titre, self.coordination,
             self.prefixe_titre_secondaire, self.titre_secondaire)
        return str_list(l, infix='')

    @model_method_cached()
    def html(self, tags=True, auteurs=True, titre=True,
             descr=True, genre_caps=False, ancestors=True,
             ancestors_links=False, links=True):
        # FIXME: Nettoyer cette horreur
        out = ''
        titre_complet = self.titre_complet()
        extrait = self.get_extrait()
        genre = self.genre
        tempo = self.tempo
        caracteristiques = self.get_caracteristiques(tags=tags)
        url = None if not tags else self.get_absolute_url()
        if auteurs:
            auts = self.auteurs_html(tags)
            if auts:
                out += auts + ', '
        if titre:
            if ancestors:
                pars = self.calc_referent_ancestors(
                    tags=tags, links=ancestors_links)
                if pars:
                    out += pars + ', '
            if titre_complet:
                out += href(url, cite(titre_complet, tags=tags), tags & links)
                if descr and genre:
                    out += ', '
        if genre or extrait or tempo:
            if not titre_complet:
                titre_complet = extrait
                if genre is not None:
                    titre_complet += self.genre.html(tags, caps=True)
                if tempo:
                    titre_complet += ' ' + tempo
                pupitres = self.calc_pupitres()
                if pupitres:
                    titre_complet += ' ' + pupitres
                if caracteristiques:
                    titre_complet += ' ' + caracteristiques.pop(0)
                if titre:
                    out += href(url, titre_complet, tags=tags & links)
                    if descr and caracteristiques:
                        out += ','
            elif descr and genre is not None:
                out += genre.html(tags, caps=genre_caps)
        if descr and caracteristiques:
            if out:
                # TODO: BUG : le validateur HTML supprime l'espace qu'on ajoute
                #       ci-dessous si on ne le met pas en syntaxe HTML
                out += '&#32;' if tags else ' '
            out += str_list(caracteristiques)
        return mark_safe(out)
    html.short_description = _('rendu HTML')
    html.allow_tags = True

    def short_html(self, tags=True, links=False):
        return self.html(tags=tags, auteurs=False, titre=True, descr=False,
                         ancestors=False, links=links)

    def titre_html(self, tags=True, links=True):
        return self.html(tags, auteurs=False, titre=True, descr=False,
                         ancestors=True, ancestors_links=True, links=links)
    titre_html.short_description = _('titre')

    def titre_descr(self, tags=False):
        return self.html(tags=tags, auteurs=False, titre=True, descr=True,
                         ancestors=True)

    def titre_descr_html(self):
        return self.titre_descr(tags=True)

    def description_html(self, tags=True):
        return self.html(tags, auteurs=False, titre=False, descr=True,
                         genre_caps=True)

    def handle_whitespaces(self):
        match = re.match(r'^,\s*(.+)$', self.coordination)
        v = self.coordination if match is None else match.group(1)
        if v:
            self.coordination = ', %s' % v
        for attr in ('prefixe_titre', 'prefixe_titre_secondaire',
                     'coordination'):
            v = getattr(self, attr)
            if v and v[-1] not in (' ', "'", '’'):
                setattr(self, attr, v + ' ')

    def related_label(self):
        txt = smart_text(self)
        auteurs = self.auteurs.html(tags=False)
        if auteurs:
            txt += ' (' + auteurs + ')'
        return txt

    def __str__(self):
        return strip_tags(self.titre_html(False))  # strip_tags car on autorise
                         # les rédacteurs à mettre des tags dans les CharFields

    _str = __str__
    _str.short_description = _('œuvre')

    @staticmethod
    def autocomplete_search_fields(add_icontains=True):
        lookups = (
            'auteurs__individu__nom',
            'prefixe_titre', 'titre',
            'prefixe_titre_secondaire', 'titre_secondaire',
            'genre__nom', 'numero', 'coupe',
            'tempo', 'sujet',
            'surnom', 'nom_courant', 'incipit',
            'opus', 'ict',
            'caracteristiques__valeur',
            'pupitres__partie__nom')
        if add_icontains:
            return [lookup + '__icontains' for lookup in lookups]
        return lookups
