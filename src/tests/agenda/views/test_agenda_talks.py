import datetime as dt

import pytest
from django.utils import formats
from django.utils.timezone import now
from django_scopes import scope


@pytest.mark.django_db
@pytest.mark.usefixtures("slot", "other_slot")
def test_can_see_talk_list(client, django_assert_num_queries, event):
    with django_assert_num_queries(6):
        response = client.get(event.urls.talks, follow=True, HTTP_ACCEPT="text/html")
    assert response.status_code == 200
    assert "<pretalx-schedule" in response.text


@pytest.mark.django_db
@pytest.mark.usefixtures("other_slot")
def test_can_see_talk(client, django_assert_num_queries, event, slot):
    with django_assert_num_queries(21):
        response = client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 200
    content = response.text
    with scope(event=event):
        assert content.count(slot.submission.title) >= 2  # meta+h1
        assert slot.submission.abstract in content
        assert slot.submission.description in content
        assert formats.date_format(slot.local_start, "H:i") in content
        assert formats.date_format(slot.local_end, "H:i") in content
        assert str(slot.room.name) in content
        assert "fa-edit" not in content  # edit btn
        assert "fa-video" not in content  # do not record
        assert "<iframe" not in content  # test plugin not active


@pytest.mark.django_db
def test_can_see_talk_with_iframe(client, django_assert_num_queries, event, slot):
    event.plugins = "tests"
    event.save()
    with django_assert_num_queries(21):
        response = client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 200
    content = response.text
    assert "<iframe" in content


@pytest.mark.django_db
@pytest.mark.usefixtures("other_slot")
def test_can_see_social_card(client, slot):
    response = client.get(slot.submission.urls.social_image, follow=True)
    assert response.status_code == 404  # no image


@pytest.mark.django_db
def test_cannot_see_new_talk(client, django_assert_num_queries, event, unreleased_slot):
    slot = unreleased_slot
    with django_assert_num_queries(11):
        response = client.get(slot.submission.urls.public)
    assert response.status_code == 404
    with scope(event=event):
        assert event.schedules.count() == 1


@pytest.mark.django_db
def test_orga_can_see_new_talk(
    orga_client, django_assert_num_queries, event, unreleased_slot
):
    slot = unreleased_slot
    with django_assert_num_queries(24):
        response = orga_client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 200
    content = response.text
    with scope(event=event):
        assert event.schedules.count() == 1
        assert content.count(slot.submission.title) >= 2  # meta+h1
        assert slot.submission.abstract in content
        assert slot.submission.description in content
        assert formats.date_format(slot.local_start, "H:i") in content
        assert formats.date_format(slot.local_end, "H:i") in content
        assert str(slot.room.name) in content
        assert "fa-edit" not in content  # edit btn
        assert "fa-video" not in content  # do not record


@pytest.mark.django_db
def test_can_see_talk_edit_btn(
    orga_client, django_assert_num_queries, orga_user, event, slot
):
    with scope(event=event):
        slot.submission.speakers.add(orga_user)
    with django_assert_num_queries(25):
        response = orga_client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 200
    content = response.text
    assert "fa-edit" in content  # edit btn
    assert "fa-video" not in content


@pytest.mark.django_db
def test_can_see_talk_do_not_record(client, event, django_assert_num_queries, slot):
    with scope(event=event):
        slot.submission.do_not_record = True
        slot.submission.save()
    with django_assert_num_queries(20):
        response = client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 200
    content = response.text
    assert "fa-edit" not in content  # edit btn
    assert "fa-video" in content


@pytest.mark.django_db
def test_can_see_talk_does_accept_feedback(
    client, django_assert_num_queries, event, slot
):
    with scope(event=event):
        slot.start = now() - dt.timedelta(days=1)
        slot.end = slot.start + dt.timedelta(hours=1)
        slot.save()
    with django_assert_num_queries(21):
        response = client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 200
    content = response.text
    assert "fa-edit" not in content  # edit btn
    assert "fa-comments" in content
    assert "fa-video" not in content


