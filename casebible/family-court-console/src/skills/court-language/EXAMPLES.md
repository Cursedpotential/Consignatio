---
name: court-language-examples
description: Worked before/after rewrite pairs and the safe phrasebank for each doc_type in court_language_review. Read alongside SKILL.md and TEMPLATES.md before rewriting anything. Loaded at runtime by mcp-app/src/court-language.ts to build the tool's safe_phrasebank output — keep the "### Safe phrasebank" bullet list under each doc_type heading in sync with any edits here.
---

> _Byline: Claude Code · Fable 5.1 · 2026-09-07._ Every example is synthetic — no real names, no real
> case facts. "Before" voice is drawn from the raw phrasing `content/tools/court-language/lexicon.json`
> catches; "After" voice follows the reframing table in
> `skills/family-court-toolkit/references/documentation-methods/SKILL.md` ("Reframing Emotions for
> Court") and the constraints in `content/custody-guide/GUARDRAILS.md` S2 (banned clinical labels) and
> S8 (child-protection absolute). **Parsing contract:** each doc_type section is a `## <doc_type>`
> heading matching a key in `lexicon.json`'s `doc_profiles`; the bullet list under that section's
> `### Safe phrasebank` heading is loaded verbatim as the tool's `safe_phrasebank` for that doc_type.
> Do not rename a doc_type heading without updating `lexicon.json` to match.

## affidavit

### Example 1
**Before:** "He is a narcissist who always shows up late and never calls ahead, and it's obviously outrageous."
**After:** "1. On January 12, 2024, February 3, 2024, and February 28, 2024, [Party] arrived more than 20 minutes after the scheduled 5:00 PM exchange time. 2. On none of those three occasions did [Party] call ahead to notify me of the delay."

### Example 2
**Before:** "She's manipulative and I think she's probably keeping him from me on purpose."
**After:** "3. On May 1, 2024, I called to arrange parenting time as provided in the current order. 4. I did not receive a response, and I did not exercise parenting time that weekend."

### Example 3
**Before:** "My son told me dad left him home alone for three hours, which is basically neglect."
**After:** "5. Between approximately 2:00 PM and 5:00 PM on June 8, 2024, I called the household three times and did not reach an answer. I have attached my phone log as Exhibit A."

### Example 4
**Before:** "I recorded the call where she admitted lying, and it proves she's a liar."
**After:** "[Do not include this paragraph. Consult a licensed Michigan attorney about the recording before referencing it anywhere in this affidavit or any filing.]"

### Safe phrasebank
- "On [date], I personally observed [specific event]."
- "I have personal knowledge of the following facts."
- "A true and accurate copy of [document] is attached as Exhibit [X]."
- "I do not have personal knowledge of [fact], and I do not assert it here."
- "On [date] and [date], [specific, countable event] occurred."
- "I am competent to testify to the matters stated in this affidavit."
- "The following facts are stated from my own direct observation."
- "I declare that the statements above are true to the best of my information, knowledge, and belief."

## motion_brief

### Example 1
**Before:** "The other parent is obviously an unfit, controlling narcissist who is unstable and dangerous."
**After:** "The record establishes that [Party] did not appear for three consecutive scheduled exchanges (Exhibit A, Exhibit B, Exhibit C), each without advance notice, which bears on the best-interest factor concerning willingness to facilitate a relationship with the other parent, MCL 722.23(j)."

### Example 2
**Before:** "He clearly did this on purpose to punish me, and it's ridiculous that he keeps getting away with it."
**After:** "On the three dates identified in Exhibits A-C, [Party] did not provide the notice required by the current order. This pattern is relevant to MCL 722.23(j)."

### Example 3
**Before:** "This is custodial interference and outright contempt — he should be punished."
**After:** "[Party]'s failure to return the child at the ordered exchange time on the dates in Exhibit D is inconsistent with the current order's terms; the court may consider whether enforcement under MCR 3.208 is warranted."

### Safe phrasebank
- "The record establishes that [specific fact], as shown in Exhibit [X]."
- "This pattern is relevant to MCL 722.23([factor])."
- "[Party] did not comply with the order's requirement that [specific term], on [dates], per Exhibit [X]."
- "The court may consider whether [specific relief] is warranted based on [cited exhibit/record]."
- "No exhibit currently in the record establishes [contested fact]; the movant respectfully submits that [cited exhibit] resolves the question."

## testimony_answer

### Example 1
**Before (volunteered narrative to a yes/no question):** "Are you employed? — Well, it's complicated, I lost my job because my ex kept causing problems and I couldn't focus, and honestly it's her fault I'm in this position, she's always sabotaging me."
**After:** "No. I am not currently employed."

### Example 2
**Before:** "Did you see your daughter last month? — Barely, because he's an alienator who blocks every single attempt I make, it's honestly disgusting what he does."
**After:** "I saw her once, on May 3rd."

### Example 3
**Before:** "Do you agree with the proposed support calculation? — I probably would if it weren't for the fact that he's lying about his income, which he always does."
**After:** "I'd like to review the written recommendation before agreeing."

### Safe phrasebank
- "No."
- "Yes."
- "I don't know."
- "I don't have that information."
- "Could you clarify the question?"
- "I don't believe that's within the scope of today's hearing."
- "That is the factual answer."
- "I can provide records if needed."

## message_to_other_parent

### Example 1
**Before:** "You ALWAYS wait until the last minute and expect me to drop everything, you're so selfish, and the kids will be so disappointed in you again just like every other time."
**After:** "I received your request to change Friday's pickup from 5 PM to 7 PM. That doesn't work for our schedule. I'll have the children ready at 5 PM as ordered."

### Example 2
**Before:** "If you don't have him ready by 5 you'll regret it, this is exactly why we're divorced, you never think about anyone but yourself."
**After:** "Per the current order, I will arrive for pickup at 5:00 PM today."

### Example 3
**Before:** "You're a liar and a narcissist and I know you're doing this on purpose to hurt me."
**After:** "The appointment on June 10 conflicts with my scheduled parenting time. Please reschedule to a time outside 3-7 PM, or let me know and I will take her."

### Safe phrasebank
- "I received your message about [topic]. [Brief factual response]."
- "That doesn't work for our schedule. [Alternative, if any]."
- "Per the current order, [specific action] will occur at [time/date]."
- "I'll have the children ready at [time] as scheduled."
- "Please confirm by [date] so I can plan accordingly."
- "I'm not able to discuss that further here; I'll follow up in writing if needed."

## incident_log

### Example 1
**Before:** "He was drunk again and totally out of control, screaming like a lunatic, it was insane."
**After:** "F: On March 15, 2024, at 6:45 PM, [Party] arrived to pick up the children. I could smell alcohol on his breath from approximately 3 feet away; his speech was slightly slurred. A: I told him I was not comfortable sending the children with him and offered to reschedule. He declined and left. C: This is the 4th such observation in 6 months (prior: 1/12/24, 2/3/24, 2/28/24). T: March 15, 2024, 6:45 PM, at my home."

### Example 2
**Before:** "She's clearly manipulating the kids again, it's obvious she's alienating them from me."
**After:** "F: On April 2, 2024, I observed our son become tearful and hesitant while getting ready for his scheduled visit. A: I did not question him about it and proceeded with the scheduled exchange. C: This is the 2nd time in 3 months I have observed this reaction before a scheduled exchange (prior: 2/10/24). T: April 2, 2024, 4:00 PM, at pickup."

### Example 3
**Before:** "He obviously did this on purpose because he's vindictive and wants to sabotage my time."
**After:** "F: On May 20, 2024, the school called at 2:30 PM to say [Party] had scheduled a dentist appointment for our daughter during my 3-7 PM parenting time without prior notice to me. A: I called the school to confirm the appointment time and documented the call. C: This is the 1st such scheduling conflict this year. T: May 20, 2024, 2:30 PM call; appointment scheduled for 4:00 PM."

### Safe phrasebank
- "F: On [date] at [time], [observable event]."
- "A: I [specific action taken]."
- "C: This is the [Nth] occurrence of [pattern] in [timeframe] (prior: [dates])."
- "T: [date], [time], [location]."
- "I documented this with [photo/screenshot/witness] at the time."

## objection_to_recommendation

### Example 1
**Before:** "I object to the entire recommendation, it's completely unfair and the referee obviously didn't listen to a word I said."
**After:** "Finding 3: The referee found that overnight parenting time should remain unchanged. This finding is not supported by the record because Exhibit C (school attendance log, admitted at the hearing) shows the child missed school on the mornings following each of the last three overnight visits — a fact the referee's recommendation does not address. Requested correction: modify overnight parenting time to [specific proposed schedule]."

### Example 2
**Before:** "The referee sided with her because she lied on the stand and everyone could see it, this whole thing is rigged."
**After:** "Finding 5: The referee found [Party]'s testimony regarding the child's bedtime routine credible. This finding is not supported by the record because [Party]'s own Exhibit 2 (text message dated 4/1/24) is inconsistent with that testimony, and no other exhibit corroborates it. Requested correction: strike Finding 5 or reopen the record on this narrow point."

### Example 3
**Before:** "This whole recommendation should be thrown out because the referee is clearly biased against fathers."
**After:** "Finding 1: The referee found that [Party] failed to provide 14 days' notice of the requested schedule change, as required by [order term]. This finding is not supported by the record because Exhibit A (certified mail receipt) shows notice was given 16 days before the requested date. Requested correction: strike Finding 1's characterization of the notice as untimely."

### Safe phrasebank
- "Finding [N]: [state the referee's finding, quoted or closely paraphrased]."
- "This finding is not supported by the record because [cite exhibit/transcript page]."
- "Requested correction: [specific, narrow relief]."
- "The record does not contain evidence supporting [specific element of the finding]."
- "I request a judicial hearing on this specific finding under MCR 3.215(E)(4)."
