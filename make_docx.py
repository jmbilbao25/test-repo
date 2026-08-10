"""Generates the assignment write-up as a .docx file."""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "JVM-Tuning-Assignment.docx")

doc = Document()

for section in doc.sections:
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)

PRINTABLE_IN = 6.5

style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(8)
style.paragraph_format.line_spacing = 1.10

_fig_no = [0]


def shade(paragraph, hex_fill):
    pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    pr.append(shd)


def code_block(lines):
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0) if i < len(lines) - 1 else Pt(10)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent = Inches(0.25)
        run = p.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)
        shade(p, "F2F2F2")


def figure(filename, caption, width=6.3):
    assert width <= PRINTABLE_IN
    _fig_no[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FIG, filename), width=Inches(width))

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(14)
    run = cap.add_run(f"Figure {_fig_no[0]}: {caption}")
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)


# ----------------------------------------------------------------- heading
day = doc.add_paragraph()
day.alignment = WD_ALIGN_PARAGRAPH.CENTER
day.paragraph_format.space_after = Pt(2)
drun = day.add_run("Day 2 Assignment")
drun.bold = True
drun.font.size = Pt(12)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_after = Pt(6)
trun = title.add_run("JVM Tuning and Spring Boot Microservice Performance")
trun.bold = True
trun.font.size = Pt(16)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(16)
for text, br in [("John Michael Bilbao", True),
                 ("Techstart", True),
                 ("August 10, 2026", False)]:
    r = sub.add_run(text)
    r.font.size = Pt(10.5)
    if br:
        r.add_break()

# ------------------------------------------------------------ introduction
doc.add_heading("Introduction", level=1)
doc.add_paragraph(
    "A microservice is just a small application that does one job and talks over HTTP. I used "
    "Spring Boot for this one because it comes with Tomcat built in and handles most of the setup "
    "itself, so the whole service is only a few lines of code."
)
doc.add_paragraph(
    "Spring Boot runs on the JVM, and the JVM decides how much memory the application gets and when "
    "it clears out objects that are no longer needed. That clearing out is garbage collection. If "
    "the heap is too small the collector keeps running, and the application spends more time "
    "freeing memory than answering requests. Tuning means setting options like the heap size and "
    "the collector type to fit the work the application actually does. I built a small item "
    "service, put it under load, watched it in VisualVM, then changed the settings to see what "
    "would happen. Everything here ran on Java 21 with Spring Boot 3.4.1, on a machine with eight "
    "cores."
)

# -------------------------------------------------------------- the service
doc.add_heading("The microservice", level=1)
doc.add_paragraph(
    "It is a Maven project with the Spring Web and Actuator dependencies. Three classes, and the "
    "controller is the only interesting one:"
)
code_block([
    "@RestController",
    "@RequestMapping(\"/api/items\")",
    "public class ItemController {",
    "",
    "    private static final String[] CATEGORIES =",
    "            {\"Tools\", \"Books\", \"Food\", \"Toys\", \"Parts\"};",
    "",
    "    @GetMapping",
    "    public List<Item> getItems(@RequestParam(defaultValue = \"5000\") int count) {",
    "        List<Item> items = new ArrayList<>();",
    "        for (int i = 0; i < count; i++) {",
    "            String name = \"Item \" + i + \" - \" + CATEGORIES[i % CATEGORIES.length];",
    "            items.add(new Item(i, name,",
    "                    CATEGORIES[i % CATEGORIES.length], 10.0 + (i % 100)));",
    "        }",
    "        return items;",
    "    }",
    "}",
])
doc.add_paragraph(
    "Item is a record with an id, name, category and price. The endpoint is "
    "GET /api/items?count=5000 and it returns the list as JSON."
)
doc.add_paragraph(
    "The list gets rebuilt on every request instead of being cached, which is on purpose. A cached "
    "list would barely allocate anything and there would be nothing to watch in VisualVM."
)
figure("fig1-terminal.png", "The endpoint responding, and the health check", width=5.9)

# ---------------------------------------------------------------- monitoring
doc.add_heading("Monitoring with VisualVM", level=1)
doc.add_paragraph(
    "I got VisualVM from visualvm.github.io and started it while the service was already running. "
    "The process shows up on the left under Local, and double clicking it opens the Overview tab, "
    "which shows the JVM options the process started with. I ran the first round with a small heap "
    "and the serial collector so there would be something to find:"
)
code_block(["java -Xms64m -Xmx128m -XX:+UseSerialGC \\",
            "     -cp \"target/classes:$(cat cp.txt)\" \\",
            "     com.example.itemservice.ItemserviceApplication"])
figure("fig-baseline-overview.png", "Overview tab, showing the baseline flags in effect")

