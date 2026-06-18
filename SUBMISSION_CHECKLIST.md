# Submission Checklist — EF234405 DAA Final Exam

> ⏰ **DEADLINE: 18 June 2026, 23:59 WIB.** Late penalty **0.15% of the grade per
> minute**. Submit early — a few minutes late is a real score loss.

This checklist mirrors §1 (Submission Guidelines) and §6 (compliance) of the
official brief. Items marked **[AUTHOR]** require you to fill in real identity
details before sending.

---

## 1. The ZIP archive

- [ ] **[AUTHOR]** Filename **exactly**:
      `EF234405_DAA_FIN_StudentID1_Name1[_StudentID2_Name2].ZIP`
      (append `_StudentID3_Name3` for a third member; use your real IDs and names,
      no spaces inside a name field — e.g. `EF234405_DAA_FIN_5025221001_BudiSantoso.ZIP`).
- [ ] The ZIP contains **exactly two files** and nothing else:
  - `Report.pdf`
  - `Declaration.pdf`
- [ ] `Declaration.pdf` is **signed** by every member (handwritten or digital).
- [ ] `Report.pdf` has the real names, Student IDs, class, and date on the title page.

A placeholder ZIP is pre-built at `dist/EF234405_DAA_FIN_StudentID1_Name1.ZIP`
(built by `python dist/make_zip.py`). **Rename it** with your real IDs/names, or
rebuild it after editing the report/declaration.

## 2. The email

- [ ] **To:** `yifana@gmail.com`  (MM Irfan Subakti)
- [ ] **CC** (all TAs — copy/paste this exact list):
  - `fellyla.hyuga@gmail.com` — Fellyla Fiorenza Wilianto
  - `putrimeyliyaalfath@gmail.com` — Putri Meyliya Rachmawati
  - `syalbiaishere@gmail.com` — Syalbia Noor Rahmah
  - `iffaamaliasabrina@gmail.com` — Iffa Amalia Sabrina
  - `mrafibudip@gmail.com` — Muhammad Rafi Budi Purnama
  - `aqilazhn05@gmail.com` — Aqila Zahira Naia Puteri Arifin
  - `itsrhenaldy@gmail.com` — Rhenaldy Chandra
  - `ricardo.supriyanto08@gmail.com` — Ricardo Supriyanto
  - `amelianovasafitri@gmail.com` — Amelia Nova Safitri
  - `thalytapramesti@gmail.com` — Thalyta Vius Pramesti
- [ ] **[AUTHOR] Subject** (no `.ZIP` extension):
      `EF234405_DAA_FIN_StudentID1_Name1[_StudentID2_Name2]`
- [ ] **Body includes the public GitHub link:**
      `https://github.com/milhan-z/draftpaa`
- [ ] The ZIP is attached.

## 3. Repository & reproducibility (checked separately by the TA)

- [ ] Repo is **public**: https://github.com/milhan-z/draftpaa
- [ ] Commit history shows each member committing under their own account
      (not one final push). **[AUTHOR]** If this is a team, ensure every member
      has commits under their own GitHub identity.
- [ ] `README.md` build/run/benchmark steps work on a **clean checkout**.
- [ ] One-command benchmark regenerates `bench/results.csv` + the plots.
- [ ] `pytest -q` passes.

## 4. Final sanity pass

- [ ] Open `Report.pdf` and `Declaration.pdf` one last time — fonts, figures,
      tables, and signatures all render correctly.
- [ ] Re-read the correctness proof in §3 until you can explain it without notes.
- [ ] Confirm every benchmark number in the report matches `bench/results.csv`.

---

### Quick send summary (fill the brackets)

```
To:      yifana@gmail.com
CC:      fellyla.hyuga@gmail.com, putrimeyliyaalfath@gmail.com, syalbiaishere@gmail.com,
         iffaamaliasabrina@gmail.com, mrafibudip@gmail.com, aqilazhn05@gmail.com,
         itsrhenaldy@gmail.com, ricardo.supriyanto08@gmail.com, amelianovasafitri@gmail.com,
         thalytapramesti@gmail.com
Subject: EF234405_DAA_FIN_[StudentID1]_[Name1][_StudentID2_Name2]
Attach:  EF234405_DAA_FIN_[StudentID1]_[Name1][_StudentID2_Name2].ZIP   (Report.pdf + Declaration.pdf)
Body:    Public repository: https://github.com/milhan-z/draftpaa
```
