# V306 cross-mode mapping test correction — 2026-10-14

Fix commit: `58ff27b60608240b55b3a753622f5435ba87bdb7`.

The prior adversarial fixture swapped boat_combo strings, which could fail earlier on duplicate/invalid boat tickets and therefore did not isolate the intended cross-mode entry mapping check. The corrected test changes only the course_combo permutation for the national_motor mode, preserving each mode's internally valid course/boat mapping and ensuring the expected result is specifically `CROSS_MODE_ENTRY_MISMATCH`.

Verified pull-request CI: V303 run `38440819531` SUCCESS; V303 8 tests PASS, V306 12 tests PASS including `test_cross_mode_entry_mismatch`. V301/V302/V304/V305 and Development CI also SUCCESS on the fix commit.

This is structural synthetic testing only. Main snapshot on 2026-10-14 still shows V230 eligible=0 and new snapshots=0; V232 new research freezes=0; V254 source cohorts=0. These values are not evidence of a daytime missed deadline, and no prospective accuracy score can be added. Formal Fresh remains locked; no production promotion.
