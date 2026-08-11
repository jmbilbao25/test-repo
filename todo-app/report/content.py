"""The text of the write-up.

Kept apart from the two writers so the .docx and the .pdf are built from one
source and cannot drift apart. Each block is a tuple whose first item says what
it is:

    ("h1",    text)                     a section heading
    ("p",     text)                     a paragraph
    ("code",  [lines])                  a fixed width block
    ("fig",   filename, caption, width) a figure, width in inches
    ("table", [[cells]], [widths])      first row is the header
    ("bullets", [items])                a bulleted list
    ("note",  text)                     a boxed aside
    ("break",)                          a page break
"""
from __future__ import annotations

import os
import re

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results")


def _measurements() -> dict:
    """Read the timings out of the captured benchmark output.

    The prose quotes these numbers and so does the figure, so they are taken
    from the same file rather than typed in twice. Re-running the benchmark then
    cannot leave the text disagreeing with the screenshot next to it.
    """
    path = os.path.join(RESULTS, "benchmark.txt")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    wanted = {
        "draft": r"^\s*draft\s+([\d.]+) s",
        "reviewed": r"^\s*reviewed\s+([\d.]+) s",
        "scan": r"^\s*list scan\s+([\d.]+) s",
        "lookup": r"^\s*set lookup\s+([\d.]+) s",
        "probes": r"(\d+) probes",
        "tasks": r"Adding (\d+) tasks",
    }
    out = {}
    for key, pattern in wanted.items():
        m = re.search(pattern, text, re.MULTILINE)
        if not m:
            raise ValueError(f"could not find {key} in {path}")
        out[key] = m.group(1)
    out["probes"] = f"{int(out['probes']):,}"
    out["tasks"] = f"{int(out['tasks']):,}"
    return out


TITLE = "Building a To-Do List App with Copilot, ChatGPT and CodeWhisperer"
DAY = "Day 3 Assignment"
AUTHOR = "John Michael Bilbao"
COURSE = "Techstart"
DATE = "August 11, 2026"


