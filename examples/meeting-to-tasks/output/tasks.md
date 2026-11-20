# BrightSmile x Northbeam - Project kickoff call

**Wednesday 2 Dec 2026** · Hoa Tran, Dr. Minh Le, Thu Nguyen, Khoa Pham (BrightSmile) · An Vo, Bao Dang (Northbeam)

## Summary

BrightSmile confirmed the Recommended option (SMS reminders in; Zalo and the dashboard after Tet) and agreed the booking and handover rules. This week's critical path is access and content: SMS account details and Facebook admin by **Fri 4 Dec**, calendar sharing on **Mon 7 Dec**, and the price and insurer lists on **Thu 3 Dec**, so the Vietnamese script can go to review by **Fri 11 Dec** and be approved before the **18 Dec content freeze**. Still open: who receives handover alerts at night.

## Decisions

| ID | Decision |
|---|---|
| D1 | Recommended option; admin dashboard postponed until after Tet. |
| D2 | SMS reminders in scope; Zalo out for now. |
| D3 | Only check-ups, cleaning, fillings and whitening are bookable online; everything else becomes a consultation request. Last appointment ends 30 minutes before closing. |
| D4 | Urgent symptoms (pain, swelling, bleeding) get the clinic hotline immediately plus a handover alert; other medical questions and complaints get a normal handover. |
| D5 | The assistant never confirms insurance coverage; it offers a front-desk check instead. |
| D6 | Hoa and Dr. Minh both review the script and approve within 2 business days. |
| D7 | User testing on 28, 29 and 30 Dec with Thu and Khoa. |

## Action items

| ID | Task | Owner | Due | Priority |
|---|---|---|---|---|
| A2 | Send service account email for calendar sharing | Bao Dang | Wed 2 Dec | High |
| A4 | Send latest price list and insurer list to An | Thu Nguyen | Thu 3 Dec | High |
| A1 | Check SMS brandname on TinNhanNhanh account and send details | Hoa Tran | Fri 4 Dec | High |
| A8 | Ask marketing agency to add Bao as Facebook page admin | Hoa Tran | Fri 4 Dec | High |
| A3 | Share all 11 dentist calendars with the service account *(after A2)* | Hoa Tran | Mon 7 Dec | High |
| A5 | Draft Vietnamese script and send to Hoa and Dr. Minh *(after A4)* | An Vo | Fri 11 Dec | High |
| A10 | Add optional "how did you hear about us" question to booking | An Vo | Fri 11 Dec* | Low |
| A6 | Review and approve the Vietnamese script *(after A5)* | Dr. Minh Le | Tue 15 Dec* | High |
| A7 | Add insurance-coverage test case to the test script | Bao Dang | - | Medium |
| A9 | Send testing invites for 28-30 Dec to Thu and Khoa | An Vo | - | Medium |

\* Inferred: A10 ships with the script draft; A6 is 2 business days after the draft arrives.

## Open questions

- **Q1** Who receives handover alerts at night and on Sundays at each clinic? Needed before testing on 28 Dec. *(Hoa Tran)*
- **Q2** Opening hours for District 3 and Thu Duc were not discussed - confirm weekday and Saturday hours. *(no owner yet)*
- **Q3** At which clinics do Dr. Lan and Dr. Quang work, so whitening is only offered there? *(no owner yet)*

## Notes for the organiser

- Validation: `tasks_tool.py validate` passed - 10 action items, all quotes found in the transcript, 0 errors, 0 warnings.
- Exports: `tasks-jira.csv` (set the date format to `yyyy-MM-dd` in the Jira import wizard), `tasks-asana.csv`, `tasks-notion.csv`, `tasks-generic.csv`.
- A8's date is soft ("hopefully by Friday") - worth a reminder on Thursday.
- Q2 and Q3 have no owner; suggest assigning both to Hoa, as Operations Manager.