@pytest.mark.django_db
def test_cannot_see_nonpublic_talk(client, django_assert_num_queries, event, slot):
    event.is_public = False
    event.save()
    with django_assert_num_queries(10):
        response = client.get(slot.submission.urls.public, follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
def test_cannot_see_other_events_talk(
    client, django_assert_num_queries, event, slot, other_event
):
    with django_assert_num_queries(8):
        response = client.get(
            slot.submission.urls.public.replace(event.slug, other_event.slug),
            follow=True,
        )
    assert response.status_code == 404


@pytest.mark.django_db
def test_event_talk_visiblity_submitted(client, django_assert_num_queries, submission):
    with django_assert_num_queries(9):
        response = client.get(submission.urls.public, follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("slot")
def test_event_talk_visiblity_accepted(
    client, django_assert_num_queries, accepted_submission
):
    with django_assert_num_queries(10):
        response = client.get(accepted_submission.urls.public, follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("slot")
def test_event_talk_visiblity_confirmed(
    client, django_assert_num_queries, confirmed_submission
):
    with django_assert_num_queries(19):
        response = client.get(confirmed_submission.urls.public, follow=True)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("slot")
def test_event_talk_visiblity_canceled(
    client, django_assert_num_queries, canceled_submission
):
    with django_assert_num_queries(10):
        response = client.get(canceled_submission.urls.public, follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("slot")
def test_event_talk_visiblity_withdrawn(
    client, django_assert_num_queries, withdrawn_submission
):
    with django_assert_num_queries(10):
        response = client.get(withdrawn_submission.urls.public, follow=True)
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.usefixtures("slot", "other_slot")
def test_talk_speaker_other_submissions(
    client, django_assert_num_queries, event, speaker, other_submission
):
    with scope(event=event):
        other_submission.speakers.add(speaker)
    with django_assert_num_queries(19):
        response = client.get(other_submission.urls.public, follow=True)

    assert response.status_code == 200
    assert response.context["speakers"]
    assert len(response.context["speakers"]) == 2, response.context["speakers"]
    speaker_response = [
        s for s in response.context["speakers"] if s.name == speaker.name
    ][0]
    other_response = [
        s for s in response.context["speakers"] if s.name != speaker.name
    ][0]
    assert len(speaker_response.other_submissions) == 1
    assert len(other_response.other_submissions) == 0
    with scope(event=event):
        assert (
            speaker_response.other_submissions[0].title
            == speaker.submissions.first().title
        )


@pytest.mark.django_db
@pytest.mark.usefixtures("other_slot")
def test_talk_speaker_other_submissions_only_if_visible(
    client,
    django_assert_num_queries,
    event,
    speaker,
    slot,
    other_submission,
):
    with scope(event=event):
        other_submission.speakers.add(speaker)
        slot.submission.accept(force=True)
        slot.submission.save()
        event.wip_schedule.freeze("testversion 2")
        other_submission.slots.all().update(is_visible=True)
        slot.submission.slots.filter(schedule=event.current_schedule).update(
            is_visible=False
        )

    with django_assert_num_queries(19):
        response = client.get(other_submission.urls.public, follow=True)

    assert response.status_code == 200
    assert response.context["speakers"]
    assert len(response.context["speakers"]) == 2, response.context["speakers"]
    speaker_response = [
        s for s in response.context["speakers"] if s.name == speaker.name
    ][0]
    other_response = [
        s for s in response.context["speakers"] if s.name != speaker.name
    ][0]
    assert len(speaker_response.other_submissions) == 0
    assert len(other_response.other_submissions) == 0


@pytest.mark.django_db
def test_talk_review_page(client, django_assert_num_queries, submission):
    with django_assert_num_queries(14):
        response = client.get(submission.urls.review, follow=True)
    assert response.status_code == 200
    assert submission.title in response.text
