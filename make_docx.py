"""Generates the assignment write-up as a .docx file."""
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = "/projects/sandbox/jvm-tuning-assignment/JVM-Tuning-Assignment.docx"

doc = Document()

# Base font
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(8)
style.paragraph_format.line_spacing = 1.15


def shade(paragraph, hex_fill):
    pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    pr.append(shd)


def code_block(lines):
    """Monospaced, shaded block for code and commands."""
    for i, line in enumerate(lines):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0) if i < len(lines) - 1 else Pt(10)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.left_indent = Inches(0.25)
        run = p.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)
        shade(p, "F2F2F2")


def screenshot_slot(caption):
    """Placeholder box where the screenshot gets pasted in."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run("[  PASTE SCREENSHOT HERE  ]")
    run.font.name = "Consolas"
    run.font.size = Pt(10)
    run.bold = True
    run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    shade(p, "FAFAFA")

    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(12)
    crun = cap.add_run(caption)
    crun.italic = True
    crun.font.size = Pt(9)
    crun.font.color.rgb = RGBColor(0x59, 0x59, 0x59)


def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        shade(hdr[i].paragraphs[0], "DDDDDD")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            run.font.size = Pt(10)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


# ----------------------------------------------------------------- title
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
trun = title.add_run("JVM Tuning and Spring Boot Microservice Performance")
trun.bold = True
trun.font.size = Pt(18)

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(18)
for text, br in [("Name: [Your Name]", True),
                 ("Course / Section: [Course]", True),
                 ("Date: [Date]", False)]:
    r = sub.add_run(text)
    r.font.size = Pt(10.5)
    if br:
        r.add_break()

# ----------------------------------------------------------- introduction
doc.add_heading("1. Introduction", level=1)
doc.add_paragraph(
    "A microservice is a small application that does one job and communicates over HTTP. "
    "I used Spring Boot to build one because it comes with an embedded Tomcat server and "
    "sets up most of the configuration on its own, so a working REST endpoint only takes a "
    "few lines of code."
)
doc.add_paragraph(
    "Every Spring Boot application runs inside the JVM, and the JVM is what decides how much "
    "memory the application can use and when it throws away objects that are no longer needed. "
    "That cleanup is called garbage collection. When the heap is too small for the workload, the "
    "collector has to run over and over, and the application ends up spending more time freeing "
    "memory than answering requests. JVM tuning is the process of setting options such as the "
    "heap size and the collector type so the application matches the work it actually does."
)
doc.add_paragraph(
    "For this assignment I built a small item service, put it under load, watched it in VisualVM, "
    "then changed the JVM settings and measured the difference."
)

doc.add_paragraph()
p = doc.add_paragraph()
r = p.add_run("Environment: ")
r.bold = True
p.add_run("Java 21 (OpenJDK), Spring Boot 3.4.1, Maven 3.9, 8 CPU cores, 31 GB RAM.")

# --------------------------------------------------------------- step 1
doc.add_heading("2. Step 1: Building the Microservice", level=1)
doc.add_paragraph(
    "I created a Maven project with the Spring Web and Spring Boot Actuator dependencies. The "
    "whole service is three classes. The controller is the only part that really matters:"
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
    "Item itself is just a record with an id, name, category and price. The endpoint is "
    "GET /api/items?count=5000 and it returns the list as JSON."
)
doc.add_paragraph(
    "One thing I did on purpose: the list is rebuilt on every single request instead of being "
    "cached. If I cached it the service would barely allocate anything and there would be nothing "
    "interesting to look at in VisualVM. Rebuilding it means every request creates thousands of "
    "short lived objects, which is what puts pressure on the garbage collector."
)
doc.add_paragraph("Building and running it:")
code_block([
    "mvn package -DskipTests",
    "java -jar target/itemservice-0.0.1-SNAPSHOT.jar",
    "",
    "curl \"http://localhost:8085/api/items?count=10\"",
])
doc.add_paragraph(
    "I tested it in Postman first to confirm it returned a proper JSON array before worrying "
    "about performance."
)
screenshot_slot("Figure 1: Response from GET /api/items in Postman")

# --------------------------------------------------------------- step 2
doc.add_heading("3. Step 2: Monitoring with VisualVM", level=1)
doc.add_paragraph(
    "I downloaded VisualVM from visualvm.github.io and started it while the service was already "
    "running. The local Java process shows up in the panel on the left, listed by its main class. "
    "Double clicking it opens the Monitor tab with the CPU, heap, classes and threads graphs."
)
doc.add_paragraph(
    "An idle application does not show much, so I needed traffic. I wrote a short Python script "
    "that sends 1,200 requests using 16 threads, asking for 25,000 items each time, and records "
    "how long every request takes."
)
doc.add_paragraph(
    "For the first run I started the service with a small heap so I could see the problem clearly:"
)
code_block(["java -Xms64m -Xmx128m -XX:+UseSerialGC -jar target/itemservice-0.0.1-SNAPSHOT.jar"])
doc.add_paragraph("What the Monitor tab showed while the load was running:")
for line in [
    "Used heap shot up to the 128 MB ceiling within a couple of seconds and stayed pinned there.",
    "The heap graph had a very tight sawtooth shape, which means collections were happening one "
    "after another with almost no gap.",
    "CPU usage was high, but the GC activity portion of the graph was taking most of it rather "
    "than the application itself.",
    "Thread count stayed flat at around 30, so threads were not the problem.",
]:
    doc.add_paragraph(line, style="List Bullet")

screenshot_slot("Figure 2: VisualVM Monitor tab under load, heap capped at 128 MB")
screenshot_slot("Figure 3: CPU graph showing GC activity taking most of the CPU time")

doc.add_paragraph(
    "Reading exact pause times off a graph is guesswork, so I also turned on GC logging to get "
    "real numbers to put next to the screenshots:"
)
code_block(["-Xlog:gc:file=gc.log:time,level,tags"])
doc.add_paragraph(
    "The log made the problem obvious. During the 11.65 second test the JVM ran 369 collections, "
    "and 76 of those were full GCs. Added together the pauses came to 9,812 ms. That means the "
    "application was stopped for roughly 84 percent of the run. The bottleneck was not my code "
    "and it was not CPU or threads, it was simply that the heap was far too small for the amount "
    "of garbage the endpoint produces."
)

# --------------------------------------------------------------- step 3
doc.add_heading("4. Step 3: Optimizing the JVM Settings", level=1)
doc.add_paragraph("Based on what VisualVM and the GC log showed, I changed the settings like this:")
table(
    ["Setting", "Before", "After", "Why"],
    [
        ["Initial heap", "-Xms64m", "-Xms512m",
         "Starting equal to the maximum stops the JVM from repeatedly growing the heap while it "
         "is already busy."],
        ["Maximum heap", "-Xmx128m", "-Xmx512m",
         "The real fix. There was never enough room for the short lived objects, so collections "
         "never stopped."],
        ["Collector", "-XX:+UseSerialGC", "-XX:+UseG1GC",
         "Serial GC uses one thread and stops the whole application. G1 works in parallel across "
         "cores and does much of its work concurrently."],
        ["Pause target", "not set", "-XX:MaxGCPauseMillis=100",
         "Tells G1 to aim for pauses under 100 ms, which it balances by resizing its regions."],
    ],
    widths=[1.1, 1.15, 1.15, 2.9],
)
doc.add_paragraph("The tuned command:")
code_block([
    "java -Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 \\",
    "     -jar target/itemservice-0.0.1-SNAPSHOT.jar",
])
doc.add_paragraph(
    "I ran the same load script again with VisualVM attached. This time the heap graph looked "
    "completely different. Used heap moved between roughly 60 MB and 200 MB inside the 512 MB "
    "space, with clear gaps between collections instead of a solid band, and the GC portion of "
    "the CPU graph dropped to a thin line."
)
screenshot_slot("Figure 4: VisualVM Monitor tab after tuning, heap with room to breathe")

# --------------------------------------------------------------- results
doc.add_heading("5. Results", level=1)
doc.add_paragraph(
    "Same code, same load script, same machine. The only difference between the two columns is "
    "the JVM flags."
)
table(
    ["Measurement", "Before tuning", "After tuning", "Change"],
    [
        ["Requests handled per second", "103.0", "173.5", "68% faster"],
        ["Average response time", "155.0 ms", "92.0 ms", "41% lower"],
        ["Median (p50) response time", "161.2 ms", "92.6 ms", "43% lower"],
        ["95th percentile response time", "287.7 ms", "115.3 ms", "60% lower"],
        ["Slowest single request", "454.3 ms", "173.1 ms", "62% lower"],
        ["Total time for 1,200 requests", "11.65 s", "6.92 s", "4.73 s saved"],
        ["Garbage collections", "369", "32", "91% fewer"],
        ["Full GCs", "76", "0", "eliminated"],
        ["Total time paused for GC", "9,812 ms", "236 ms", "97% lower"],
    ],
    widths=[2.2, 1.4, 1.4, 1.3],
)
doc.add_paragraph(
    "The full GC count is the number I find most telling. A full GC stops every application "
    "thread while it collects the entire heap, and there were 76 of them before the change and "
    "none at all after. The 95th percentile dropping from 287.7 ms to 115.3 ms is the same story "
    "seen from the user side, since those long pauses were exactly what made the slowest requests "
    "slow."
)

doc.add_heading("A result I did not expect", level=2)
doc.add_paragraph(
    "Before the heavy test I had run a lighter one, 2,000 requests of 5,000 items each. Those "
    "numbers were much less exciting:"
)
table(
    ["Measurement", "Before tuning", "After tuning"],
    [
        ["Requests per second", "577.2", "571.3"],
        ["Average response time", "13.8 ms", "14.0 ms"],
        ["Garbage collections", "160", "14"],
        ["Full GCs", "2", "0"],
        ["Total time paused for GC", "483.1 ms", "139.2 ms"],
    ],
    widths=[2.4, 1.7, 1.7],
)
doc.add_paragraph(
    "Throughput did not improve at all here. It actually came out 1 percent lower, which is small "
    "enough to just be noise between runs. GC work still dropped a lot, from 160 collections to "
    "14, but the application was not waiting on garbage collection in the first place at this "
    "level of load, so fixing GC gave nothing back in speed. I only saw the 68 percent gain once "
    "the load was heavy enough to actually exhaust the small heap."
)

# ------------------------------------------------------- lessons learned
doc.add_heading("6. Lessons Learned", level=1)
for text in [
    "Tuning only helps when the thing you are tuning is the actual bottleneck. My light load test "
    "proved that. GC activity fell sharply and the response times did not budge, because garbage "
    "collection was not what was holding it back at that point.",

    "Measure before changing anything. If I had jumped straight to changing flags I would have had "
    "no way of knowing whether it helped, and no idea which flag was responsible.",

    "Graphs and logs answer different questions. VisualVM was what showed me where to look, since "
    "I could see the heap pinned at its limit and the thread count sitting flat. But for numbers "
    "I could actually put in a table, the GC log was far better than trying to read values off a "
    "moving chart.",

    "Full GC count is a more useful warning sign than heap usage. A heap sitting near its limit is "
    "not automatically a problem, that can just be the collector being efficient. Repeated full "
    "GCs are, because each one freezes the whole application.",

    "A bigger heap is not automatically better. I went to 512 MB because that was the size that "
    "removed the full GCs. Setting it enormously high would have wasted memory the service does "
    "not need, and very large heaps can make individual collections take longer.",

    "The default settings on my machine would have hidden all of this. Java chose a 7.9 GB maximum "
    "heap and G1 on its own, and the endpoint never struggled. I had to deliberately restrict the "
    "heap to 128 MB to create a problem worth investigating, which is roughly the situation you "
    "would be in deploying to a small container with a memory limit.",
]:
    doc.add_paragraph(text, style="List Bullet")

# --------------------------------------------------------------- summary
doc.add_heading("7. Conclusion", level=1)
doc.add_paragraph(
    "I built a Spring Boot microservice with one REST endpoint, monitored it in VisualVM while it "
    "was under load, found that a 128 MB heap with the serial collector was leaving the "
    "application paused for most of the test, and fixed it by raising the heap to 512 MB and "
    "switching to G1 with a 100 ms pause target. That took throughput from 103 to 173.5 requests "
    "per second and removed all 76 full GCs. The part I will remember is that the exact same "
    "change made no difference under lighter load, so the measurement mattered as much as the fix."
)

# -------------------------------------------------------------- appendix
doc.add_heading("Appendix: Reproducing the Tests", level=1)
doc.add_paragraph("Baseline run:")
code_block([
    "java -Xms64m -Xmx128m -XX:+UseSerialGC \\",
    "     -Xlog:gc:file=baseline-gc.log:time,level,tags \\",
    "     -jar target/itemservice-0.0.1-SNAPSHOT.jar",
])
doc.add_paragraph("Tuned run:")
code_block([
    "java -Xms512m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=100 \\",
    "     -Xlog:gc:file=tuned-gc.log:time,level,tags \\",
    "     -jar target/itemservice-0.0.1-SNAPSHOT.jar",
])
doc.add_paragraph(
    "Load in both cases came from loadtest.py (1,200 requests, 16 concurrent, count=25000). "
    "Counting the collections and adding up the pauses afterwards:"
)
code_block([
    "grep -c 'Pause Young\\|Pause Full' baseline-gc.log",
    "grep -c 'Pause Full' baseline-gc.log",
    "grep -oP '\\d+\\.\\d+(?=ms)' baseline-gc.log | awk '{s+=$1} END {print s}'",
])

doc.save(OUT)
print("wrote", OUT)
