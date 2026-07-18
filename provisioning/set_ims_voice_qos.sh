#!/usr/bin/env bash
#
# set_ims_voice_qos.sh — ensure IMS subscribers carry a usable dedicated
# voice/video bearer policy so Open5GS creates the 5QI-1 (voice) and 5QI-2
# (video) GBR flows for VoLTE/VoNR calls.
#
# Why this is needed: the Open5GS PCF picks the 5QI from the media type
# (audio -> 5QI-1, video -> 5QI-2) but takes the GBR/MBR from the
# subscriber's session PCC rule, ignoring the bandwidth the P-CSCF signals.
# The webui/open5gs-dbctl leave those PCC-rule GBR/MBR values unset (0), so
# no dedicated GBR bearer is ever created and voice rides the default flow.
# This script sets non-zero GBR/MBR on the "ims" APN's 5QI-1 and 5QI-2 PCC
# rules (creating the rules if absent). It is idempotent.
#
# Usage:
#   provisioning/set_ims_voice_qos.sh <IMSI> [<IMSI> ...]
#   provisioning/set_ims_voice_qos.sh all
#
# Run it after adding an IMS subscriber. Values (Kbps) may be overridden:
#   AUDIO_GBR/AUDIO_MBR (default 44/64), VIDEO_GBR/VIDEO_MBR (default 512/2048).

set -euo pipefail

MONGO_CONTAINER="${MONGO_CONTAINER:-mongo}"
MONGO_DB="${MONGO_DB:-open5gs}"
IMS_APN="${IMS_APN:-ims}"
AUDIO_GBR="${AUDIO_GBR:-44}"; AUDIO_MBR="${AUDIO_MBR:-64}"
VIDEO_GBR="${VIDEO_GBR:-512}"; VIDEO_MBR="${VIDEO_MBR:-2048}"

if [[ $# -lt 1 ]]; then
	echo "usage: $0 <IMSI> [<IMSI> ...] | all" >&2
	exit 64
fi

# Build the Mongo query selector: all IMS subscribers, or a specific list.
if [[ "$1" == "all" ]]; then
	SELECTOR='{}'
else
	printf -v LIST '"%s",' "$@"
	SELECTOR="{ imsi: { \$in: [ ${LIST%,} ] } }"
fi

docker exec -i "$MONGO_CONTAINER" mongosh --quiet "$MONGO_DB" <<EOF
// Kbps bit-rate unit in Open5GS is 1.
function kbps(v) { return { value: v, unit: 1 }; }
function ensureRule(rules, index, gbr, mbr) {
	var r = rules.find(function(x){ return x.qos && x.qos.index === index; });
	if (!r) {
		r = { qos: { index: index,
			arp: { priority_level: index === 1 ? 2 : 4,
			       pre_emption_capability: 2, pre_emption_vulnerability: 2 },
			gbr: {}, mbr: {} }, flow: [] };
		rules.push(r);
	}
	r.qos.gbr = { downlink: kbps(gbr), uplink: kbps(gbr) };
	r.qos.mbr = { downlink: kbps(mbr), uplink: kbps(mbr) };
	return r;
}

var changed = 0, skipped = 0;
db.subscribers.find(${SELECTOR}).forEach(function(s) {
	var touched = false, hasIms = false;
	(s.slice || []).forEach(function(sl) {
		(sl.session || []).forEach(function(se) {
			if (se.name !== "${IMS_APN}") return;
			hasIms = true;
			if (!se.pcc_rule) se.pcc_rule = [];
			ensureRule(se.pcc_rule, 1, ${AUDIO_GBR}, ${AUDIO_MBR});
			ensureRule(se.pcc_rule, 2, ${VIDEO_GBR}, ${VIDEO_MBR});
			touched = true;
		});
	});
	if (touched) {
		db.subscribers.updateOne({ _id: s._id }, { \$set: { slice: s.slice } });
		print("updated " + s.imsi + " (ims 5QI-1 gbr=${AUDIO_GBR}/mbr=${AUDIO_MBR}, 5QI-2 gbr=${VIDEO_GBR}/mbr=${VIDEO_MBR})");
		changed++;
	} else {
		print("SKIP  " + s.imsi + " — no '${IMS_APN}' APN session (add the IMS session first)");
		skipped++;
	}
});
print("done: " + changed + " updated, " + skipped + " skipped");
EOF
