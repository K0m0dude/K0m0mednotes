# Ward round factfiles

A searchable, sortable set of revision notes for each specialty, published as a free website on GitHub Pages.
You write notes in a simple form (or plain Markdown files). GitHub turns them into web pages automatically.

> **Privacy:** free GitHub Pages sites are public. Never put patient details, or anything that could identify a patient, in a note.

---

## Adding a new note

1. Open **app.pagescms.org**, choose your repository, and click **Factfiles**, then the button for adding a new entry.
2. Fill in the form:
   - **Title**, **Specialty** and **Category** (pick from the drop-downs).
   - Optional: a **Short name** for the jump buttons, and **Search keywords** (abbreviations, drug names) so the search finds it.
3. Type into the five boxes: **Background and pathophysiology**, **Diagnosis and clinical signs**, **Investigations**, **Treatment**, **Emergency protocols and red flags**. Use the toolbar for bullets and bold, or click **Source** to type Markdown. Leave a box empty to skip that section.
4. Click **Save**. Wait a minute or two, then refresh your site. The note is there, in the right place, sorted, searchable and listed on the home page.
5. Not finished? Tick **Draft** before saving. The note stays hidden until you untick it.

To change a note later, open it in the same list, edit, and save.

### Formatting cheat sheet

| You want | Type |
| --- | --- |
| Bullet point | `- text` |
| Sub-bullet | indent it under a bullet |
| Bold | `**text**` |
| Italic | `*text*` |
| Sub-heading inside a section | `### Heading` |
| Blue key-facts box | start the line with `> ` |
| Red warning box | start with `> Red flag:` (or `> Warning:`) |
| Table | a normal Markdown table |

The orange box at the end of each card is the **Emergency protocols and red flags** section.

---

## Adding a new specialty

1. In the editor open **Specialties**, add an entry with a **Title**, a **Short description**, a **Colour** (hex code such as `#b3261e`) and an **Order**.
2. Add notes as usual and choose the new specialty in the **Specialty** drop-down.

The home page gets a new card and the specialty gets its own page automatically. A specialty only appears once it has at least one published note.

## Adding a new category

Nineteen categories are ready (Cardiovascular, Respiratory, Musculoskeletal, Dermatology, Psychiatry, Paediatrics and so on). To add another, open **Categories** in the editor and add an entry with a title, colour and order. It then appears in the **Category** drop-down.

---

## If something goes wrong

- **A note does not appear.** Open the **Actions** tab on GitHub and click the latest run. If it has a red cross, the error names the file and what to fix (for example a missing title, or a specialty that does not exist). Fix it and save again. Until then the live site keeps showing the last good version.
- **The note appears under "Uncategorised".** Its category was left blank or does not exist. Pick one from the drop-down.
- **You changed the site title, disclaimer or footer.** Edit them under **Site settings** in the editor.

---

## How it fits together (for reference)

```
content/
  notes/            one Markdown file per factfile
  specialties/      one file per specialty (title, description, colour)
  categories/       one file per category (title, colour, order)
  site.yml          site title, introduction, disclaimer, footer
templates/          page layout, styling and search/sort script
build.py            turns the content into the website (runs on GitHub)
.pages.yml          defines the editor forms
.github/workflows/  the automatic build and publish step
```

To preview on your own computer: install Python, run `pip install -r requirements.txt`, then `python build.py`, and open `dist/index.html`.