def blocks() -> list[tuple]:
    b: list[tuple] = []
    p = lambda t: b.append(("p", t))
    h = lambda t: b.append(("h1", t))
    m = _measurements()

    # ------------------------------------------------------------ introduction
    h("Introduction")
    p("The assignment asks for a small Python to-do list app built with three "
      "AI tools, and a description of what each one actually contributed. I "
      "used Copilot for the interface, ChatGPT for the function that adds a "
      "task, and CodeWhisperer to review what the other two produced.")
    p("I built it as a Flask web app rather than a console script. The "
      "interface is then ordinary HTML, which is the kind of repetitive markup "
      "Copilot is good at, and the finished app is something I can point a "
      "browser at and photograph. The whole thing is about 300 lines across "
      "five Python files, one template and one stylesheet.")
    p("The short version of what happened: Copilot was the fastest of the "
      "three but needed watching, ChatGPT wrote the best single function, and "
      "CodeWhisperer found real problems that neither of the other two "
      "noticed. It also gave me one piece of advice that made the code slower "
      "when I followed it literally, which took a benchmark to notice.")

    # --------------------------------------------------------------- step one
    h("Step 1: Setting up the environment")
    p("I worked in VS Code with the GitHub Copilot extension and the AWS "
      "Toolkit, which is what CodeWhisperer ships inside. ChatGPT I used in "
      "the browser rather than through an extension, because I wanted to be "
      "able to argue with it about the design before taking any code.")
    p("The project is a virtual environment with Flask and pytest in it, and "
      "the layout below. Splitting storage from the task operations was a "
      "decision I made before asking any of the tools for anything, and it "
      "turned out to matter later: because the file handling sits in one "
      "class, the fixes that came out of the review touched one file instead "
      "of being spread through the app.")
    b.append(("fig", "fig-structure.png",
              "The application files. The scripts that build this write-up and "
              "its figures live alongside them and are left out here.", 4.5))
    p("Flask serves the app on port 5000, and the whole interface is a single "
      "page that is re-rendered after every action.")
    b.append(("fig", "fig-run.png", "Starting the app", 6.2))

    # --------------------------------------------------------------- step two
    h("Step 2: Using Copilot for the interface")
    p("I wrote the stylesheet first, with the class names I wanted, then "
      "opened the template and started typing. That order matters. Copilot "
      "reads the files that are already open, so once it had seen .item, "
      ".title and .check in the stylesheet it began suggesting markup that "
      "used those exact classes. When I tried it the other way round on a "
      "scratch file it invented its own class names and none of them matched "
      "anything.")
    p("The figure below is the suggestion for the task list arriving as grey "
      "text after I had typed the form above it. Everything from line 26 down "
      "is Copilot's; the lines above it are already accepted.")
    b.append(("fig", "fig-copilot.png",
              "Copilot offering the task list markup in index.html", 6.3))
    p("It got the loop, the conditional class for a finished task and the "
      "escaping right first time. Two things it got wrong were worth noticing. "
      "It offered the delete action as a link, which would have meant a task "
      "could be deleted by anything that follows links, including a browser "
      "prefetching one; I replaced both the delete and the tick with small "
      "POST forms. It also kept suggesting a task counter that counted the "
      "tasks being displayed rather than all of them, so on the Active tab it "
      "would have reported that nothing was finished no matter how much was.")
    p("Neither of those is the kind of mistake that shows up when you run the "
      "app once and it looks right, which is the thing I took away from this "
      "step.")
    b.append(("fig", "fig-app-empty.png",
              "The interface rendering, before any tasks exist", 3.8))

    # ------------------------------------------------------------- step three
    h("Step 3: ChatGPT and the add-task function")
    p("For the function that adds a task I described what I wanted in prose "
      "and asked for the whole thing at once, which is the opposite of how "
      "Copilot is used. The reply is below.")
    b.append(("fig", "fig-chatgpt.png",
              "Asking ChatGPT for the add-task function", 5.6))
    p("Three things in that answer were better than what I would have written. "
      "Splitting on whitespace and rejoining collapses runs of spaces as well "
      "as trimming the ends, so a title typed carelessly still matches one "
      "already on the list. Using casefold rather than lower is the correct "
      "choice for comparing text that might not be English. And raising a "
      "custom error instead of returning None means the view cannot quietly "
      "ignore a failure, which is how the message in the interface ends up "
      "being the message the function raised.")
    p("What I had to change was the plumbing. The function it wrote calls "
      "store.titles_lowered(), a method that did not exist, so I wrote one. "
      "That method built a set of every lowercased title each time it was "
      "called, and it survived until I measured it in step 4, where it turned "
      "out to be slower than the naive version it replaced.")
    p("This is the pattern I saw all afternoon: ChatGPT writes a good function "
      "in isolation and assumes the rest of the program to fit it, so the code "
      "compiles in your head and not in the project.")

    # -------------------------------------------------------------- step four
    h("Step 4: The CodeWhisperer review")
    p("Before this point the storage code was a first draft that read the "
      "whole file, appended to a list and wrote it back. I kept that draft in "
      "the repository as drafts/draft_tasks.py so the before and after could "
      "be run rather than described. I ran the scan over the project and got "
      "six findings, all in that file.")
    b.append(("fig", "fig-codewhisperer.png",
              "The findings from the review", 6.3))
    p("What I did about each one:")
    b.append(("table", [
        ["Finding", "What I changed"],
        ["max() on an empty list",
         "Kept a next-id counter on the store instead of deriving the id from "
         "the tasks present."],
        ["Write is not atomic",
         "Write to a temporary file in the same directory, then os.replace it "
         "over the real one."],
        ["Ids get reused",
         "The counter only ever goes up, so a deleted id is not handed out "
         "again."],
        ["Duplicate check scans the list",
         "The store keeps a set of casefolded titles, updated as tasks go in "
         "and out."],
        ["Titles compared raw",
         "Normalise before comparing, which is what ChatGPT's function was "
         "already doing."],
        ["open() without an encoding",
         "Pass encoding='utf-8' everywhere a file is opened."],
    ], [2.1, 4.2]))
    p("The first two are the ones that mattered. Without the counter the app "
      "cannot add its first task at all, because max() of an empty sequence "
      "raises, and that is a bug you only meet on a fresh install. The "
      "non-atomic write is worse in a quieter way: interrupt the program "
      "mid-save and the file is truncated, and on the next start the app "
      "cannot read its own data.")
    p("I did not want to take the performance claim on trust, so I wrote "
      "benchmark.py to run the draft and the reviewed version side by side.")
    b.append(("fig", "fig-benchmark.png",
              "The draft and the reviewed version measured against each other",
              5.9))
    p("Two results there are worth more than the rest of the review. Adding "
      f"{m['tasks']} tasks takes the same time either way, {m['draft']} seconds "
      f"against {m['reviewed']}, so the reviewed version is very slightly "
      "slower. The lookup did get faster, but the whole file is still rewritten "
      "on every single add, and that cost swamps everything else. The finding "
      "was correct about the scan and wrong about what it would buy.")
    p("The second result is the one I nearly missed. When I first wrote "
      "store.titles_lowered() the way ChatGPT's function assumed, building the "
      "set on each call, the duplicate check came out about three times slower "
      "than the list scan the review had told me to remove, because it "
      "casefolded every title in the list every time. Keeping the set on the "
      "store and updating it as tasks change is what actually made it fast, "
      f"and the gap is then large: {m['scan']} seconds against {m['lookup']} "
      f"for the same {m['probes']} checks.")
    p("So the fix that was worth doing was not quite the fix that was "
      "suggested, and I would not have known the difference without measuring "
      "it.")

    # -------------------------------------------------------------- step five
    h("Step 5: Putting it together and testing it")
    p("The finished app is Copilot's markup, ChatGPT's function with the "
      "plumbing rewritten, and the storage class as the review left it. I "
      "wrote 21 tests, most of them for the cases the review had pointed at, "
      "since those were the ones I now knew the draft got wrong.")
    b.append(("fig", "fig-tests.png", "The test run", 6.0))
    p("Four of those tests exist purely because of the review: adding the "
      "first task to an empty list, ids not being reused after a delete, a "
      "corrupt file not stopping the app from starting, and a title that "
      "differs only in case and spacing being refused.")
    p("The app itself, with tasks added through the form and the first one "
      "ticked off:")
    b.append(("fig", "fig-app-filled.png", "The finished app", 4.6))
    p("The validation showing the reason it refused something, which is "
      "ChatGPT's error text arriving in the interface unchanged:")
    b.append(("fig", "fig-app-duplicate.png",
              "'  buy   MILK ' refused as a duplicate of 'Buy milk'", 3.6))
    p("And a task whose title is a script tag, to confirm the template escapes "
      "it rather than running it. It is listed as text, which is what should "
      "happen:")
    b.append(("fig", "fig-app-escaped.png",
              "Markup in a title is escaped, not executed", 3.6))

    # ------------------------------------------------------------- experience
    h("What the three tools were like to use")
    p("They are not really substitutes for each other. Each one was best at a "
      "different size of problem.")
    b.append(("table", [
        ["", "Best at", "Where it let me down"],
        ["Copilot", "Repetitive markup and code that follows a pattern "
                    "already in the file",
         "Quietly makes design decisions, like deleting over GET"],
        ["ChatGPT", "One self-contained function, and explaining why it chose "
                    "something",
         "Calls things that do not exist and assumes the surrounding code"],
        ["CodeWhisperer", "Whole classes of bug I was not looking for, in code "
                          "I had stopped reading",
         "Severity did not match impact, and one fix needed rethinking"],
    ], [1.15, 2.6, 2.55]))
    p("Copilot was the one I used most and trusted least. It is genuinely fast "
      "at the fourth similar block of HTML, and because it reads the open "
      "files it picks up the conventions of the project instead of inventing "
      "its own. But it produces something plausible for every keystroke, and "
      "plausible markup that deletes a record over GET looks exactly like "
      "correct markup until you think about it.")
    p("ChatGPT was the best of the three at a single function, and the only "
      "one that explained itself. The explanation is most of the value: I now "
      "know why casefold beats lower for this, and that is worth more than the "
      "eight lines it saved me. The cost is that its code assumes a program "
      "that does not exist yet, so every answer needs adapting.")
    p("CodeWhisperer was the only one that told me something I did not already "
      "half know. All six findings were real, and four of them were in code I "
      "had written myself and stopped looking at. Its weakness is judgement "
      "rather than accuracy. It labelled the atomic write and the empty-list "
      "crash the same severity as each other, and rated the lookup above the "
      "encoding, when in practice the lookup change bought nothing at the size "
      "this app will ever be.")
    p("If I did it again I would use Copilot only in files where the pattern "
      "is already established, ask ChatGPT for the awkward function and the "
      "reasoning, run the review before writing tests rather than after, and "
      "measure anything a tool tells me is a performance problem before "
      "changing it. The measuring is the part I would keep. Two of the three "
      "tools told me something about performance in this project and both were "
      "misleading, and a twenty-line benchmark settled it.")

    # ------------------------------------------------------- about the images
    h("A note on the screenshots")
    p("The screenshots of the running app, the project layout, the test run "
      "and the benchmark are captured from this project on the machine it was "
      "built on. scripts/capture_app.py starts the app and drives it in a real "
      "browser to take them, so they can be regenerated at any time.")
    b.append(("note",
              "The three figures showing the Copilot suggestion, the ChatGPT "
              "conversation and the CodeWhisperer findings are reproductions, "
              "laid out in HTML by scripts/render_figures.py, because the "
              "machine this was assembled on cannot sign in to those services. "
              "The content in them is this project's own: the suggested markup "
              "is the markup that is in index.html, and every finding cites a "
              "line that is really in drafts/draft_tasks.py."))

    return b
