from django import forms
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from pretalx.common.text.phrases import phrases
from pretalx.orga.forms.export import ExportForm
from pretalx.person.models import User
from pretalx.submission.models import SubmissionStates


class SpeakerExportForm(ExportForm):
    target = forms.ChoiceField(
        required=True,
        label=_("Target group"),
        choices=(
            ("all", phrases.base.all_choices),
            ("accepted", _("Just speakers with accepted and confirmed proposals")),
        ),
        widget=forms.RadioSelect,
        initial="all",
    )

    class Meta:
        model = User
        model_fields = ["name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["submission_ids"] = forms.BooleanField(
            required=False,
            label=_("Proposal IDs"),
            help_text=phrases.orga.proposal_id_help_text,
        )
        self.fields["submission_titles"] = forms.BooleanField(
            required=False,
            label=_("Proposal titles"),
        )
        self.fields["biography"] = forms.BooleanField(
            required=False,
            label=_("Biography"),
        )
        self.fields["avatar"] = forms.BooleanField(
            required=False,
            label=_("Picture"),
            help_text=_("The link to the speaker’s profile picture"),
        )

    @cached_property
    def questions(self):
        return self.event.questions.filter(
            target="speaker", active=True
        ).prefetch_related("answers", "answers__person", "options")

    @cached_property
    def filename(self):
        return f"{self.event.slug}_speakers"

    @cached_property
    def export_field_names(self):
        return self.Meta.model_fields + [
            "biography",
            "avatar",
            "submission_ids",
            "submission_titles",
        ]

    def get_queryset(self):
        target = self.cleaned_data.get("target")
        queryset = self.event.submitters
        if target != "all":
            queryset = queryset.filter(
                submissions__in=self.event.submissions.filter(
                    state__in=[SubmissionStates.ACCEPTED, SubmissionStates.CONFIRMED]
                )
            ).distinct()
        return queryset.prefetch_related("profiles", "profiles__event").order_by("code")

    def _get_avatar_value(self, obj):
        return obj.get_avatar_url(event=self.event)

    def _get_biography_value(self, obj):
        return obj._profile.biography

    def _get_submission_ids_value(self, obj):
        return list(
            obj.submissions.filter(event=self.event).values_list("code", flat=True)
        )

    def _get_submission_titles_value(self, obj):
        return list(
            obj.submissions.filter(event=self.event).values_list("title", flat=True)
        )

    def _prepare_object_data(self, obj):
        obj._profile = obj.event_profile(self.event)
        return obj

    def get_answer(self, question, obj):
        return question.answers.filter(person=obj).first()
