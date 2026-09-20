# Ward round factfiles

A searchable, sortable set of revision notes for each specialty, published as a free website on GitHub Pages.
You write notes in a simple form (or plain Markdown files). GitHub turns them into web pages automatically.

> **Privacy:** free GitHub Pages sites are public. Never put patient details, or anything that could identify a patient, in a note.

---

## One-time setup (about 15 minutes)

1. **Make a repository.** Sign in at github.com, click **New repository**, name it (for example `factfiles`), keep it **Public**, and create it.
2. **Upload the files.** Unzip the download. On the new repository page click **Add file, then Upload files**, and drag in everything from inside the unzipped folder. Click **Commit changes**.
   - Check that the repository now shows a `.github` folder and a `.pages.yml` file. Some computers hide or skip these.
   - If either is missing, click **Add file, then Create new file**. Type the path (`.github/workflows/pages.yml` or `.pages.yml`), paste in the contents of the matching file from the `setup-backup` folder (`pages.yml` or `pages-cms.yml`), and commit.
3. **Turn on publishing.** Go to **Settings, then Pages**. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. **Wait for the first build.** Open the **Actions** tab. A run called *Build and deploy site* should be going (if not, open it and click **Run workflow**). When it shows a green tick, your site is live at `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/`. Bookmark it.
5. **Connect the editor.** Go to **app.pagescms.org**, sign in with GitHub, and follow the prompts to give it access to this one repository. Open the repository and you will see **Factfiles**, **Specialties**, **Categories** and **Site settings** in the sidebar. Bookmark this too.

You never need to repeat these steps.

---

## Adding a new note (the everyday routine)

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
