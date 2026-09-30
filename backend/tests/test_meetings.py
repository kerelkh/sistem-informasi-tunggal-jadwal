from fastapi.testclient import TestClient

MEETING = {
	"title": "Rakor Anggaran",
	"timezone": "Asia/Jakarta",
	"scheduled_start": "2026-10-01T09:00+07:00",
	"scheduled_end": "2026-10-01T11:00+07:00",
}


def create(client: TestClient, headers, **overrides):
	res = client.post("/api/v1/meetings", json={**MEETING, **overrides}, headers=headers)
	assert res.status_code == 201, res.text
	return res.json()


def notifications(client: TestClient, headers):
	return client.get("/api/v1/notifications", headers=headers).json()


def test_organizer_is_accepted_participant(client: TestClient, make_user):
	_, ani = make_user("Ani")
	m = create(client, ani)
	assert m["me"]["role"] == "organizer"
	assert m["me"]["status"] == "accepted"
	assert m["participants"][0]["role"] == "organizer"


def test_invite_accept_flow(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	m = create(client, ani, invitee_ids=[budi_id])

	# Budi is notified and sees a pending meeting
	[n] = notifications(client, budi)
	assert n["type"] == "meeting_invitation"
	assert n["link"] == f"/dashboard/meetings/{m['id']}"
	assert client.get("/api/v1/meetings/meta/pending-count", headers=budi).json() == {"count": 1}
	[item] = client.get("/api/v1/meetings", headers=budi).json()
	assert item["me"] == {"role": "invitee", "status": "pending", "has_takehome_pay": False, "takehome_pay_paid": False}

	# Accept → organizer notified, meeting counts
	res = client.post(f"/api/v1/meetings/{m['id']}/respond", json={"action": "accept"}, headers=budi)
	assert res.status_code == 200
	assert res.json()["me"]["status"] == "accepted"
	assert notifications(client, ani)[0]["type"] == "invitation_accepted"

	# Invitee can't edit the meeting itself
	assert client.put(f"/api/v1/meetings/{m['id']}", json={"title": "x"}, headers=budi).status_code == 403

	# Cancel attendance after accepting, with a reason
	res = client.post(
		f"/api/v1/meetings/{m['id']}/respond", json={"action": "cancel", "note": "Dinas luar"}, headers=budi
	)
	assert res.json()["me"]["status"] == "cancelled"
	n = notifications(client, ani)[0]
	assert n["type"] == "invitation_cancelled" and n["body"] == "Dinas luar"


def test_decline_then_reinvite(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	m = create(client, ani, invitee_ids=[budi_id])
	client.post(f"/api/v1/meetings/{m['id']}/respond", json={"action": "decline"}, headers=budi)
	# Can't accept once declined...
	res = client.post(f"/api/v1/meetings/{m['id']}/respond", json={"action": "accept"}, headers=budi)
	assert res.status_code == 400
	# ...until invited again
	res = client.post(f"/api/v1/meetings/{m['id']}/participants", json={"user_ids": [budi_id]}, headers=ani)
	assert res.status_code == 200
	budi_row = next(p for p in res.json()["participants"] if p["user"]["id"] == budi_id)
	assert budi_row["status"] == "pending"


def test_cannot_invite_busy_user(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	create(client, budi, title="Budi's own formal meeting", scheduled_start="2026-10-01T10:00+07:00", scheduled_end="2026-10-01T12:00+07:00")

	res = client.post("/api/v1/meetings", json={**MEETING, "invitee_ids": [budi_id]}, headers=ani)
	assert res.status_code == 409
	assert "Budi" in res.json()["detail"]
	# Nothing half-created
	assert client.get("/api/v1/meetings", headers=ani).json() == []


def test_informal_and_pending_do_not_block(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	cici_id, cici = make_user("Cici")
	create(client, budi, title="Coffee", is_formal=False)
	create(client, cici, invitee_ids=[budi_id])  # Budi hasn't answered yet

	res = client.get(
		"/api/v1/availability",
		params={"start": "2026-10-01T09:30+07:00", "end": "2026-10-01T10:00+07:00", "user_ids": [budi_id]},
		headers=ani,
	).json()
	[budi_av] = res["users"]
	assert budi_av["available"] is True
	assert {(b["title"], b["blocking"], b["tentative"]) for b in budi_av["busy"]} == {
		("Coffee", False, False),
		("Rakor Anggaran", False, True),
	}
	create(client, ani, invitee_ids=[budi_id])


def test_availability_rules(client: TestClient, make_user, unit_id):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	create(client, budi)  # 09:00–11:00
	create(client, budi, title="No end", scheduled_start="2026-10-02T14:00+07:00", scheduled_end=None)

	def available(start, end=None):
		params = {"start": start, "unit_id": unit_id, "q": "budi", "tz": "Asia/Jakarta"}
		if end:
			params["end"] = end
		[u] = client.get("/api/v1/availability", params=params, headers=ani).json()["users"]
		return u["available"]

	assert available("2026-10-01T11:00+07:00", "2026-10-01T12:00+07:00")  # half-open: starts as it ends
	assert not available("2026-10-01T10:59+07:00", "2026-10-01T12:00+07:00")
	assert not available("2026-10-01T08:00+07:00")  # blank end → rest of the day
	assert not available("2026-10-02T20:00+07:00", "2026-10-02T21:00+07:00")  # no end → runs all day
	assert available("2026-10-03T08:00+07:00")


def test_cancelled_meeting_frees_slot_and_notifies(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	m = create(client, ani, invitee_ids=[budi_id])
	client.post(f"/api/v1/meetings/{m['id']}/respond", json={"action": "accept"}, headers=budi)

	res = client.post(f"/api/v1/meetings/{m['id']}/cancel", headers=ani)
	assert res.json()["status"] == "cancelled"
	assert notifications(client, budi)[0]["type"] == "meeting_cancelled"

	[u] = client.get(
		"/api/v1/availability", params={"start": "2026-10-01T09:00+07:00", "user_ids": [budi_id]}, headers=ani
	).json()["users"]
	assert u["available"] and u["busy"] == []


def test_reschedule_notifies_invitees(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	m = create(client, ani, invitee_ids=[budi_id])
	client.put(f"/api/v1/meetings/{m['id']}", json={"notes": {"type": "doc"}}, headers=ani)
	assert len(notifications(client, budi)) == 1  # notes aren't material
	client.put(f"/api/v1/meetings/{m['id']}", json={"scheduled_start": "2026-10-01T13:00+07:00", "scheduled_end": None}, headers=ani)
	n = notifications(client, budi)[0]
	assert n["type"] == "meeting_updated" and n["body"] == "Jadwal baru"
	assert n["event_at"] == "2026-10-01T06:00:00Z"


def test_revoke_and_privacy(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	_, cici = make_user("Cici")
	m = create(client, ani, invitee_ids=[budi_id])
	# Outsiders can't see it
	assert client.get(f"/api/v1/meetings/{m['id']}", headers=cici).status_code == 404

	client.delete(f"/api/v1/meetings/{m['id']}/participants/{budi_id}", headers=ani)
	assert notifications(client, budi)[0]["type"] == "invitation_revoked"
	assert client.get(f"/api/v1/meetings/{m['id']}", headers=budi).status_code == 404


def test_takehome_pay_is_per_person(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	m = create(client, ani, invitee_ids=[budi_id], has_takehome_pay=True)
	assert m["me"]["has_takehome_pay"] is True

	# Not attending yet → no pay to track
	res = client.put(f"/api/v1/meetings/{m['id']}/my-pay", json={"has_takehome_pay": True, "takehome_pay_paid": True}, headers=budi)
	assert res.status_code == 400
	client.post(f"/api/v1/meetings/{m['id']}/respond", json={"action": "accept"}, headers=budi)
	res = client.put(f"/api/v1/meetings/{m['id']}/my-pay", json={"has_takehome_pay": True, "takehome_pay_paid": True}, headers=budi)
	assert res.json()["me"]["takehome_pay_paid"] is True
	# Organizer's own record is untouched
	assert client.get(f"/api/v1/meetings/{m['id']}", headers=ani).json()["me"]["takehome_pay_paid"] is False
	# Paid without pay is rejected
	res = client.put(f"/api/v1/meetings/{m['id']}/my-pay", json={"has_takehome_pay": False, "takehome_pay_paid": True}, headers=budi)
	assert res.status_code == 400


def test_delete_meeting(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	m = create(client, ani, invitee_ids=[budi_id])
	assert client.delete(f"/api/v1/meetings/{m['id']}", headers=budi).status_code == 403
	assert client.delete(f"/api/v1/meetings/{m['id']}", headers=ani).status_code == 204
	assert client.get("/api/v1/meetings", headers=budi).json() == []
	assert notifications(client, budi)[0]["link"] is None


def test_notifications_are_private(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	create(client, ani, invitee_ids=[budi_id])
	[n] = notifications(client, budi)
	assert client.patch(f"/api/v1/notifications/{n['id']}/read", headers=ani).status_code == 404
	assert client.get("/api/v1/notifications/unread-count", headers=budi).json() == {"count": 1}


def test_times_are_utc_instants(client: TestClient, make_user):
	_, ani = make_user("Ani")
	# 09:00 in Jakarta is 02:00 UTC — stored and sent as the instant, not the wall clock.
	m = create(client, ani)
	assert m["scheduled_start"] == "2026-10-01T02:00:00Z"
	assert m["timezone"] == "Asia/Jakarta"
	# The same instant written from another zone is the same meeting time. (Informal,
	# so it may share the slot with the first one.)
	m = create(client, ani, scheduled_start="2026-10-01T11:00:00+09:00", scheduled_end=None, is_formal=False)
	assert m["scheduled_start"] == "2026-10-01T02:00:00Z"
	assert m["created_at"].endswith("Z")


def test_time_without_zone_is_refused(client: TestClient, make_user):
	_, ani = make_user("Ani")
	res = client.post("/api/v1/meetings", json={**MEETING, "scheduled_start": "2026-10-01T09:00"}, headers=ani)
	assert res.status_code == 422
	assert res.json()["detail"] == "Waktu mulai: waktu harus menyertakan zona waktu (mis. +07:00 atau Z)."
	res = client.post("/api/v1/meetings", json={**MEETING, "timezone": "Mars/Olympus"}, headers=ani)
	assert res.json()["detail"] == "Zona waktu: zona waktu tidak dikenal."


def test_no_end_runs_to_midnight_where_it_is_held(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	# 20:00 WIB with no end → busy until 00:00 WIB = 17:00 UTC.
	create(client, budi, scheduled_start="2026-10-01T20:00+07:00", scheduled_end=None)

	def available(start, end):
		[u] = client.get(
			"/api/v1/availability", params={"start": start, "end": end, "user_ids": [budi_id]}, headers=ani
		).json()["users"]
		return u["available"]

	assert not available("2026-10-01T16:30:00Z", "2026-10-01T16:45:00Z")
	# Past Jakarta midnight it's over — even though it's still 1 October in UTC.
	assert available("2026-10-01T17:00:00Z", "2026-10-01T18:00:00Z")


def test_availability_window_from_another_zone(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	create(client, budi)  # 09:00–11:00 WIB = 02:00–04:00 UTC
	res = client.get(
		"/api/v1/availability",
		# 11:30–12:00 in Tokyo (UTC+9) = 09:30–10:00 in Jakarta
		params={"start": "2026-10-01T11:30:00+09:00", "end": "2026-10-01T12:00:00+09:00", "user_ids": [budi_id]},
		headers=ani,
	).json()
	assert res["window_start"] == "2026-10-01T02:30:00Z"
	assert res["users"][0]["available"] is False


def test_notifications_carry_the_instant(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	create(client, ani, invitee_ids=[budi_id])
	[n] = notifications(client, budi)
	assert n["body"] is None and n["event_at"] == "2026-10-01T02:00:00Z"


def test_validation_errors_are_indonesian(client: TestClient, make_user):
	_, ani = make_user("Ani")
	res = client.post("/api/v1/meetings", json={"scheduled_start": "2026-10-01T09:00+07:00"}, headers=ani)
	assert res.status_code == 422
	assert res.json() == {"detail": "Judul: wajib diisi."}
	res = client.post("/api/v1/meetings", json={**MEETING, "scheduled_end": "2026-10-01T08:00+07:00"}, headers=ani)
	assert res.json()["detail"] == "Waktu selesai jadwal tidak boleh sebelum waktu mulai jadwal."


def test_formal_meeting_cannot_clash_with_own_schedule(client: TestClient, make_user):
	ani_id, ani = make_user("Ani")
	_, budi = make_user("Budi")
	create(client, ani, title="Rapat milik Ani")

	# Clashes with a formal meeting Ani organises
	res = client.post("/api/v1/meetings", json={**MEETING, "scheduled_start": "2026-10-01T10:00+07:00", "scheduled_end": "2026-10-01T12:00+07:00"}, headers=ani)
	assert res.status_code == 409
	assert "Rapat milik Ani" in res.json()["detail"] and "01/10/2026 09:00–11:00" in res.json()["detail"]
	assert len(client.get("/api/v1/meetings", headers=ani).json()) == 1

	# An informal meeting may share the slot; back-to-back is fine
	create(client, ani, is_formal=False)
	create(client, ani, scheduled_start="2026-10-01T11:00+07:00", scheduled_end="2026-10-01T12:00+07:00")

	# A pending invitation doesn't block; an accepted one does
	m = create(client, budi, title="Undangan Budi", scheduled_start="2026-10-02T09:00+07:00", scheduled_end="2026-10-02T10:00+07:00", invitee_ids=[ani_id])
	create(client, ani, title="Masih boleh", scheduled_start="2026-10-02T09:30+07:00", scheduled_end="2026-10-02T10:30+07:00")
	res = client.post(f"/api/v1/meetings/{m['id']}/respond", json={"action": "accept"}, headers=ani)
	assert res.status_code == 200
	res = client.post("/api/v1/meetings", json={**MEETING, "scheduled_start": "2026-10-02T09:00+07:00", "scheduled_end": "2026-10-02T09:30+07:00"}, headers=ani)
	assert res.status_code == 409 and "Undangan Budi" in res.json()["detail"]


def test_edit_cannot_move_into_a_clash(client: TestClient, make_user):
	_, ani = make_user("Ani")
	budi_id, budi = make_user("Budi")
	create(client, ani, title="Pagi")
	m = create(client, ani, title="Siang", scheduled_start="2026-10-01T13:00+07:00", scheduled_end="2026-10-01T14:00+07:00", invitee_ids=[budi_id])

	# Organizer clash
	res = client.put(f"/api/v1/meetings/{m['id']}", json={"scheduled_start": "2026-10-01T10:00+07:00", "scheduled_end": "2026-10-01T11:30+07:00"}, headers=ani)
	assert res.status_code == 409 and "Pagi" in res.json()["detail"]
	assert client.get(f"/api/v1/meetings/{m['id']}", headers=ani).json()["scheduled_start"].startswith("2026-10-01T06:00")

	# Invitee clash
	create(client, budi, title="Rapat Budi", scheduled_start="2026-10-01T15:00+07:00", scheduled_end="2026-10-01T16:00+07:00")
	res = client.put(f"/api/v1/meetings/{m['id']}", json={"scheduled_start": "2026-10-01T15:00+07:00", "scheduled_end": "2026-10-01T16:00+07:00"}, headers=ani)
	assert res.status_code == 409 and "Budi" in res.json()["detail"]

	# Moving within its own slot, or editing other fields, is fine
	res = client.put(f"/api/v1/meetings/{m['id']}", json={"scheduled_end": "2026-10-01T14:30+07:00", "title": "Siang (diperpanjang)"}, headers=ani)
	assert res.status_code == 200, res.text