doc.add_paragraph(
    "Nothing much happens while the application is idle, so I wrote a Python script that hits the "
    "endpoint from several threads at once and left it looping for a couple of minutes while I "
    "watched the Monitor tab."
)
figure("fig-baseline-monitor.png", "Monitor tab during the baseline run", width=5.9)
doc.add_paragraph(
    "Heap went straight up to its ceiling and stayed pinned there, and used heap sawtoothed up and "
    "down without ever settling, so the collector was running constantly rather than every now and "
    "then. Threads went up when the load arrived and then stayed flat, so the thread count was not "
    "the problem."
)
doc.add_paragraph(
    "The GC activity figure confused me at first. VisualVM showed about 7 percent, which sounds "
    "harmless, but the GC log for the same session was full of collections and showed the "
    "application frozen for most of the run. Both are right. Serial GC stops everything and then "
    "works on a single thread, and VisualVM spreads GC time across all the cores, so one busy core "
    "out of eight looks small. The graph shows how much of the CPU is going into GC, while the log "
    "shows how long the application is actually stopped, and for a service answering requests it is "
    "the second one that matters."
)

# -------------------------------------------------------------------- tuning
doc.add_heading("Changing the settings", level=1)
doc.add_paragraph(
    "The heap was the problem, not CPU and not threads. I raised the maximum from 128 MB to 512 MB "
    "and set the minimum to match, which stops the JVM growing the heap while it is already busy. I "
    "also swapped the serial collector for G1, since G1 spreads its work across cores and does much "
    "of it concurrently, and gave it a 100 ms pause target."
)
code_block([
    "java -Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 \\",
    "     -cp \"target/classes:$(cat cp.txt)\" \\",
    "     com.example.itemservice.ItemserviceApplication",
])
figure("fig-tuned-overview.png", "Overview tab after the change")
figure("fig-tuned-monitor.png", "Monitor tab during the tuned run", width=5.9)
doc.add_paragraph(
    "Used heap now moves up and down with visible gaps instead of one solid band, so the collector "
    "gets to rest between cycles. GC activity dropped to almost nothing and the full collections "
    "disappeared completely. CPU actually went up a little, which looked wrong until I realised it "
    "was finally being spent on requests instead of on collecting garbage."
)

# ------------------------------------------------------------------ results
doc.add_heading("Results", level=1)
doc.add_paragraph(
    "Screenshots show behaviour but not speed, so I ran the load test again with VisualVM detached. "
    "Same code and same machine, only the flags were different."
)

t = doc.add_table(rows=1, cols=3)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
# Fixed layout, otherwise the column widths are ignored and the table gets
# stretched across the full page width.
t.autofit = False
COL_TWIPS = [3600, 1440, 1440]  # 2.5in, 1.0in, 1.0in
grid = t._tbl.find(qn("w:tblGrid"))
for gc, tw in zip(grid.findall(qn("w:gridCol")), COL_TWIPS):
    gc.set(qn("w:w"), str(tw))
hdr = t.rows[0].cells
for i, h in enumerate(["", "Before", "After"]):
    hdr[i].text = ""
    run = hdr[i].paragraphs[0].add_run(h)
    run.bold = True
    run.font.size = Pt(10)
for row in [
    ["Requests per second", "103", "174"],
    ["Average response time", "155 ms", "92 ms"],
    ["Slowest 5% of requests", "288 ms", "115 ms"],
    ["Full collections", "76", "0"],
    ["Total time paused", "9.8 s", "0.2 s"],
]:
    cells = t.add_row().cells
    for i, val in enumerate(row):
        cells[i].text = ""
        r = cells[i].paragraphs[0].add_run(str(val))
        r.font.size = Pt(10)
for r_ in t.rows:
    for i, tw in enumerate(COL_TWIPS):
        r_.cells[i].width = Inches(tw / 1440)
doc.add_paragraph()

doc.add_paragraph(
    "The full collections are what stand out. Each one freezes every thread while it works, and "
    "that is what made the slowest requests slow."
)
doc.add_paragraph(
    "I had run a lighter test earlier and it barely moved at all. The GC work still dropped, but "
    "the application was not waiting on garbage collection at that load in the first place, so "
    "there was nothing for the change to fix. The improvement only turned up once the load was "
    "heavy enough to run the small heap out of room."
)

# ------------------------------------------------------------------ learned
doc.add_heading("What I learned", level=1)
doc.add_paragraph(
    "Tuning only helps if the thing you are tuning is what is actually slowing you down. The "
    "lighter test made that obvious, since the GC work dropped a long way and the response times "
    "did not move at all."
)
doc.add_paragraph(
    "It is also worth checking what a percentage is a percentage of. The GC activity on screen "
    "looked fine sitting next to a log that showed the application frozen for most of the run, and "
    "neither number was wrong."
)
doc.add_paragraph(
    "Repeated full collections turned out to be a better warning sign than a heap sitting near its "
    "limit, since a full heap can just mean the collector is doing its job well. And bigger is not "
    "automatically better. I went with 512 MB because that was what got rid of them. Java's own "
    "default on this machine was a much larger heap with G1 already chosen, and the endpoint never "
    "struggled, so I had to shrink it on purpose to create a problem worth looking at."
)

doc.save(OUT)
print("wrote", OUT)
